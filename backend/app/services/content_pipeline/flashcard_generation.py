"""Flashcard generation service using self-contained modules with enriched context."""

import json
import logging
import traceback
from typing import Dict, Any
from datetime import datetime

from app.config import settings
from app.repositories.content_repository import ContentRepository
from app.content_generation.llm.client import create_llm_client
from app.content_generation.generators.flashcard_generator import FlashcardGenerator
from app.content_generation.utils.flashcard_id import tag_flashcards_with_ids

logger = logging.getLogger(__name__)


class FlashcardGenerationService:
    """
    Service for generating flashcards from structured analysis.
    
    Supports two modes:
    1. Enriched mode (default): Uses TopicBriefBuilder + v3 prompt for rich,
       answer-type specific context (DEFINITIONS, EXAMPLES, etc.)
    2. Legacy mode: Uses raw content with v2 prompt
    """
    
    def __init__(
        self, 
        repository: ContentRepository,
        use_consolidation: bool = True,
        use_enriched_prompt: bool = True,
        min_educational_value: float = 0.2
    ):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
            use_consolidation: Whether to use topic-based consolidation (recommended)
            use_enriched_prompt: Whether to use v3 enriched prompt (recommended)
            min_educational_value: Minimum educational value threshold for filtering slides
        """
        self.repository = repository
        self.model_name = settings.MODEL_FLASHCARDS
        self.use_consolidation = use_consolidation
        self.use_enriched_prompt = use_enriched_prompt
        self.min_educational_value = min_educational_value
    
    def _extract_content_from_analysis(self, structured_analysis: Dict[str, Any]) -> str:
        """Extract text content from structured analysis."""
        # Handle JSON string from database
        if isinstance(structured_analysis, str):
            try:
                structured_analysis = json.loads(structured_analysis)
            except json.JSONDecodeError:
                structured_analysis = {}
        
        content_parts = []
        
        # Add lecture title
        if "lecture_title" in structured_analysis:
            content_parts.append(f"# {structured_analysis['lecture_title']}\n")
        
        # Extract from structured_content
        structured_content = structured_analysis.get("structured_content", {})
        
        # Add summary
        if "summary" in structured_content:
            content_parts.append(f"\n## Summary\n{structured_content['summary']}\n")
        
        # Add sections
        if "sections" in structured_content:
            for section in structured_content["sections"]:
                if isinstance(section, dict):
                    title = section.get("title", "")
                    content = section.get("content", "")
                    content_parts.append(f"\n## {title}\n{content}\n")
        
        # Add key concepts
        if "key_concepts" in structured_content:
            concepts = structured_content["key_concepts"]
            if concepts:
                content_parts.append("\n## Key Concepts\n")
                for concept in concepts:
                    if isinstance(concept, str):
                        content_parts.append(f"- {concept}\n")
                    elif isinstance(concept, dict):
                        name = concept.get("name", "")
                        description = concept.get("description", "")
                        content_parts.append(f"- **{name}**: {description}\n")
        
        # Fallback: use raw slide analyses
        if not content_parts or len("".join(content_parts)) < 100:
            raw_analyses = structured_analysis.get("raw_slide_analyses", [])
            for slide_data in raw_analyses:
                analysis = slide_data.get("analysis", {})
                if "main_text" in analysis:
                    content_parts.append(analysis["main_text"] + "\n")
        
        return "\n".join(content_parts)
    
    async def generate_flashcards(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Generate flashcards for a lecture.
        
        Args:
            lecture_id: ID of the lecture to process
            
        Returns:
            Dict: Result with success status and data
        """
        try:
            # Fetch lecture from database
            lecture = await self.repository.get_lecture_by_id(lecture_id)
            
            if not lecture:
                raise ValueError(f"Lecture with ID {lecture_id} not found")
            
            # Check prerequisites
            if lecture["analysis_status"] != "completed":
                raise ValueError(
                    f"Cannot generate flashcards: analysis_status is '{lecture['analysis_status']}', must be 'completed'"
                )
            
            if lecture["flashcard_status"] == "completed":
                logger.info(f"Lecture {lecture_id} already has completed flashcards")
                return {
                    "success": True,
                    "message": "Flashcards already completed",
                    "lecture_id": lecture_id
                }
            
            # Update status to in_progress
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="flashcard_status",
                status_value="in_progress"
            )
            
            # Get course context
            course = await self.repository.get_course_by_code(lecture["course_code"])
            
            if not course:
                raise ValueError(f"Course with code '{lecture['course_code']}' not found")
            
            # Determine provider from model name
            provider = "anthropic"  # Default for Claude
            if "gpt" in self.model_name.lower():
                provider = "openai"
            elif "gemini" in self.model_name.lower():
                provider = "gemini"
            
            # Get appropriate API key
            api_key = settings.ANTHROPIC_API_KEY
            if provider == "openai":
                api_key = settings.OPENAI_API_KEY
            elif provider == "gemini":
                api_key = settings.GEMINI_API_KEY
            
            # Initialize LLM client
            # Note: max_tokens increased to 16000 to handle enriched flashcard output
            # (6 answer types + mermaid diagrams + math visualizations can be large)
            llm_client = create_llm_client(
                provider=provider,
                model=self.model_name,
                api_key=api_key,
                temperature=0.7,
                max_tokens=16000
            )
            
            # Initialize flashcard generator
            generator = FlashcardGenerator(
                llm_client=llm_client,
                course_name=course["course_name"],
                reference_textbooks=course.get("reference_textbooks", []),
                use_consolidation=self.use_consolidation,
                use_enriched_prompt=self.use_enriched_prompt,
                min_educational_value=self.min_educational_value
            )
            
            # Check for pre-computed consolidated_structured_analysis first
            consolidated_analysis = lecture.get("consolidated_structured_analysis")
            if isinstance(consolidated_analysis, str):
                try:
                    consolidated_analysis = json.loads(consolidated_analysis)
                except json.JSONDecodeError:
                    consolidated_analysis = None
            
            # Handle structured_analysis - may be JSON string from database
            structured_analysis = lecture.get("structured_analysis", {})
            if isinstance(structured_analysis, str):
                try:
                    structured_analysis = json.loads(structured_analysis)
                except json.JSONDecodeError:
                    structured_analysis = {}
            
            raw_slide_analyses = structured_analysis.get("raw_slide_analyses", [])
            structured_content = structured_analysis.get("structured_content", {})
            
            # Log what we found
            if consolidated_analysis:
                logger.info(
                    f"Lecture {lecture_id}: Using pre-computed consolidated_structured_analysis. "
                    f"Topics: {consolidated_analysis.get('consolidation_stats', {}).get('topics_created', 0)}, "
                    f"Semantic chunks: {consolidated_analysis.get('consolidation_stats', {}).get('semantic_chunks', 0)}"
                )
            elif not raw_slide_analyses:
                logger.warning(
                    f"Lecture {lecture_id} missing 'raw_slide_analyses' in structured_analysis. "
                    f"Re-run Analysis to enable consolidation-based flashcard generation. "
                    f"Falling back to legacy mode."
                )
            else:
                logger.info(
                    f"Lecture {lecture_id}: Found {len(raw_slide_analyses)} slides in raw_slide_analyses. "
                    f"First slide structure: {list(raw_slide_analyses[0].keys()) if raw_slide_analyses else 'empty'}"
                )
            
            # Use consolidated approach if enabled and consolidated analysis or raw slides available
            if self.use_consolidation and (consolidated_analysis or raw_slide_analyses):
                logger.info(f"Using topic-based consolidation for flashcard generation")
                logger.info(f"Enriched prompt: {self.use_enriched_prompt}")
                
                # Generate flashcards using consolidated approach with enriched context
                # Note: Reduced to 3 flashcards per chunk to fit within token limits
                # (6 answer types + optional diagrams per flashcard = large output)
                # With max_tokens=16000, 3 flashcards should fit comfortably
                generation_result = generator.generate_from_slide_analyses(
                    raw_slide_analyses=raw_slide_analyses,
                    lecture_title=lecture["lecture_title"],
                    structured_content=structured_content,  # Pass structured_content for enrichment
                    max_flashcards_per_chunk=3,
                    consolidated_analysis=consolidated_analysis  # Pass pre-computed consolidation if available
                )
                
                flashcards_list = generation_result.get("flashcards", [])
                consolidation_summary = generation_result.get("consolidation_summary", "")
                
                logger.info(f"Consolidation: {consolidation_summary}")
                logger.info(
                    f"Stats: {generation_result.get('original_slides', 0)} slides → "
                    f"{generation_result.get('educational_slides', 0)} educational → "
                    f"{generation_result.get('topics_processed', 0)} topics → "
                    f"{len(flashcards_list)} flashcards"
                )
                
                # Prepare result with consolidation metadata
                flashcards_data = {
                    "course_name": course["course_name"],
                    "lecture_title": lecture["lecture_title"],
                    "model_used": self.model_name,
                    "provider": provider,
                    "total_flashcards": len(flashcards_list),
                    "flashcards": flashcards_list,
                    "consolidation_summary": consolidation_summary,
                    "original_slides_count": generation_result.get("original_slides", 0),
                    "educational_slides_count": generation_result.get("educational_slides", 0),
                    "topics_processed": generation_result.get("topics_processed", 0),
                    "slides_filtered": generation_result.get("slides_filtered", 0),
                    "used_enriched_prompt": generation_result.get("used_enriched_prompt", False)
                }
                
                # Tag flashcards with stable IDs before storing
                flashcards_data = tag_flashcards_with_ids(
                    flashcards_data=flashcards_data,
                    course_code=lecture["course_code"],
                    lecture_id=lecture_id
                )
                logger.info(f"Tagged {len(flashcards_list)} flashcards with IDs for lecture {lecture_id}")
            else:
                # Fallback to legacy approach
                logger.info("Using legacy content extraction for flashcard generation")
            
            # Extract content from structured analysis
                content = self._extract_content_from_analysis(structured_analysis)
            
            # Generate flashcards (with chunking if needed)
            flashcards_list = generator.generate_from_chunks(
                content=content,
                chunk_size=12000,
                max_flashcards_per_chunk=6
            )
            
            # Prepare result
            flashcards_data = {
                "course_name": course["course_name"],
                "lecture_title": lecture["lecture_title"],
                "model_used": self.model_name,
                "provider": provider,
                "total_flashcards": len(flashcards_list),
                "flashcards": flashcards_list,
                "used_enriched_prompt": False
            }
            
            # Tag flashcards with stable IDs before storing
            flashcards_data = tag_flashcards_with_ids(
                flashcards_data=flashcards_data,
                course_code=lecture["course_code"],
                lecture_id=lecture_id
            )
            logger.info(f"Tagged {len(flashcards_list)} flashcards with IDs for lecture {lecture_id}")
            
            # Update lecture with results
            await self.repository.update_lecture_content(
                lecture_id=lecture_id,
                content_field="flashcards",
                content_data=flashcards_data
            )
            
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="flashcard_status",
                status_value="completed"
            )
            
            # Clear any previous errors
            await self.repository.clear_lecture_error(
                lecture_id=lecture_id,
                error_key="flashcard_error"
            )
            
            logger.info(f"Successfully completed flashcard generation for lecture {lecture_id}")
            return {
                "success": True,
                "message": "Flashcard generation completed",
                "lecture_id": lecture_id,
                "flashcard_count": len(flashcards_list)
            }
            
        except Exception as e:
            logger.error(f"Error generating flashcards for lecture {lecture_id}: {str(e)}")
            
            # Update lecture with error
            try:
                await self.repository.update_lecture_status(
                    lecture_id=lecture_id,
                    status_field="flashcard_status",
                    status_value="failed"
                )
                
                error_data = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.repository.update_lecture_error(
                    lecture_id=lecture_id,
                    error_key="flashcard_error",
                    error_data=error_data
                )
            except Exception as commit_error:
                logger.error(f"Failed to update error status: {str(commit_error)}")
            
            return {
                "success": False,
                "message": f"Failed to generate flashcards: {str(e)}",
                "lecture_id": lecture_id
            }
