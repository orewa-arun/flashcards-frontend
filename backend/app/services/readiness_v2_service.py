"""
Service for calculating and persisting exam readiness scores using PostgreSQL.

This service aggregates flashcard-level performance data to compute
the overall exam readiness score with three pillars: Coverage, Accuracy, and Momentum.
"""

import json
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
import asyncpg

from app.repositories.quiz_repository import QuizRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.models.readiness_v2 import (
    UserExamReadiness,
    UserFlashcardPerformance,
    WeakFlashcard,
    RawScores,
    MaxPossibleScores,
    PerformanceByLevel,
    RecentAttempt
)
from app import readiness_config as config

logger = logging.getLogger(__name__)


class ReadinessV2Service:
    """
    Service for calculating and persisting exam readiness scores.
    
    This service aggregates data from user_flashcard_performance table
    to compute the final exam readiness score.
    """
    
    # Class-level cache for deck readiness (shared across instances)
    _readiness_cache: Dict[str, Tuple[UserExamReadiness, datetime]] = {}
    _cache_ttl = timedelta(seconds=30)
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.quiz_repository = QuizRepository(pool)
        self.analytics_repository = AnalyticsRepository(pool)
    
    async def calculate_and_persist_exam_readiness(
        self,
        user_id: str,
        course_id: str,
        exam_id: str
    ) -> UserExamReadiness:
        """
        Calculate exam readiness score and persist it.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            exam_id: Exam identifier from timetable
            
        Returns:
            UserExamReadiness document
        """
        try:
            # Step 1: Get exam lectures from timetable
            exam_lectures = await self.quiz_repository.get_exam_lectures(course_id, exam_id)
            
            if not exam_lectures:
                logger.warning(f"No lectures found for exam {exam_id} in course {course_id}")
                return self._create_empty_readiness(user_id, course_id, exam_id)
            
            # Step 2: Load all flashcard IDs for those lectures
            flashcard_ids = await self._fetch_exam_flashcard_ids(course_id, exam_lectures)
            
            if not flashcard_ids:
                logger.warning(f"No flashcards found for exam {exam_id}")
                return self._create_empty_readiness(user_id, course_id, exam_id)
            
            # Step 3: Fetch all user flashcard performance documents
            flashcard_performances = await self._fetch_user_flashcard_performances(
                user_id, flashcard_ids
            )
            
            # Step 4: Aggregate scores
            raw_scores = self._aggregate_scores(flashcard_performances)
            
            # Step 5: Calculate max possible scores
            max_possible_scores = self._calculate_max_possible_scores(len(flashcard_ids))
            
            # Step 6: Normalize to factors (0-1)
            coverage_factor = self._normalize_score(
                raw_scores.coverage_total,
                max_possible_scores.coverage
            )
            accuracy_factor = self._normalize_score(
                raw_scores.accuracy_total,
                max_possible_scores.accuracy
            )
            momentum_factor = self._normalize_score(
                raw_scores.momentum_total,
                max_possible_scores.momentum
            )
            
            # Step 7: Calculate final weighted score
            overall_score = (
                coverage_factor * config.FINAL_SCORE_WEIGHTS["coverage"] +
                accuracy_factor * config.FINAL_SCORE_WEIGHTS["accuracy"] +
                momentum_factor * config.FINAL_SCORE_WEIGHTS["momentum"]
            ) * 100  # Convert to 0-100 scale
            
            # Step 8: Identify weak flashcards
            weak_flashcards = self._identify_weak_flashcards(flashcard_performances)
            
            # Step 9: Create readiness document
            readiness = UserExamReadiness(
                user_id=user_id,
                exam_id=exam_id,
                course_id=course_id,
                overall_readiness_score=round(overall_score, 2),
                coverage_factor=round(coverage_factor, 4),
                accuracy_factor=round(accuracy_factor, 4),
                momentum_factor=round(momentum_factor, 4),
                raw_scores=raw_scores,
                max_possible_scores=max_possible_scores,
                weak_flashcards=weak_flashcards,
                total_flashcards_in_exam=len(flashcard_ids),
                flashcards_attempted=len(flashcard_performances),
                last_calculated=datetime.now(timezone.utc)
            )
            
            # Step 10: Persist to database
            await self.quiz_repository.save_exam_readiness(
                user_id=user_id,
                exam_id=exam_id,
                course_id=course_id,
                overall_readiness_score=readiness.overall_readiness_score,
                coverage_factor=readiness.coverage_factor,
                accuracy_factor=readiness.accuracy_factor,
                momentum_factor=readiness.momentum_factor,
                raw_scores=raw_scores.model_dump(),
                max_possible_scores=max_possible_scores.model_dump(),
                weak_flashcards=[wf.model_dump() for wf in weak_flashcards],
                total_flashcards_in_exam=readiness.total_flashcards_in_exam,
                flashcards_attempted=readiness.flashcards_attempted
            )
            
            logger.info(f"Calculated exam readiness for user {user_id}, exam {exam_id}: "
                       f"{readiness.overall_readiness_score:.1f}% "
                       f"(C:{coverage_factor:.2f}, A:{accuracy_factor:.2f}, M:{momentum_factor:.2f})")
            
            return readiness
            
        except Exception as e:
            logger.error(f"Error calculating exam readiness: {e}", exc_info=True)
            raise
    
    async def get_exams_containing_lecture(
        self,
        course_id: str,
        lecture_id: str
    ) -> List[Dict[str, str]]:
        """
        Find all exams that include a specific lecture.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            List of dicts with exam_id and exam_name for matching exams
        """
        return await self.quiz_repository.get_exams_containing_lecture(course_id, lecture_id)
    
    async def _fetch_exam_flashcard_ids(
        self,
        course_id: str,
        exam_lectures: List[str]
    ) -> List[str]:
        """
        Load all flashcard IDs for the given lectures from PostgreSQL.
        
        Args:
            course_id: Course identifier
            exam_lectures: List of lecture IDs (can be string or int)
            
        Returns:
            List of flashcard IDs
        """
        flashcard_ids = []
        
        from app.repositories.content_repository import ContentRepository
        content_repo = ContentRepository(self.pool)
        
        for lecture_id in exam_lectures:
            try:
                # Try to parse lecture_id as int for DB lookup
                lecture_id_int = int(lecture_id) if isinstance(lecture_id, str) else lecture_id
                lecture = await content_repo.get_lecture_by_id(lecture_id_int)
                
                if not lecture:
                    logger.warning(f"Lecture {lecture_id} not found in database")
                    continue
                
                flashcards_data = lecture.get('flashcards')
                if not flashcards_data:
                    logger.debug(f"No flashcards found for lecture {lecture_id}")
                    continue
                
                # Parse JSONB if needed
                if isinstance(flashcards_data, str):
                    flashcards_data = json.loads(flashcards_data)
                
                # Handle both formats: {"flashcards": [...]} or direct list
                if isinstance(flashcards_data, dict):
                    flashcards = flashcards_data.get("flashcards", [])
                elif isinstance(flashcards_data, list):
                    flashcards = flashcards_data
                else:
                    flashcards = []
                
                for flashcard in flashcards:
                    fc_id = flashcard.get("flashcard_id") or flashcard.get("id")
                    if fc_id:
                        flashcard_ids.append(fc_id)
                        
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid lecture ID format: {lecture_id} - {e}")
            except Exception as e:
                logger.error(f"Error loading flashcards for lecture {lecture_id}: {e}")
        
        logger.info(f"Loaded {len(flashcard_ids)} flashcard IDs from {len(exam_lectures)} lectures")
        return flashcard_ids
    
    async def _fetch_user_flashcard_performances(
        self,
        user_id: str,
        flashcard_ids: List[str]
    ) -> List[UserFlashcardPerformance]:
        """Fetch all flashcard performance documents for the user from PostgreSQL."""
        performances = []
        
        for flashcard_id in flashcard_ids:
            perf_data = await self.analytics_repository.get_flashcard_performance(
                user_id, flashcard_id
            )
            
            if perf_data:
                performances.append(self._dict_to_performance_model(perf_data))
        
        return performances
    
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
    
    def _aggregate_scores(
        self,
        flashcard_performances: List[UserFlashcardPerformance]
    ) -> RawScores:
        """Aggregate scores from all flashcard performances."""
        coverage_total = 0.0
        accuracy_total = 0
        momentum_total = 0.0
        
        for perf in flashcard_performances:
            coverage_total += perf.coverage_score
            accuracy_total += perf.accuracy_score
            momentum_total += perf.momentum_score
        
        return RawScores(
            coverage_total=coverage_total,
            accuracy_total=accuracy_total,
            momentum_total=momentum_total
        )
    
    def _calculate_max_possible_scores(
        self,
        total_flashcards: int
    ) -> MaxPossibleScores:
        """
        Calculate maximum possible scores for normalization.
        
        Args:
            total_flashcards: Total number of flashcards in the exam
            
        Returns:
            MaxPossibleScores with max values for each pillar
        """
        # Coverage: each flashcard can contribute up to MAX_COVERAGE_POINTS_PER_FLASHCARD
        max_coverage = total_flashcards * config.MAX_COVERAGE_POINTS_PER_FLASHCARD
        
        # Accuracy: based on estimated questions per flashcard
        max_accuracy_per_flashcard = sum(
            config.ESTIMATED_QUESTIONS_PER_FLASHCARD[level] * config.ACCURACY_POINTS[level]["correct"]
            for level in ["easy", "medium", "hard", "boss"]
        )
        max_accuracy = total_flashcards * max_accuracy_per_flashcard
        
        # Momentum: normalized to 1.0 per flashcard
        max_momentum = total_flashcards * 1.0
        
        return MaxPossibleScores(
            coverage=max_coverage,
            accuracy=max_accuracy,
            momentum=max_momentum
        )
    
    def _normalize_score(self, raw_score: float, max_score: float) -> float:
        """Normalize a raw score to 0-1 range."""
        if max_score == 0:
            return 0.0
        return max(0.0, min(1.0, raw_score / max_score))
    
    def _identify_weak_flashcards(
        self,
        flashcard_performances: List[UserFlashcardPerformance]
    ) -> List[WeakFlashcard]:
        """Identify and return weak flashcards."""
        weak_flashcards = []
        
        for perf in flashcard_performances:
            if perf.is_weak:
                weak_flashcards.append(WeakFlashcard(
                    flashcard_id=perf.flashcard_id,
                    accuracy_score=perf.accuracy_score
                ))
        
        # Sort by accuracy score (worst first)
        weak_flashcards.sort(key=lambda x: x.accuracy_score)
        
        return weak_flashcards
    
    def _create_empty_readiness(
        self,
        user_id: str,
        course_id: str,
        exam_id: str
    ) -> UserExamReadiness:
        """Create an empty readiness document for exams with no data."""
        return UserExamReadiness(
            user_id=user_id,
            exam_id=exam_id,
            course_id=course_id,
            overall_readiness_score=0.0,
            coverage_factor=0.0,
            accuracy_factor=0.0,
            momentum_factor=0.0,
            raw_scores=RawScores(coverage_total=0.0, accuracy_total=0, momentum_total=0.0),
            max_possible_scores=MaxPossibleScores(coverage=0.0, accuracy=0, momentum=0.0),
            weak_flashcards=[],
            total_flashcards_in_exam=0,
            flashcards_attempted=0,
            last_calculated=datetime.now(timezone.utc)
        )
    
    def select_feedback_message(
        self,
        coverage_factor: float,
        accuracy_factor: float,
        momentum_factor: float
    ) -> Tuple[str, str, str]:
        """
        Select appropriate feedback message based on weakest pillar.
        
        Args:
            coverage_factor: Coverage score (0-1)
            accuracy_factor: Accuracy score (0-1)
            momentum_factor: Momentum score (0-1)
            
        Returns:
            Tuple of (headline, message, action_type)
        """
        # Determine weakest pillar
        pillars = [
            ("coverage", coverage_factor, config.READINESS_DASHBOARD_FEEDBACK["weak_coverage"]),
            ("accuracy", accuracy_factor, config.READINESS_DASHBOARD_FEEDBACK["weak_accuracy"]),
            ("momentum", momentum_factor, config.READINESS_DASHBOARD_FEEDBACK["weak_momentum"])
        ]
        
        weakest_pillar, weakest_score, feedback_config = min(pillars, key=lambda x: x[1])
        
        # If all scores are good (>0.8), use maintenance message
        if weakest_score > 0.8:
            feedback_config = config.READINESS_DASHBOARD_FEEDBACK["maintenance"]
            action_type = "maintenance"
        else:
            action_type = weakest_pillar
        
        # Select a random message from the list
        headline = feedback_config["headline"]
        message = random.choice(feedback_config["messages"])
        
        return (headline, message, action_type)
    
    async def get_exam_readiness(
        self,
        user_id: str,
        exam_id: str
    ) -> Optional[UserExamReadiness]:
        """
        Get cached exam readiness score.
        
        Args:
            user_id: Firebase UID
            exam_id: Exam identifier
            
        Returns:
            UserExamReadiness document or None if not found
        """
        readiness_data = await self.quiz_repository.get_exam_readiness(user_id, exam_id)
        
        if readiness_data:
            return UserExamReadiness(
                user_id=readiness_data["user_id"],
                exam_id=readiness_data["exam_id"],
                course_id=readiness_data["course_id"],
                overall_readiness_score=readiness_data["overall_readiness_score"],
                coverage_factor=readiness_data["coverage_factor"],
                accuracy_factor=readiness_data["accuracy_factor"],
                momentum_factor=readiness_data["momentum_factor"],
                raw_scores=RawScores(**readiness_data.get("raw_scores", {})),
                max_possible_scores=MaxPossibleScores(**readiness_data.get("max_possible_scores", {})),
                weak_flashcards=[WeakFlashcard(**wf) for wf in readiness_data.get("weak_flashcards", [])],
                total_flashcards_in_exam=readiness_data["total_flashcards_in_exam"],
                flashcards_attempted=readiness_data["flashcards_attempted"],
                last_calculated=readiness_data["last_calculated"]
            )
        return None
    
    async def calculate_deck_readiness(
        self,
        user_id: str,
        course_id: str,
        deck_ids: List[str]
    ) -> UserExamReadiness:
        """
        Calculate readiness score for one or more decks (for Mix Mode).
        
        This method reuses the exam readiness calculation logic but operates
        on deck_ids instead of exam_id. The result is returned as UserExamReadiness
        with exam_id set to a deck-specific identifier.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            deck_ids: List of deck/lecture IDs
            
        Returns:
            UserExamReadiness document with deck-based scores
        """
        try:
            # Generate a unique exam_id for this deck combination
            sorted_deck_ids = sorted(deck_ids)
            deck_exam_id = f"deck_{'_'.join(sorted_deck_ids)}"
            
            # Load all flashcard IDs for the decks (reuse exam method, it accepts lecture list)
            flashcard_ids = await self._fetch_exam_flashcard_ids(course_id, deck_ids)
            
            if not flashcard_ids:
                logger.warning(f"No flashcards found for decks {deck_ids}")
                return self._create_empty_readiness(user_id, course_id, deck_exam_id)
            
            # Fetch all user flashcard performance documents
            flashcard_performances = await self._fetch_user_flashcard_performances(
                user_id, flashcard_ids
            )
            
            # Aggregate scores
            raw_scores = self._aggregate_scores(flashcard_performances)
            
            # Calculate max possible scores
            max_possible_scores = self._calculate_max_possible_scores(len(flashcard_ids))
            
            # Normalize to factors (0-1)
            coverage_factor = self._normalize_score(
                raw_scores.coverage_total,
                max_possible_scores.coverage
            )
            accuracy_factor = self._normalize_score(
                raw_scores.accuracy_total,
                max_possible_scores.accuracy
            )
            momentum_factor = self._normalize_score(
                raw_scores.momentum_total,
                max_possible_scores.momentum
            )
            
            # Calculate final weighted score
            overall_score = (
                coverage_factor * config.FINAL_SCORE_WEIGHTS["coverage"] +
                accuracy_factor * config.FINAL_SCORE_WEIGHTS["accuracy"] +
                momentum_factor * config.FINAL_SCORE_WEIGHTS["momentum"]
            ) * 100  # Convert to 0-100 scale
            
            # Identify weak flashcards
            weak_flashcards = self._identify_weak_flashcards(flashcard_performances)
            
            # Create readiness document
            readiness = UserExamReadiness(
                user_id=user_id,
                exam_id=deck_exam_id,
                course_id=course_id,
                overall_readiness_score=round(overall_score, 2),
                coverage_factor=round(coverage_factor, 4),
                accuracy_factor=round(accuracy_factor, 4),
                momentum_factor=round(momentum_factor, 4),
                raw_scores=raw_scores,
                max_possible_scores=max_possible_scores,
                weak_flashcards=weak_flashcards,
                total_flashcards_in_exam=len(flashcard_ids),
                flashcards_attempted=len(flashcard_performances),
                last_calculated=datetime.now(timezone.utc)
            )
            
            logger.info(f"Calculated deck readiness for user {user_id}, decks {deck_ids}: "
                       f"{readiness.overall_readiness_score:.1f}% "
                       f"(C:{coverage_factor:.2f}, A:{accuracy_factor:.2f}, M:{momentum_factor:.2f})")
            
            return readiness
            
        except Exception as e:
            logger.error(f"Error calculating deck readiness: {e}", exc_info=True)
            raise
    
    async def get_or_calculate_deck_readiness(
        self,
        user_id: str,
        course_id: str,
        deck_ids: List[str],
        force_refresh: bool = False
    ) -> UserExamReadiness:
        """
        Get deck readiness from cache or calculate if needed.
        
        This method implements a 30-second in-memory cache to optimize
        real-time updates during Mix Mode sessions.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            deck_ids: List of deck/lecture IDs
            force_refresh: If True, bypass cache and recalculate
            
        Returns:
            UserExamReadiness document with deck-based scores
        """
        # Generate cache key
        sorted_deck_ids = sorted(deck_ids)
        cache_key = f"deck_readiness:{user_id}:{'_'.join(sorted_deck_ids)}"
        
        # Check cache if not forcing refresh
        if not force_refresh and cache_key in self._readiness_cache:
            cached_readiness, cached_time = self._readiness_cache[cache_key]
            age = datetime.now(timezone.utc) - cached_time
            
            if age < self._cache_ttl:
                logger.debug(f"Cache hit for {cache_key} (age: {age.total_seconds():.1f}s)")
                return cached_readiness
            else:
                logger.debug(f"Cache expired for {cache_key} (age: {age.total_seconds():.1f}s)")
        
        # Calculate fresh readiness
        readiness = await self.calculate_deck_readiness(user_id, course_id, deck_ids)
        
        # Update cache
        self._readiness_cache[cache_key] = (readiness, datetime.now(timezone.utc))
        
        return readiness
    
    @classmethod
    def invalidate_deck_cache(cls, user_id: str, deck_ids: List[str]):
        """
        Invalidate cached deck readiness for a user.
        
        This should be called after quiz completion to ensure fresh scores.
        
        Args:
            user_id: Firebase UID
            deck_ids: List of deck/lecture IDs to invalidate
        """
        sorted_deck_ids = sorted(deck_ids)
        cache_key = f"deck_readiness:{user_id}:{'_'.join(sorted_deck_ids)}"
        
        if cache_key in cls._readiness_cache:
            del cls._readiness_cache[cache_key]
            logger.debug(f"Invalidated cache for {cache_key}")


async def get_readiness_v2_service() -> ReadinessV2Service:
    """Dependency injection helper with PostgreSQL pool."""
    from app.db.postgres import get_postgres_pool
    pool = await get_postgres_pool()
    return ReadinessV2Service(pool)
