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
    
    def __init__(self, database):
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
            partial_credit = question_result.partial_credit_score
            
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
                performance.performance_by_level[level] = PerformanceByLevel(points=0.0)
            
            performance.performance_by_level[level].attempts += 1
            if is_correct:
                performance.performance_by_level[level].correct += 1
            
            # Calculate points earned for this attempt (supports partial credit)
            points_earned = self._calculate_points_for_attempt(level, is_correct, partial_credit if partial_credit is not None else 0.0)
            
            # Add points to performance_by_level
            performance.performance_by_level[level].points += points_earned
            
            # Add to recent_attempts (capped)
            new_attempt = RecentAttempt(
                timestamp=datetime.now(timezone.utc),
                level=level,
                is_correct=is_correct,
                points_earned=points_earned
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
            # total_points_earned is the same as accuracy_score (cumulative points)
            performance.total_points_earned = performance.accuracy_score
            performance.momentum_score = self._calculate_momentum_score(
                performance.recent_attempts
            )
            
            # Calculate Comfortability Score and determine next level
            performance.comfortability_score = self._calculate_comfortability_score(
                performance.recent_attempts
            )
            performance.question_next_level = self._determine_question_next_level(
                performance.comfortability_score
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
                        f"accuracy={performance.accuracy_score:.2f}, "
                        f"momentum={performance.momentum_score:.2f}, "
                        f"cs={performance.comfortability_score:.2f}, "
                        f"next_level={performance.question_next_level}, "
                        f"is_weak={performance.is_weak}")
        
        # Invalidate deck readiness cache for affected lectures
        from app.services.readiness_v2_service import ReadinessV2Service
        for lecture in affected_lectures:
            ReadinessV2Service.invalidate_deck_cache(user_id, [lecture])
        
        return list(affected_lectures)
    
    def _map_difficulty_to_level(self, difficulty: str) -> str:
        """Map various difficulty representations to standardized levels."""
        return config.DIFFICULTY_LEVEL_MAP.get(difficulty.lower(), "medium")
    
    def _calculate_points_for_attempt(self, level: str, is_correct: bool, partial_credit: float = 0.0) -> float:
        """
        Calculate points earned for a single attempt based on level and correctness.
        Supports partial credit for partially correct answers.
        
        Args:
            level: Difficulty level (easy, medium, hard, boss)
            is_correct: Whether the answer was fully correct
            partial_credit: Optional partial credit score (0.0 to 1.0) for MCA questions
            
        Returns:
            Points earned (can be negative for incorrect answers on hard/boss levels, supports decimals)
        """
        level_points = config.ACCURACY_POINTS.get(level, {})
        
        # If partial credit is provided (non-zero) and it's not a fully correct answer
        if partial_credit > 0.0 and not is_correct:
            max_points = level_points.get("correct", 0)
            return max_points * partial_credit
        
        # Otherwise, use standard binary scoring
        if is_correct:
            return float(level_points.get("correct", 0))
        else:
            return float(level_points.get("incorrect", 0))
    
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
    
    def _calculate_accuracy_score(self, performance_by_level: Dict[str, PerformanceByLevel]) -> float:
        """
        Calculate accuracy score for a flashcard.
        
        Formula: Sum of points earned across all levels (supports partial credit).
        Can be negative.
        """
        total_accuracy = 0.0
        
        for level, perf in performance_by_level.items():
            # Use the stored points which already accounts for partial credit
            total_accuracy += perf.points
        
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
            
            # Use stored points_earned if available, otherwise calculate from level
            if hasattr(attempt, 'points_earned') and attempt.points_earned is not None:
                earned_points = attempt.points_earned
            else:
                # Fallback: calculate from level and is_correct (for backward compatibility)
                level_points = config.ACCURACY_POINTS.get(attempt.level, {})
                if attempt.is_correct:
                    earned_points = level_points.get("correct", 1)
                else:
                    earned_points = level_points.get("incorrect", 0)
            
            # Get max points for this level (for normalization)
            level_points = config.ACCURACY_POINTS.get(attempt.level, {})
            max_points = level_points.get("correct", 1)
            
            weighted_correct += earned_points * decay_factor
            weighted_total += max_points * decay_factor
        
        if weighted_total == 0:
            return 0.0
        
        # Normalize to 0-1 range (can be negative if many incorrect answers)
        momentum = weighted_correct / weighted_total
        return max(0.0, min(1.0, momentum))  # Clamp to [0, 1]
    
    def _calculate_comfortability_score(self, recent_attempts: List[RecentAttempt]) -> float:
        """
        Calculate Comfortability Score (CS) based on recent performance.
        
        Formula: Average points_earned in the most recent 3 attempts + max(2 - wrong answers in last 3, 0)
        
        Args:
            recent_attempts: List of recent attempts (already capped)
            
        Returns:
            Comfortability score (float)
        """
        if not recent_attempts:
            return 0.0
        
        # Get the last 3 attempts (or fewer if less than 3 exist)
        last_three = recent_attempts[-3:]
        
        # Calculate average points earned
        total_points = sum(attempt.points_earned for attempt in last_three)
        avg_points = total_points / len(last_three)
        
        # Count wrong answers in last 3 attempts
        wrong_answers = sum(1 for attempt in last_three if not attempt.is_correct)
        
        # Calculate bonus: max(2 - wrong_answers, 0)
        bonus = max(2 - wrong_answers, 0)
        
        # Final CS
        cs = avg_points + bonus
        
        return cs
    
    def _determine_question_next_level(self, comfortability_score: float) -> str:
        """
        Determine the recommended next question difficulty level based on CS.
        
        Thresholds (from config):
        - CS < 1.5 → 'easy'
        - 1.5 <= CS < 3.0 → 'medium'
        - 3.0 <= CS < 4.0 → 'hard'
        - CS >= 4.0 → 'boss'
        
        Args:
            comfortability_score: The calculated CS value
            
        Returns:
            Recommended level string ('easy', 'medium', 'hard', or 'boss')
        """
        if comfortability_score < config.CS_THRESHOLD_EASY_TO_MEDIUM:
            return 'easy'
        elif comfortability_score < config.CS_THRESHOLD_MEDIUM_TO_HARD:
            return 'medium'
        elif comfortability_score < config.CS_THRESHOLD_HARD_TO_BOSS:
            return 'hard'
        else:
            return 'boss'
    
    def _determine_weak_state(
        self,
        accuracy_score: float,
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

