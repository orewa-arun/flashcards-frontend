"""
Analytics repository - PostgreSQL queries for user analytics and progress tracking.
Provides a clean abstraction layer over the database for:
- Deck progress (spaced repetition / flashcard review)
- Quiz attempts (granular question history)
- Flashcard performance (aggregated stats for adaptive quizzes)
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository for user analytics database operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Deck Progress Operations ====================
    
    async def get_deck_progress(
        self,
        user_id: str,
        deck_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get progress for a specific deck.
        
        Args:
            user_id: Firebase UID
            deck_id: Deck identifier (e.g., "MIS_lec_1-3")
            
        Returns:
            Progress dict or None if not found
        """
        query = """
            SELECT 
                user_id, deck_id, course_id, progress,
                cards_studied, total_cards, last_studied, study_streak,
                created_at, updated_at
            FROM user_deck_progress
            WHERE user_id = $1 AND deck_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, deck_id)
            
            if not row:
                return None
            
            return dict(row)
    
    async def get_user_deck_progress_all(
        self,
        user_id: str,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all deck progress for a user.
        
        Args:
            user_id: Firebase UID
            course_id: Optional course filter
            
        Returns:
            List of progress records
        """
        base_query = """
            SELECT 
                user_id, deck_id, course_id, progress,
                cards_studied, total_cards, last_studied, study_streak,
                created_at, updated_at
            FROM user_deck_progress
            WHERE user_id = $1
        """
        
        params = [user_id]
        
        if course_id:
            base_query += " AND course_id = $2"
            params.append(course_id)
        
        base_query += " ORDER BY last_studied DESC"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            return [dict(row) for row in rows]
    
    async def update_deck_progress(
        self,
        user_id: str,
        deck_id: str,
        course_id: str,
        progress: float,
        cards_studied: int,
        total_cards: int,
        study_streak: int = 0
    ) -> Dict[str, Any]:
        """
        Update or create deck progress.
        
        Args:
            user_id: Firebase UID
            deck_id: Deck identifier
            course_id: Course identifier
            progress: Progress as float 0.0 to 1.0
            cards_studied: Number of cards studied
            total_cards: Total cards in deck
            study_streak: Consecutive study days
            
        Returns:
            Updated progress dict
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO user_deck_progress (
                user_id, deck_id, course_id, progress,
                cards_studied, total_cards, last_studied, study_streak,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $7, $7)
            ON CONFLICT (user_id, deck_id)
            DO UPDATE SET
                progress = $4,
                cards_studied = $5,
                total_cards = $6,
                last_studied = $7,
                study_streak = $8,
                updated_at = $7
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, deck_id, course_id, progress,
                cards_studied, total_cards, now, study_streak
            )
            
            logger.info(f"Updated deck progress for user {user_id}, deck {deck_id}")
            return dict(row)
    
    # ==================== Quiz Attempt Operations ====================
    
    async def record_quiz_attempt(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str,
        flashcard_id: str,
        question_hash: str,
        is_correct: bool,
        partial_credit: float = 0.0,
        time_taken_seconds: Optional[int] = None,
        difficulty_level: Optional[str] = None
    ) -> int:
        """
        Record a single quiz question attempt.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            flashcard_id: Source flashcard ID
            question_hash: Hash of the question text
            is_correct: Whether the answer was correct
            partial_credit: Partial credit score (0.0 to 1.0)
            time_taken_seconds: Time taken to answer
            difficulty_level: Difficulty level of the question
            
        Returns:
            ID of the created attempt record
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO user_quiz_attempts (
                user_id, course_id, lecture_id, flashcard_id,
                question_hash, is_correct, partial_credit,
                time_taken_seconds, difficulty_level, timestamp
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, course_id, lecture_id, flashcard_id,
                question_hash, is_correct, partial_credit,
                time_taken_seconds, difficulty_level, now
            )
            
            return row["id"]
    
    async def bulk_record_quiz_attempts(
        self,
        attempts: List[Dict[str, Any]]
    ) -> int:
        """
        Record multiple quiz attempts in a single transaction.
        
        Args:
            attempts: List of attempt dicts with keys:
                user_id, course_id, lecture_id, flashcard_id,
                question_hash, is_correct, partial_credit,
                time_taken_seconds, difficulty_level
                
        Returns:
            Number of attempts recorded
        """
        if not attempts:
            return 0
        
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO user_quiz_attempts (
                user_id, course_id, lecture_id, flashcard_id,
                question_hash, is_correct, partial_credit,
                time_taken_seconds, difficulty_level, timestamp
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for attempt in attempts:
                    await conn.execute(
                        query,
                        attempt["user_id"],
                        attempt["course_id"],
                        attempt["lecture_id"],
                        attempt["flashcard_id"],
                        attempt["question_hash"],
                        attempt["is_correct"],
                        attempt.get("partial_credit", 0.0),
                        attempt.get("time_taken_seconds"),
                        attempt.get("difficulty_level"),
                        now
                    )
        
        logger.info(f"Recorded {len(attempts)} quiz attempts")
        return len(attempts)
    
    async def get_attempted_questions(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Set[str]:
        """
        Get set of question hashes the user has already attempted.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            Set of question hashes
        """
        query = """
            SELECT DISTINCT question_hash
            FROM user_quiz_attempts
            WHERE user_id = $1 AND course_id = $2 AND lecture_id = $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, course_id, lecture_id)
            return {row["question_hash"] for row in rows}
    
    async def get_seen_flashcard_ids(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Set[str]:
        """
        Get set of flashcard IDs the user has been tested on.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            Set of flashcard IDs
        """
        query = """
            SELECT DISTINCT flashcard_id
            FROM user_quiz_attempts
            WHERE user_id = $1 AND course_id = $2 AND lecture_id = $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, course_id, lecture_id)
            return {row["flashcard_id"] for row in rows}
    
    # ==================== Flashcard Performance Operations ====================
    
    async def get_flashcard_performance(
        self,
        user_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get performance data for a specific flashcard.
        
        Args:
            user_id: Firebase UID
            flashcard_id: Flashcard identifier
            
        Returns:
            Performance dict or None if not found
        """
        query = """
            SELECT 
                user_id, flashcard_id, course_id, lecture_id,
                is_weak, next_level, coverage_score, accuracy_score,
                momentum_score, comfortability_score, total_points_earned,
                performance_data, last_updated, created_at
            FROM user_flashcard_performance
            WHERE user_id = $1 AND flashcard_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, flashcard_id)
            
            if not row:
                return None
            
            result = dict(row)
            # Parse JSONB field
            if result.get("performance_data"):
                if isinstance(result["performance_data"], str):
                    result["performance_data"] = json.loads(result["performance_data"])
            
            return result
    
    async def get_user_performance_for_lecture(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregated user performance for a lecture.
        
        This returns a summary of all flashcard performances for a lecture,
        including weakness scores.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            Dict with flashcards and questions performance data
        """
        query = """
            SELECT 
                flashcard_id, is_weak, next_level,
                coverage_score, accuracy_score, momentum_score,
                performance_data
            FROM user_flashcard_performance
            WHERE user_id = $1 AND course_id = $2 AND lecture_id = $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, course_id, lecture_id)
            
            if not rows:
                return None
            
            flashcards = {}
            questions = {}
            
            for row in rows:
                flashcard_id = row["flashcard_id"]
                perf_data = row["performance_data"]
                
                if isinstance(perf_data, str):
                    perf_data = json.loads(perf_data)
                
                # Extract performance by level
                perf_by_level = perf_data.get("performance_by_level", {})
                
                correct = sum(p.get("correct", 0) for p in perf_by_level.values())
                incorrect = sum(p.get("attempts", 0) - p.get("correct", 0) for p in perf_by_level.values())
                
                flashcards[flashcard_id] = {
                    "correct": correct,
                    "incorrect": incorrect,
                    "last_attempted": perf_data.get("last_attempted")
                }
                
                # Extract question-level data if available
                question_data = perf_data.get("questions", {})
                questions.update(question_data)
            
            return {
                "user_id": user_id,
                "course_id": course_id,
                "lecture_id": lecture_id,
                "flashcards": flashcards,
                "questions": questions
            }
    
    async def update_flashcard_performance(
        self,
        user_id: str,
        flashcard_id: str,
        course_id: str,
        lecture_id: str,
        is_weak: bool,
        next_level: str,
        coverage_score: float,
        accuracy_score: float,
        momentum_score: float,
        comfortability_score: float,
        total_points_earned: float,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update or create flashcard performance record.
        
        Args:
            user_id: Firebase UID
            flashcard_id: Flashcard identifier
            course_id: Course identifier
            lecture_id: Lecture identifier
            is_weak: Whether the flashcard is marked as weak
            next_level: Recommended next question level
            coverage_score: Coverage score (0-2)
            accuracy_score: Accuracy score (can be negative)
            momentum_score: Momentum score (0-1)
            comfortability_score: Comfortability score
            total_points_earned: Total points earned
            performance_data: JSONB data with detailed stats
            
        Returns:
            Updated performance dict
        """
        now = datetime.now(timezone.utc)
        perf_json = json.dumps(performance_data)
        
        query = """
            INSERT INTO user_flashcard_performance (
                user_id, flashcard_id, course_id, lecture_id,
                is_weak, next_level, coverage_score, accuracy_score,
                momentum_score, comfortability_score, total_points_earned,
                performance_data, last_updated, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13, $13)
            ON CONFLICT (user_id, flashcard_id)
            DO UPDATE SET
                is_weak = $5,
                next_level = $6,
                coverage_score = $7,
                accuracy_score = $8,
                momentum_score = $9,
                comfortability_score = $10,
                total_points_earned = $11,
                performance_data = $12::jsonb,
                last_updated = $13
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, flashcard_id, course_id, lecture_id,
                is_weak, next_level, coverage_score, accuracy_score,
                momentum_score, comfortability_score, total_points_earned,
                perf_json, now
            )
            
            result = dict(row)
            if result.get("performance_data"):
                if isinstance(result["performance_data"], str):
                    result["performance_data"] = json.loads(result["performance_data"])
            
            logger.debug(f"Updated flashcard performance for {flashcard_id}")
            return result
    
    async def get_weak_flashcards(
        self,
        user_id: str,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all weak flashcards for a user.
        
        Args:
            user_id: Firebase UID
            course_id: Optional course filter
            
        Returns:
            List of weak flashcard performance records
        """
        base_query = """
            SELECT 
                user_id, flashcard_id, course_id, lecture_id,
                is_weak, next_level, coverage_score, accuracy_score,
                momentum_score, comfortability_score, total_points_earned,
                performance_data, last_updated
            FROM user_flashcard_performance
            WHERE user_id = $1 AND is_weak = TRUE
        """
        
        params = [user_id]
        
        if course_id:
            base_query += " AND course_id = $2"
            params.append(course_id)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            
            results = []
            for row in rows:
                result = dict(row)
                if result.get("performance_data"):
                    if isinstance(result["performance_data"], str):
                        result["performance_data"] = json.loads(result["performance_data"])
                results.append(result)
            
            return results
    
    async def get_flashcard_performances_for_lecture(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all flashcard performances for a specific lecture.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            List of flashcard performance records
        """
        query = """
            SELECT 
                user_id, flashcard_id, course_id, lecture_id,
                is_weak, next_level, coverage_score, accuracy_score,
                momentum_score, comfortability_score, total_points_earned,
                performance_data, last_updated
            FROM user_flashcard_performance
            WHERE user_id = $1 AND course_id = $2 AND lecture_id = $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, course_id, lecture_id)
            
            results = []
            for row in rows:
                result = dict(row)
                if result.get("performance_data"):
                    if isinstance(result["performance_data"], str):
                        result["performance_data"] = json.loads(result["performance_data"])
                results.append(result)
            
            return results
    
    async def calculate_weakness_scores(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str
    ) -> Dict[str, float]:
        """
        Calculate weakness scores for all flashcards in a lecture.
        
        Formula: (incorrect + 1) / (correct + 1)
        Higher score = more weakness = needs more practice
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            Dict mapping flashcard_id to weakness score
        """
        performances = await self.get_flashcard_performances_for_lecture(
            user_id, course_id, lecture_id
        )
        
        weakness_scores = {}
        
        for perf in performances:
            flashcard_id = perf["flashcard_id"]
            perf_data = perf.get("performance_data", {})
            perf_by_level = perf_data.get("performance_by_level", {})
            
            correct = sum(p.get("correct", 0) for p in perf_by_level.values())
            attempts = sum(p.get("attempts", 0) for p in perf_by_level.values())
            incorrect = attempts - correct
            
            # Calculate weakness score
            weakness_scores[flashcard_id] = (incorrect + 1) / (correct + 1)
        
        return weakness_scores







