"""Quiz generation service using self-contained modules."""

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
    """Service for generating quizzes from flashcards."""
    
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
        Generate quizzes for a lecture.
        
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
            provider = "gemini"  # Default for Gemini
            if "gpt" in self.model_name.lower():
                provider = "openai"
            elif "claude" in self.model_name.lower():
                provider = "anthropic"
            
            # Get appropriate API key
            api_key = settings.GEMINI_API_KEY
            if provider == "openai":
                api_key = settings.OPENAI_API_KEY
            elif provider == "anthropic":
                api_key = settings.ANTHROPIC_API_KEY
            
            # Initialize LLM client
            llm_client = create_llm_client(
                provider=provider,
                model=self.model_name,
                api_key=api_key,
                temperature=0.7,
                max_tokens=8000
            )
            
            # Initialize quiz generator
            generator = QuizGenerator(
                llm_client=llm_client,
                course_name=course["course_name"],
                reference_textbooks=course.get("reference_textbooks", [])
            )
            
            # Extract flashcards list
            flashcards_data = lecture["flashcards"]
            flashcards_list = flashcards_data.get("flashcards", [])
            
            if not flashcards_list:
                raise ValueError("No flashcards found in lecture data")
            
            # Generate quizzes for all 4 levels
            quizzes = generator.generate_all_levels(
                flashcards=flashcards_list,
                questions_per_flashcard=5
            )
            
            # Update lecture with results
            await self.repository.update_lecture_content(
                lecture_id=lecture_id,
                content_field="quizzes",
                content_data=quizzes
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
            
            # Count total questions
            total_questions = sum(q.get("total_questions", 0) for q in quizzes)
            
            logger.info(f"Successfully completed quiz generation for lecture {lecture_id}")
            return {
                "success": True,
                "message": "Quiz generation completed",
                "lecture_id": lecture_id,
                "total_questions": total_questions,
                "levels": len(quizzes)
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
