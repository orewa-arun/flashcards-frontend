"""Cognitive flashcard generation module."""

import logging
import json
from typing import Dict, Any, List
from pathlib import Path

from app.content_generation.llm.client import LLMClient
from app.content_generation.prompts import get_flashcard_prompt

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Generate cognitive flashcards from structured content."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        course_name: str,
        reference_textbooks: List[str]
    ):
        """
        Initialize flashcard generator.
        
        Args:
            llm_client: LLM client for generation
            course_name: Name of the course
            reference_textbooks: List of reference textbooks
        """
        self.llm_client = llm_client
        self.course_name = course_name
        self.textbook_reference = ", ".join(reference_textbooks) if reference_textbooks else "Course Materials"
    
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
        """Parse LLM response to flashcard list."""
        try:
            # Remove code fences
            if response.startswith("```"):
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1]
                    if response.startswith("json"):
                        response = response[4:].strip()
            
            # Parse JSON
            flashcards = json.loads(response)
            
            # Validate it's a list
            if not isinstance(flashcards, list):
                logger.warning("Response is not a list, wrapping it")
                flashcards = [flashcards]
            
            return flashcards
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse flashcards JSON: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            return []
    
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

