"""Cognitive flashcard generation module with enriched context support."""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.content_generation.llm.client import LLMClient
from app.content_generation.prompts import get_flashcard_prompt, get_enriched_flashcard_prompt
from app.content_generation.analyzers.content_consolidator import (
    ContentConsolidator, 
    consolidate_for_flashcards
)
from app.content_generation.builders.topic_brief_builder import (
    TopicBriefBuilder,
    TopicBrief,
    build_enriched_prompt_context
)

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """
    Generate cognitive flashcards from structured content.
    
    Supports two modes:
    1. Legacy mode: Uses raw content with v2 prompt
    2. Enriched mode: Uses TopicBriefBuilder with v3 prompt for richer, 
       answer-type-specific context
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        course_name: str,
        reference_textbooks: List[str],
        use_consolidation: bool = True,
        use_enriched_prompt: bool = True,
        min_educational_value: float = 0.3
    ):
        """
        Initialize flashcard generator.
        
        Args:
            llm_client: LLM client for generation
            course_name: Name of the course
            reference_textbooks: List of reference textbooks
            use_consolidation: Whether to use topic-based consolidation (recommended)
            use_enriched_prompt: Whether to use the v3 enriched prompt (recommended)
            min_educational_value: Minimum educational value threshold (0.0-1.0)
        """
        self.llm_client = llm_client
        self.course_name = course_name
        self.textbook_reference = ", ".join(reference_textbooks) if reference_textbooks else "Course Materials"
        self.use_consolidation = use_consolidation
        self.use_enriched_prompt = use_enriched_prompt
        self.min_educational_value = min_educational_value
        self.consolidator = ContentConsolidator(min_educational_value=min_educational_value)
        self.brief_builder = TopicBriefBuilder()
    
    def generate(
        self,
        content: str,
        source_name: str = "",
        max_flashcards: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards from content.
        
        Args:
            content: Text content to generate flashcards from
            source_name: Name of the source (e.g., lecture name)
            max_flashcards: Maximum flashcards to generate per chunk
            
        Returns:
            List of flashcard dicts
        """
        logger.info(f"Generating flashcards from: {source_name}")
        
        # Build prompt
        prompt = self._build_prompt(content, max_flashcards)
        
        # Generate flashcards
        try:
            response = self.llm_client.generate(prompt)
            flashcards = self._parse_flashcards(response)
            
            logger.info(f"Generated {len(flashcards)} flashcards")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            raise
    
    def generate_from_chunks(
        self,
        content: str,
        chunk_size: int = 12000,
        max_flashcards_per_chunk: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards from large content by chunking.
        
        Args:
            content: Full content text
            chunk_size: Maximum characters per chunk
            max_flashcards_per_chunk: Max flashcards per chunk
            
        Returns:
            List of all generated flashcards
        """
        chunks = self._chunk_content(content, chunk_size)
        logger.info(f"Processing {len(chunks)} content chunks")
        
        all_flashcards = []
        
        for idx, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {idx}/{len(chunks)}")
            
            try:
                flashcards = self.generate(
                    content=chunk,
                    source_name=f"Chunk {idx}/{len(chunks)}",
                    max_flashcards=max_flashcards_per_chunk
                )
                all_flashcards.extend(flashcards)
                
            except Exception as e:
                logger.error(f"Error processing chunk {idx}: {str(e)}")
                continue
        
        logger.info(f"Total flashcards generated: {len(all_flashcards)}")
        return all_flashcards
    
    def generate_from_slide_analyses(
        self,
        raw_slide_analyses: List[Dict[str, Any]],
        lecture_title: str = "",
        structured_content: Optional[Dict[str, Any]] = None,
        max_flashcards_per_chunk: int = 6,
        consolidated_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate flashcards from raw slide analyses with consolidation.
        
        This method consolidates fragmented slides into topic-based chunks,
        removing redundancy and non-educational content before generation.
        Uses enriched context with answer-type specific sections.
        
        Args:
            raw_slide_analyses: List of slide analysis dictionaries
            lecture_title: Title of the lecture
            structured_content: Optional structured_content (summary, sections, etc.)
            max_flashcards_per_chunk: Max flashcards per topic chunk
            consolidated_analysis: Optional pre-computed consolidated analysis from database
            
        Returns:
            Dictionary with flashcards and consolidation metadata
        """
        logger.info(f"Generating flashcards from {len(raw_slide_analyses)} slides")
        logger.info(f"Using enriched prompt: {self.use_enriched_prompt}")
        
        # Use pre-computed consolidation if available, otherwise compute it
        if consolidated_analysis:
            logger.info("Using pre-computed consolidated_structured_analysis from database")
            # Extract the full_result which contains the consolidation output
            consolidation_result = consolidated_analysis.get("full_result", consolidated_analysis)
        else:
            # Step 1: Consolidate slides into semantic chunks
            logger.info("Computing consolidation on-the-fly (no pre-computed version available)")
            consolidation_result = self.consolidator.consolidate(
                raw_slide_analyses, 
                lecture_title
            )
        
        semantic_chunks = consolidation_result.get("semantic_chunks", [])
        all_topics = consolidation_result.get("topics", [])
        
        if not semantic_chunks:
            logger.warning("No educational content found after consolidation")
            return {
                "flashcards": [],
                "consolidation_summary": "No educational content found",
                "topics_processed": 0,
                "slides_filtered": consolidation_result.get("filtered_slides_count", 0)
            }
        
        logger.info(f"Consolidated into {len(semantic_chunks)} semantic chunks from {len(all_topics)} topics")
        
        # Step 2: Generate flashcards from each chunk
        all_flashcards = []
        
        for idx, chunk in enumerate(semantic_chunks, 1):
            topic_names = chunk.get("topics", [])
            
            logger.info(f"Processing chunk {idx}/{len(semantic_chunks)} - Topics: {', '.join(topic_names[:3])}")
            
            try:
                if self.use_enriched_prompt:
                    # Build enriched context using TopicBriefBuilder
                    brief = self.brief_builder.build_from_semantic_chunk(
                        chunk=chunk,
                        all_topics=all_topics,
                        structured_content=structured_content,
                        lecture_title=lecture_title
                    )
                    
                    # Generate with enriched context
                    flashcards = self.generate_enriched(
                        topic_brief=brief,
                        source_name=f"Topics: {', '.join(topic_names[:2])}",
                        max_flashcards=max_flashcards_per_chunk
                    )
                else:
                    # Legacy mode: use raw chunk content
                    chunk_content = chunk.get("content", "")
                    if not chunk_content.strip():
                        continue
                    
                    flashcards = self.generate(
                        content=chunk_content,
                        source_name=f"Topics: {', '.join(topic_names[:2])}",
                        max_flashcards=max_flashcards_per_chunk
                    )
                
                all_flashcards.extend(flashcards)
                
            except Exception as e:
                logger.error(f"Error processing chunk {idx}: {str(e)}")
                continue
        
        logger.info(f"Total flashcards generated: {len(all_flashcards)}")
        
        return {
            "flashcards": all_flashcards,
            "total_flashcards": len(all_flashcards),
            "consolidation_summary": consolidation_result.get("consolidation_summary", ""),
            "topics_processed": len(all_topics),
            "slides_filtered": consolidation_result.get("filtered_slides_count", 0),
            "original_slides": consolidation_result.get("total_original_slides", 0),
            "educational_slides": consolidation_result.get("educational_slides_count", 0),
            "used_enriched_prompt": self.use_enriched_prompt
        }
    
    def generate_enriched(
        self,
        topic_brief: TopicBrief,
        source_name: str = "",
        max_flashcards: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards using enriched context from TopicBrief.
        
        This method uses the v3 prompt which provides answer-type specific
        sections (DEFINITIONS, EXAMPLES, VISUAL FRAMEWORKS, etc.) for
        richer, more accurate flashcard generation.
        
        Args:
            topic_brief: Structured TopicBrief with answer-type sections
            source_name: Name of the source for logging
            max_flashcards: Maximum flashcards to generate
            
        Returns:
            List of flashcard dicts
        """
        logger.info(f"Generating enriched flashcards from: {source_name}")
        logger.info(f"  Topic: {topic_brief.topic_name}")
        logger.info(f"  Educational value: {topic_brief.educational_value:.2f}")
        logger.info(f"  Definitions: {len(topic_brief.definitions)}, Examples: {len(topic_brief.examples)}")
        
        # Convert TopicBrief to structured prompt context
        enriched_content = topic_brief.to_prompt_context()
        
        # Build prompt with v3 template
        prompt = self._build_enriched_prompt(enriched_content, max_flashcards)
        
        # Generate flashcards
        try:
            response = self.llm_client.generate(prompt)
            flashcards = self._parse_flashcards(response)
            
            # Add metadata about enriched generation
            for card in flashcards:
                card["_generation_metadata"] = {
                    "topic": topic_brief.topic_name,
                    "enriched_prompt": True,
                    "definitions_available": len(topic_brief.definitions),
                    "examples_available": len(topic_brief.examples),
                    "diagrams_available": len(topic_brief.diagrams)
                }
            
            logger.info(f"Generated {len(flashcards)} enriched flashcards")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating enriched flashcards: {str(e)}")
            raise
    
    def _build_enriched_prompt(self, enriched_content: str, max_flashcards: int) -> str:
        """Build enriched flashcard generation prompt with v3 template."""
        template = get_enriched_flashcard_prompt()
        
        # Replace placeholders
        prompt = template.replace("{{COURSE_NAME}}", self.course_name)
        prompt = template.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
        prompt = prompt.replace("{{CONTENT_PLACEHOLDER}}", enriched_content)
        
        return prompt
    
    def _build_prompt(self, content: str, max_flashcards: int) -> str:
        """Build flashcard generation prompt."""
        template = get_flashcard_prompt()
        
        # Replace placeholders
        prompt = template.replace("{{COURSE_NAME}}", self.course_name)
        prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
        prompt = prompt.replace("{{CONTENT_PLACEHOLDER}}", content)
        
        # Add max flashcards instruction
        prompt += f"\n\nIMPORTANT: Generate EXACTLY {max_flashcards} flashcards or fewer. DO NOT EXCEED {max_flashcards} cards."
        
        return prompt
    
    def _parse_flashcards(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to flashcard list with truncation recovery."""
        try:
            # Remove code fences
            if response.startswith("```"):
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1]
                    if response.startswith("json"):
                        response = response[4:].strip()
            
            # Try direct parse first
            try:
                flashcards = json.loads(response)
                if not isinstance(flashcards, list):
                    flashcards = [flashcards]
                return flashcards
            except json.JSONDecodeError:
                pass
            
            # Attempt to recover from truncated JSON
            logger.warning("Attempting to recover truncated JSON...")
            recovered = self._recover_truncated_json(response)
            if recovered:
                logger.info(f"Recovered {len(recovered)} flashcards from truncated response")
                return recovered
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to parse flashcards JSON: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            return []
    
    def _recover_truncated_json(self, response: str) -> List[Dict[str, Any]]:
        """
        Attempt to recover complete flashcards from truncated JSON.
        
        The response is an array of flashcard objects. If truncated mid-object,
        we try to extract all complete objects before the truncation point.
        """
        import re
        
        flashcards = []
        
        # Clean up the response
        response = response.strip()
        if not response.startswith('['):
            # Find the array start
            start_idx = response.find('[')
            if start_idx == -1:
                return []
            response = response[start_idx:]
        
        # Try to find complete flashcard objects
        # A complete flashcard ends with }, followed by either , or ]
        depth = 0
        current_obj_start = None
        
        for i, char in enumerate(response):
            if char == '{':
                if depth == 1:  # Inside array, starting an object
                    current_obj_start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 1 and current_obj_start is not None:  # Completed an object inside array
                    # Try to parse this object
                    obj_str = response[current_obj_start:i+1]
                    try:
                        obj = json.loads(obj_str)
                        flashcards.append(obj)
                    except json.JSONDecodeError:
                        pass
                    current_obj_start = None
            elif char == '[' and depth == 0:
                depth = 1
        
        return flashcards
    
    def _chunk_content(self, content: str, chunk_size: int) -> List[str]:
        """
        Split content into chunks for processing.
        
        Args:
            content: Full content text
            chunk_size: Maximum characters per chunk
            
        Returns:
            List of content chunks
        """
        if len(content) <= chunk_size:
            return [content]
        
        # Split by paragraphs
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks

