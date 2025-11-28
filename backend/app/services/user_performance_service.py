"""Service layer for user performance tracking in adaptive quiz engine using PostgreSQL."""

import logging
from typing import Dict, Optional, Set
import asyncpg

from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class UserPerformanceService:
    """Service for managing user quiz performance in PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.repository = AnalyticsRepository(pool)
    
    async def get_user_performance(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Optional[Dict]:
        """
        Fetch user's performance record for a specific lecture.
        
        Returns:
            Performance document or None if not found
        """
        return await self.repository.get_user_performance_for_lecture(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id
        )
    
    async def record_answer(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str,
        question_hash: str,
        flashcard_id: str,
        is_correct: bool,
        question_snapshot: Optional[Dict] = None
    ) -> bool:
        """
        Record a user's answer to a quiz question.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            question_hash: Hash of the question
            flashcard_id: Source flashcard ID
            is_correct: Whether the answer was correct
            question_snapshot: Optional dict with 'question_text' and 'options' for display
            
        Returns:
            True if successful
        """
        try:
            # Record the quiz attempt
            await self.repository.record_quiz_attempt(
                user_id=user_id,
                course_id=course_id,
                lecture_id=lecture_id,
                flashcard_id=flashcard_id,
                question_hash=question_hash,
                is_correct=is_correct
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error recording answer: {e}")
            return False
    
    async def calculate_weakness_scores(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Dict[str, float]:
        """
        Calculate weakness scores for all flashcards.
        
        Formula: (incorrect + 1) / (correct + 1)
        Higher score = more weakness = needs more practice
        
        Returns:
            Dict mapping flashcard_id to weakness score
        """
        return await self.repository.calculate_weakness_scores(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id
        )
    
    async def get_attempted_questions(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Set[str]:
        """
        Get set of question hashes the user has already attempted.
        
        Returns:
            Set of question hashes
        """
        return await self.repository.get_attempted_questions(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id
        )
    
    async def get_seen_flashcard_ids(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Set[str]:
        """
        Get set of flashcard IDs the user has been tested on.
        
        This is used for the coverage-first quiz selection algorithm
        to ensure users see all concepts before reinforcement.
        
        Returns:
            Set of flashcard IDs
        """
        return await self.repository.get_seen_flashcard_ids(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id
        )


def get_user_performance_service(pool: asyncpg.Pool = None) -> UserPerformanceService:
    """Dependency injection helper."""
    if pool is None:
        raise ValueError("PostgreSQL pool is required")
    return UserPerformanceService(pool)
