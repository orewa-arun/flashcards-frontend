"""Service layer for user performance tracking in adaptive quiz engine."""

import logging
from datetime import datetime
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class UserPerformanceService:
    """Service for managing user quiz performance in MongoDB."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.user_performance
    
    async def initialize_indexes(self):
        """Create indexes for efficient querying."""
        await self.collection.create_index([
            ("user_id", 1),
            ("course_id", 1),
            ("lecture_id", 1)
        ], unique=True)
        logger.info("User performance indexes created")
    
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
        performance = await self.collection.find_one({
            "user_id": user_id,
            "course_id": course_id,
            "lecture_id": lecture_id
        })
        return performance
    
    async def record_answer(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str,
        question_hash: str,
        flashcard_id: str,
        is_correct: bool
    ) -> bool:
        """
        Record a user's answer to a quiz question.
        
        Uses atomic MongoDB operations to update performance metrics.
        """
        try:
            # Determine which counter to increment
            result_field = "correct" if is_correct else "incorrect"
            
            # Atomic update using $inc for both question and flashcard
            update_result = await self.collection.update_one(
                {
                    "user_id": user_id,
                    "course_id": course_id,
                    "lecture_id": lecture_id
                },
                {
                    "$inc": {
                        f"questions.{question_hash}.{result_field}": 1,
                        f"flashcards.{flashcard_id}.{result_field}": 1
                    },
                    "$set": {
                        f"flashcards.{flashcard_id}.last_attempted": datetime.utcnow()
                    }
                },
                upsert=True  # Create document if it doesn't exist
            )
            
            return update_result.acknowledged
        
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
        performance = await self.get_user_performance(user_id, course_id, lecture_id)
        
        if not performance or not performance.get('flashcards'):
            return {}
        
        weakness_scores = {}
        flashcards = performance.get('flashcards', {})
        
        for flashcard_id, stats in flashcards.items():
            correct = stats.get('correct', 0)
            incorrect = stats.get('incorrect', 0)
            
            # Calculate weakness score
            weakness_scores[flashcard_id] = (incorrect + 1) / (correct + 1)
        
        return weakness_scores
    
    async def get_attempted_questions(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> set:
        """
        Get set of question hashes the user has already attempted.
        
        Returns:
            Set of question hashes
        """
        performance = await self.get_user_performance(user_id, course_id, lecture_id)
        
        if not performance or not performance.get('questions'):
            return set()
        
        return set(performance.get('questions', {}).keys())
    
    async def get_seen_flashcard_ids(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> set:
        """
        Get set of flashcard IDs the user has been tested on.
        
        This is used for the coverage-first quiz selection algorithm
        to ensure users see all concepts before reinforcement.
        
        Returns:
            Set of flashcard IDs
        """
        performance = await self.get_user_performance(user_id, course_id, lecture_id)
        
        if not performance or not performance.get('flashcards'):
            return set()
        
        return set(performance.get('flashcards', {}).keys())


