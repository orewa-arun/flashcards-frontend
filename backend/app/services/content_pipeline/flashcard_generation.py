"""Flashcard generation service using self-contained modules."""

import logging
import traceback
from typing import Dict, Any
from datetime import datetime

from app.config import settings
from app.repositories.content_repository import ContentRepository
from app.content_generation.llm.client import create_llm_client
from app.content_generation.generators.flashcard_generator import FlashcardGenerator

logger = logging.getLogger(__name__)


class FlashcardGenerationService:
    """Service for generating flashcards from structured analysis."""
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        self.model_name = settings.MODEL_FLASHCARDS
    
    def _extract_content_from_analysis(self, structured_analysis: Dict[str, Any]) -> str:
        """Extract text content from structured analysis."""
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
            llm_client = create_llm_client(
                provider=provider,
                model=self.model_name,
                api_key=api_key,
                temperature=0.7,
                max_tokens=8000
            )
            
            # Initialize flashcard generator
            generator = FlashcardGenerator(
                llm_client=llm_client,
                course_name=course["course_name"],
                reference_textbooks=course.get("reference_textbooks", [])
            )
            
            # Extract content from structured analysis
            content = self._extract_content_from_analysis(lecture["structured_analysis"])
            
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
                "flashcards": flashcards_list
            }
            
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
