"""
Quiz generation service with parallel execution and batching.

This service generates multi-level quizzes from flashcards using:
- Parallel execution across all 4 difficulty levels
- Smart batching to optimize API calls
- Configurable questions per flashcard per level
- Robust error handling with retries
"""

import json
import logging
import traceback
from typing import Dict, Any
from datetime import datetime

from app.config import settings
from app.repositories.content_repository import ContentRepository
from app.content_generation.llm.client import create_llm_client
from app.content_generation.generators.quiz_generator import QuizGenerator

logger = logging.getLogger(__name__)


class QuizGenerationService:
    """Service for generating quizzes from flashcards with parallel execution."""
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        self.model_name = settings.MODEL_QUIZ
    
    async def generate_quizzes(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Generate quizzes for a lecture using parallel execution.
        
        This method:
        1. Fetches the lecture and its flashcards
        2. Initializes the quiz generator with config settings
        3. Generates all 4 levels in parallel
        4. Saves results to the database
        
        Args:
            lecture_id: ID of the lecture to process
            
        Returns:
            Dict: Result with success status and statistics
        """
        try:
            # Fetch lecture from database
            lecture = await self.repository.get_lecture_by_id(lecture_id)
            
            if not lecture:
                raise ValueError(f"Lecture with ID {lecture_id} not found")
            
            # Check prerequisites
            if lecture["flashcard_status"] != "completed":
                raise ValueError(
                    f"Cannot generate quizzes: flashcard_status is '{lecture['flashcard_status']}', must be 'completed'"
                )
            
            if lecture["quiz_status"] == "completed":
                logger.info(f"Lecture {lecture_id} already has completed quizzes")
                return {
                    "success": True,
                    "message": "Quizzes already completed",
                    "lecture_id": lecture_id
                }
            
            # Update status to in_progress
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="quiz_status",
                status_value="in_progress"
            )
            
            # Get course context
            course = await self.repository.get_course_by_code(lecture["course_code"])
            
            # Determine provider from model name
            provider = self._get_provider_from_model(self.model_name)
            api_key = self._get_api_key(provider)
            
            # Initialize LLM client with appropriate settings for quiz generation
            llm_client = create_llm_client(
                provider=provider,
                model=self.model_name,
                api_key=api_key,
                temperature=0.7,
                max_tokens=16000  # Generous limit for quiz generation
            )
            
            # Initialize quiz generator with config settings
            generator = QuizGenerator(
                llm_client=llm_client,
                course_name=course["course_name"],
                reference_textbooks=course.get("reference_textbooks", []),
                questions_per_flashcard=settings.QUESTIONS_PER_FLASHCARD,
                base_chunk_size=settings.QUIZ_CHUNK_SIZE,
                chunk_size_by_level=settings.QUIZ_CHUNK_SIZE_BY_LEVEL,
            )
            
            # Extract flashcards list
            # Handle case where flashcards is stored as JSON string
            flashcards_data = lecture["flashcards"]
            if isinstance(flashcards_data, str):
                flashcards_data = json.loads(flashcards_data)
            flashcards_list = flashcards_data.get("flashcards", [])
            
            if not flashcards_list:
                raise ValueError("No flashcards found in lecture data")
            
            logger.info(
                f"Starting parallel quiz generation for lecture {lecture_id}: "
                f"{len(flashcards_list)} flashcards, "
                f"questions_per_flashcard={settings.QUESTIONS_PER_FLASHCARD}, "
                f"base_chunk_size={settings.QUIZ_CHUNK_SIZE}, "
                f"chunk_size_by_level={settings.QUIZ_CHUNK_SIZE_BY_LEVEL}"
            )
            
            # Generate quizzes for all 4 levels in parallel
            start_time = datetime.now()
            quizzes = await generator.generate_all_levels_async(flashcards=flashcards_list)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Count totals and check for errors
            total_questions = sum(q.get("total_questions", 0) for q in quizzes)
            levels_with_errors = [q for q in quizzes if q.get("errors")]
            
            if total_questions == 0:
                raise ValueError("No quiz questions were generated across any level")
            
            # Prepare quiz data for storage
            quiz_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "generation_time_seconds": elapsed,
                "total_questions": total_questions,
                "questions_per_flashcard_config": settings.QUESTIONS_PER_FLASHCARD,
                "levels": quizzes
            }
            
            # Update lecture with results
            await self.repository.update_lecture_content(
                lecture_id=lecture_id,
                content_field="quizzes",
                content_data=quiz_data
            )
            
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="quiz_status",
                status_value="completed"
            )
            
            # Clear any previous errors
            await self.repository.clear_lecture_error(
                lecture_id=lecture_id,
                error_key="quiz_error"
            )
            
            # Log summary
            level_summary = ", ".join([
                f"L{q['level']}:{q['total_questions']}"
                for q in quizzes
            ])
            
            logger.info(
                f"Quiz generation complete for lecture {lecture_id}: "
                f"{total_questions} questions in {elapsed:.1f}s "
                f"({level_summary})"
            )
            
            return {
                "success": True,
                "message": "Quiz generation completed",
                "lecture_id": lecture_id,
                "total_questions": total_questions,
                "levels": len(quizzes),
                "generation_time_seconds": elapsed,
                "questions_by_level": {q["level"]: q["total_questions"] for q in quizzes},
                "warnings": [f"Level {q['level']} had errors" for q in levels_with_errors] if levels_with_errors else None
            }
            
        except Exception as e:
            logger.error(f"Error generating quizzes for lecture {lecture_id}: {str(e)}")
            
            # Update lecture with error
            try:
                await self.repository.update_lecture_status(
                    lecture_id=lecture_id,
                    status_field="quiz_status",
                    status_value="failed"
                )
                
                error_data = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.repository.update_lecture_error(
                    lecture_id=lecture_id,
                    error_key="quiz_error",
                    error_data=error_data
                )
            except Exception as commit_error:
                logger.error(f"Failed to update error status: {str(commit_error)}")
            
            return {
                "success": False,
                "message": f"Failed to generate quizzes: {str(e)}",
                "lecture_id": lecture_id
            }
    
    def _get_provider_from_model(self, model_name: str) -> str:
        """Determine LLM provider from model name."""
        model_lower = model_name.lower()
        if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        else:
            return "gemini"  # Default to Gemini
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key for the provider."""
        if provider == "openai":
            return settings.OPENAI_API_KEY
        elif provider == "anthropic":
            return settings.ANTHROPIC_API_KEY
        else:
            return settings.GEMINI_API_KEY
