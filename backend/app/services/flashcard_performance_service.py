"""
Service for managing user flashcard performance tracking.

This service is responsible for updating and calculating performance metrics
at the flashcard level for the Exam Readiness Engine V2.
"""

import math
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.readiness_v2 import (
    UserFlashcardPerformance,
    PerformanceByLevel,
    RecentAttempt
)
from app.models.adaptive_quiz import QuestionResult
from app import readiness_config as config

logger = logging.getLogger(__name__)


class FlashcardPerformanceService:
    """
    Service for tracking and calculating flashcard-level performance.
    
    This service updates the user_flashcard_performance collection and
    recalculates the three pillar scores (coverage, accuracy, momentum)
    for each flashcard.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.user_flashcard_performance
    
    async def initialize_indexes(self):
        """Create indexes for efficient querying."""
        await self.collection.create_index(
            [("user_id", 1), ("flashcard_id", 1)],
            unique=True
        )
        logger.info("Flashcard performance indexes created")
    
    async def update_performance_from_quiz(
        self,
        user_id: str,
        course_id: str,
        lecture_id: str,
        question_results: List[QuestionResult],
        difficulty: str
    ) -> List[str]:
        """
        Update flashcard performance based on quiz results.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            lecture_id: Lecture identifier
            question_results: List of graded question results
            difficulty: Quiz difficulty (e.g., "medium", "hard", "level_1")
            
        Returns:
            List of affected lecture IDs (for exam readiness recalculation)
        """
        # Map difficulty to standardized level
        level = self._map_difficulty_to_level(difficulty)
        
        affected_lectures = set()
        affected_lectures.add(lecture_id)
        
        for question_result in question_results:
            flashcard_id = question_result.source_flashcard_id
            is_correct = question_result.is_correct
            
            # Fetch or create performance document
            perf_doc = await self.collection.find_one({
                "user_id": user_id,
                "flashcard_id": flashcard_id
            })
            
            if perf_doc:
                # Update existing document
                performance = UserFlashcardPerformance(**perf_doc)
            else:
                # Create new document
                performance = UserFlashcardPerformance(
                    user_id=user_id,
                    flashcard_id=flashcard_id,
                    course_id=course_id,
                    lecture_id=lecture_id
                )
            
            # Update performance_by_level
            if level not in performance.performance_by_level:
                performance.performance_by_level[level] = PerformanceByLevel()
            
            performance.performance_by_level[level].attempts += 1
            if is_correct:
                performance.performance_by_level[level].correct += 1
            
            # Add to recent_attempts (capped)
            new_attempt = RecentAttempt(
                timestamp=datetime.now(timezone.utc),
                level=level,
                is_correct=is_correct
            )
            performance.recent_attempts.append(new_attempt)
            
            # Cap recent_attempts to configured limit
            if len(performance.recent_attempts) > config.MOMENTUM_RECENT_ATTEMPTS_LIMIT:
                performance.recent_attempts = performance.recent_attempts[-config.MOMENTUM_RECENT_ATTEMPTS_LIMIT:]
            
            # Recalculate scores
            performance.coverage_score = self._calculate_coverage_score(
                performance.performance_by_level
            )
            performance.accuracy_score = self._calculate_accuracy_score(
                performance.performance_by_level
            )
            performance.momentum_score = self._calculate_momentum_score(
                performance.recent_attempts
            )
            
            # Update weak state
            performance.is_weak = self._determine_weak_state(
                performance.accuracy_score,
                performance.is_weak,
                is_correct
            )
            
            performance.last_updated = datetime.now(timezone.utc)
            
            # Save to database
            await self.collection.update_one(
                {"user_id": user_id, "flashcard_id": flashcard_id},
                {"$set": performance.model_dump(exclude={"id"})},
                upsert=True
            )
            
            logger.debug(f"Updated performance for flashcard {flashcard_id}: "
                        f"coverage={performance.coverage_score:.2f}, "
                        f"accuracy={performance.accuracy_score}, "
                        f"momentum={performance.momentum_score:.2f}, "
                        f"is_weak={performance.is_weak}")
        
        return list(affected_lectures)
    
    def _map_difficulty_to_level(self, difficulty: str) -> str:
        """Map various difficulty representations to standardized levels."""
        return config.DIFFICULTY_LEVEL_MAP.get(difficulty.lower(), "medium")
    
    def _calculate_coverage_score(self, performance_by_level: Dict[str, PerformanceByLevel]) -> float:
        """
        Calculate coverage score for a flashcard.
        
        Formula: Sum of (attempts * coverage_points) for each level, capped at 2.
        """
        total_coverage = 0.0
        
        for level, perf in performance_by_level.items():
            if level in config.COVERAGE_POINTS:
                total_coverage += perf.attempts * config.COVERAGE_POINTS[level]
        
        # Cap at maximum
        return min(total_coverage, config.MAX_COVERAGE_POINTS_PER_FLASHCARD)
    
    def _calculate_accuracy_score(self, performance_by_level: Dict[str, PerformanceByLevel]) -> int:
        """
        Calculate accuracy score for a flashcard.
        
        Formula: Sum of (correct * positive_points + incorrect * negative_points) for each level.
        Can be negative.
        """
        total_accuracy = 0
        
        for level, perf in performance_by_level.items():
            if level in config.ACCURACY_POINTS:
                correct_points = perf.correct * config.ACCURACY_POINTS[level]["correct"]
                incorrect = perf.attempts - perf.correct
                incorrect_points = incorrect * config.ACCURACY_POINTS[level]["incorrect"]
                total_accuracy += correct_points + incorrect_points
        
        return total_accuracy
    
    def _calculate_momentum_score(self, recent_attempts: List[RecentAttempt]) -> float:
        """
        Calculate momentum score using time-weighted accuracy.
        
        Formula: Sum(points_earned * decay) / Sum(max_points * decay)
        Returns a value between 0 and 1 (or negative if recent performance is poor).
        """
        if not recent_attempts:
            return 0.0
        
        now = datetime.now(timezone.utc)
        weighted_correct = 0.0
        weighted_total = 0.0
        
        for attempt in recent_attempts:
            # Calculate time decay factor
            attempt_ts = attempt.timestamp
            # Normalize attempt timestamp to be timezone-aware (UTC) if it's naive
            if isinstance(attempt_ts, datetime) and attempt_ts.tzinfo is None:
                attempt_ts = attempt_ts.replace(tzinfo=timezone.utc)
            age_days = (now - attempt_ts).total_seconds() / 86400
            decay_factor = math.exp(-math.log(2) * age_days / config.MOMENTUM_HALF_LIFE_DAYS)
            
            # Get points for this level
            level_points = config.ACCURACY_POINTS.get(attempt.level, {})
            max_points = level_points.get("correct", 1)
            
            if attempt.is_correct:
                earned_points = max_points
            else:
                earned_points = level_points.get("incorrect", 0)
            
            weighted_correct += earned_points * decay_factor
            weighted_total += max_points * decay_factor
        
        if weighted_total == 0:
            return 0.0
        
        # Normalize to 0-1 range (can be negative if many incorrect answers)
        momentum = weighted_correct / weighted_total
        return max(0.0, min(1.0, momentum))  # Clamp to [0, 1]
    
    def _determine_weak_state(
        self,
        accuracy_score: int,
        current_is_weak: bool,
        is_correct: bool
    ) -> bool:
        """
        Determine if a flashcard should be marked as weak.
        
        State machine:
        - If incorrect answer: always mark as weak
        - If correct and currently weak: check if accuracy_score >= recovery threshold
        - If correct and not weak: remain not weak
        """
        # If user got it wrong, it's weak
        if not is_correct:
            return True
        
        # If user got it right and it's currently weak, check for redemption
        if current_is_weak:
            if accuracy_score >= config.WEAK_FLASHCARD_RECOVERY_THRESHOLD:
                return False  # Redeemed!
            else:
                return True  # Still weak
        
        # If user got it right and it's not weak, keep it not weak
        return False
    
    async def get_flashcard_performance(
        self,
        user_id: str,
        flashcard_id: str
    ) -> Optional[UserFlashcardPerformance]:
        """Get performance data for a specific flashcard."""
        perf_doc = await self.collection.find_one({
            "user_id": user_id,
            "flashcard_id": flashcard_id
        })
        
        if perf_doc:
            return UserFlashcardPerformance(**perf_doc)
        return None
    
    async def get_weak_flashcards_for_user(
        self,
        user_id: str,
        course_id: Optional[str] = None
    ) -> List[UserFlashcardPerformance]:
        """Get all weak flashcards for a user, optionally filtered by course."""
        query = {"user_id": user_id, "is_weak": True}
        if course_id:
            query["course_id"] = course_id
        
        cursor = self.collection.find(query)
        weak_perfs = await cursor.to_list(length=None)
        
        return [UserFlashcardPerformance(**perf) for perf in weak_perfs]


def get_flashcard_performance_service(db=None) -> FlashcardPerformanceService:
    """Dependency injection helper."""
    from app.database import get_database
    if db is None:
        db = get_database()
    return FlashcardPerformanceService(db)

