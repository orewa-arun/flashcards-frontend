"""
Service for managing user flashcard performance tracking using PostgreSQL.

This service is responsible for updating and calculating performance metrics
at the flashcard level for the Exam Readiness Engine V2.
"""

import math
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
import asyncpg

from app.repositories.analytics_repository import AnalyticsRepository
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
    
    This service updates the user_flashcard_performance table and
    recalculates the three pillar scores (coverage, accuracy, momentum)
    for each flashcard.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.repository = AnalyticsRepository(pool)
    
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
            
            # Fetch existing performance
            perf_data = await self.repository.get_flashcard_performance(user_id, flashcard_id)
            
            if perf_data:
                # Parse existing performance data
                performance_json = perf_data.get("performance_data", {})
                performance_by_level = performance_json.get("performance_by_level", {})
                recent_attempts = performance_json.get("recent_attempts", [])
                is_weak = perf_data.get("is_weak", False)
            else:
                # Initialize new performance
                performance_by_level = {}
                recent_attempts = []
                is_weak = False
            
            # Update performance_by_level
            if level not in performance_by_level:
                performance_by_level[level] = {"attempts": 0, "correct": 0, "points": 0.0}
            
            performance_by_level[level]["attempts"] += 1
            if is_correct:
                performance_by_level[level]["correct"] += 1
            
            # Calculate points earned for this attempt (supports partial credit)
            points_earned = self._calculate_points_for_attempt(
                level, is_correct, 
                partial_credit if partial_credit is not None else 0.0
            )
            
            # Add points to performance_by_level
            performance_by_level[level]["points"] += points_earned
            
            # Add to recent_attempts (capped)
            new_attempt = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "is_correct": is_correct,
                "points_earned": points_earned
            }
            recent_attempts.append(new_attempt)
            
            # Cap recent_attempts to configured limit
            if len(recent_attempts) > config.MOMENTUM_RECENT_ATTEMPTS_LIMIT:
                recent_attempts = recent_attempts[-config.MOMENTUM_RECENT_ATTEMPTS_LIMIT:]
            
            # Recalculate scores
            coverage_score = self._calculate_coverage_score(performance_by_level)
            accuracy_score = self._calculate_accuracy_score(performance_by_level)
            momentum_score = self._calculate_momentum_score(recent_attempts)
            comfortability_score = self._calculate_comfortability_score(recent_attempts)
            next_level = self._determine_question_next_level(comfortability_score)
            
            # Update weak state
            is_weak = self._determine_weak_state(accuracy_score, is_weak, is_correct)
            
            # Prepare performance_data JSONB
            performance_data = {
                "performance_by_level": performance_by_level,
                "recent_attempts": recent_attempts
            }
            
            # Save to database
            await self.repository.update_flashcard_performance(
                user_id=user_id,
                flashcard_id=flashcard_id,
                course_id=course_id,
                lecture_id=lecture_id,
                is_weak=is_weak,
                next_level=next_level,
                coverage_score=coverage_score,
                accuracy_score=accuracy_score,
                momentum_score=momentum_score,
                comfortability_score=comfortability_score,
                total_points_earned=accuracy_score,
                performance_data=performance_data
            )
            
            # Also record the individual quiz attempt
            question_hash = self._hash_question(question_result)
            await self.repository.record_quiz_attempt(
                user_id=user_id,
                course_id=course_id,
                lecture_id=lecture_id,
                flashcard_id=flashcard_id,
                question_hash=question_hash,
                is_correct=is_correct,
                partial_credit=partial_credit if partial_credit else 0.0,
                time_taken_seconds=question_result.time_taken if question_result.time_taken else 0,
                difficulty_level=level
            )
            
            logger.debug(f"Updated performance for flashcard {flashcard_id}: "
                        f"coverage={coverage_score:.2f}, "
                        f"accuracy={accuracy_score:.2f}, "
                        f"momentum={momentum_score:.2f}, "
                        f"cs={comfortability_score:.2f}, "
                        f"next_level={next_level}, "
                        f"is_weak={is_weak}")
        
        # Invalidate deck readiness cache for affected lectures
        from app.services.readiness_v2_service import ReadinessV2Service
        for lecture in affected_lectures:
            ReadinessV2Service.invalidate_deck_cache(user_id, [lecture])
        
        return list(affected_lectures)
    
    def _hash_question(self, question_result: QuestionResult) -> str:
        """Generate a hash for a question to track unique attempts."""
        import hashlib
        question_text = question_result.question.get("question_text", "") if isinstance(question_result.question, dict) else str(question_result.question)
        return hashlib.sha256(question_text.encode()).hexdigest()[:16]
    
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
    
    def _calculate_coverage_score(self, performance_by_level: Dict[str, Dict]) -> float:
        """
        Calculate coverage score for a flashcard.
        
        Formula: Sum of (attempts * coverage_points) for each level, capped at 2.
        """
        total_coverage = 0.0
        
        for level, perf in performance_by_level.items():
            if level in config.COVERAGE_POINTS:
                total_coverage += perf.get("attempts", 0) * config.COVERAGE_POINTS[level]
        
        # Cap at maximum
        return min(total_coverage, config.MAX_COVERAGE_POINTS_PER_FLASHCARD)
    
    def _calculate_accuracy_score(self, performance_by_level: Dict[str, Dict]) -> float:
        """
        Calculate accuracy score for a flashcard.
        
        Formula: Sum of points earned across all levels (supports partial credit).
        Can be negative.
        """
        total_accuracy = 0.0
        
        for level, perf in performance_by_level.items():
            # Use the stored points which already accounts for partial credit
            total_accuracy += perf.get("points", 0.0)
        
        return total_accuracy
    
    def _calculate_momentum_score(self, recent_attempts: List[Dict]) -> float:
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
            # Parse timestamp
            attempt_ts = attempt.get("timestamp")
            if isinstance(attempt_ts, str):
                attempt_ts = datetime.fromisoformat(attempt_ts.replace('Z', '+00:00'))
            if attempt_ts.tzinfo is None:
                attempt_ts = attempt_ts.replace(tzinfo=timezone.utc)
            
            age_days = (now - attempt_ts).total_seconds() / 86400
            decay_factor = math.exp(-math.log(2) * age_days / config.MOMENTUM_HALF_LIFE_DAYS)
            
            # Use stored points_earned
            earned_points = attempt.get("points_earned", 0)
            
            # Get max points for this level (for normalization)
            level = attempt.get("level", "medium")
            level_points = config.ACCURACY_POINTS.get(level, {})
            max_points = level_points.get("correct", 1)
            
            weighted_correct += earned_points * decay_factor
            weighted_total += max_points * decay_factor
        
        if weighted_total == 0:
            return 0.0
        
        # Normalize to 0-1 range (can be negative if many incorrect answers)
        momentum = weighted_correct / weighted_total
        return max(0.0, min(1.0, momentum))  # Clamp to [0, 1]
    
    def _calculate_comfortability_score(self, recent_attempts: List[Dict]) -> float:
        """
        Calculate Comfortability Score (CS) based on recent performance.
        
        Formula: Average points_earned in the most recent 3 attempts + max(2 - wrong answers in last 3, 0)
        
        Args:
            recent_attempts: List of recent attempts
            
        Returns:
            Comfortability score (float)
        """
        if not recent_attempts:
            return 0.0
        
        # Get the last 3 attempts (or fewer if less than 3 exist)
        last_three = recent_attempts[-3:]
        
        # Calculate average points earned
        total_points = sum(attempt.get("points_earned", 0) for attempt in last_three)
        avg_points = total_points / len(last_three)
        
        # Count wrong answers in last 3 attempts
        wrong_answers = sum(1 for attempt in last_three if not attempt.get("is_correct", False))
        
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
        perf_data = await self.repository.get_flashcard_performance(user_id, flashcard_id)
        
        if not perf_data:
            return None
        
        # Convert to Pydantic model
        return self._dict_to_performance_model(perf_data)
    
    async def get_weak_flashcards_for_user(
        self,
        user_id: str,
        course_id: Optional[str] = None
    ) -> List[UserFlashcardPerformance]:
        """Get all weak flashcards for a user, optionally filtered by course."""
        weak_perfs = await self.repository.get_weak_flashcards(user_id, course_id)
        
        return [self._dict_to_performance_model(perf) for perf in weak_perfs]
    
    def _dict_to_performance_model(self, perf_data: Dict) -> UserFlashcardPerformance:
        """Convert a dict from the database to a Pydantic model."""
        performance_json = perf_data.get("performance_data", {})
        
        # Parse performance_by_level
        perf_by_level = {}
        for level, data in performance_json.get("performance_by_level", {}).items():
            perf_by_level[level] = PerformanceByLevel(
                attempts=data.get("attempts", 0),
                correct=data.get("correct", 0),
                points=data.get("points", 0.0)
            )
        
        # Parse recent_attempts
        recent_attempts = []
        for attempt in performance_json.get("recent_attempts", []):
            timestamp = attempt.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            recent_attempts.append(RecentAttempt(
                timestamp=timestamp,
                level=attempt.get("level", "medium"),
                is_correct=attempt.get("is_correct", False),
                points_earned=attempt.get("points_earned", 0.0)
            ))
        
        return UserFlashcardPerformance(
            user_id=perf_data["user_id"],
            flashcard_id=perf_data["flashcard_id"],
            course_id=perf_data["course_id"],
            lecture_id=perf_data["lecture_id"],
            is_weak=perf_data.get("is_weak", False),
            question_next_level=perf_data.get("next_level", "easy"),
            coverage_score=perf_data.get("coverage_score", 0.0),
            accuracy_score=perf_data.get("accuracy_score", 0.0),
            momentum_score=perf_data.get("momentum_score", 0.0),
            comfortability_score=perf_data.get("comfortability_score", 0.0),
            total_points_earned=perf_data.get("total_points_earned", 0.0),
            performance_by_level=perf_by_level,
            recent_attempts=recent_attempts,
            last_updated=perf_data.get("last_updated")
        )


def get_flashcard_performance_service(pool: asyncpg.Pool = None) -> FlashcardPerformanceService:
    """Dependency injection helper."""
    if pool is None:
        raise ValueError("PostgreSQL pool is required")
    return FlashcardPerformanceService(pool)
