"""
Service for calculating and persisting exam readiness scores.

This service aggregates flashcard-level performance data to compute
the overall exam readiness score with three pillars: Coverage, Accuracy, and Momentum.
"""

import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.readiness_v2 import (
    UserExamReadiness,
    UserFlashcardPerformance,
    WeakFlashcard,
    RawScores,
    MaxPossibleScores
)
from app import readiness_config as config

logger = logging.getLogger(__name__)


class ReadinessV2Service:
    """
    Service for calculating and persisting exam readiness scores.
    
    This service aggregates data from user_flashcard_performance documents
    to compute the final exam readiness score.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.flashcard_perf_collection = database.user_flashcard_performance
        self.exam_readiness_collection = database.user_exam_readiness
        self.timetable_collection = database.course_timetables
    
    async def initialize_indexes(self):
        """Create indexes for efficient querying."""
        await self.exam_readiness_collection.create_index(
            [("user_id", 1), ("exam_id", 1)],
            unique=True
        )
        logger.info("Exam readiness indexes created")
    
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
            exam_lectures = await self._get_exam_lectures(course_id, exam_id)
            
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
            await self.exam_readiness_collection.update_one(
                {"user_id": user_id, "exam_id": exam_id},
                {"$set": readiness.model_dump()},
                upsert=True
            )
            
            logger.info(f"✅ Calculated exam readiness for user {user_id}, exam {exam_id}: "
                       f"{readiness.overall_readiness_score:.1f}% "
                       f"(C:{coverage_factor:.2f}, A:{accuracy_factor:.2f}, M:{momentum_factor:.2f})")
            
            return readiness
            
        except Exception as e:
            logger.error(f"Error calculating exam readiness: {e}", exc_info=True)
            raise
    
    async def _get_exam_lectures(self, course_id: str, exam_id: str) -> List[str]:
        """Get list of lecture IDs for an exam from the timetable."""
        timetable = await self.timetable_collection.find_one({"course_id": course_id})
        
        if not timetable:
            return []
        
        # Find the specific exam
        for exam in timetable.get("exams", []):
            if exam.get("exam_id") == exam_id:
                return exam.get("lectures", [])
        
        return []
    
    async def _fetch_exam_flashcard_ids(
        self,
        course_id: str,
        exam_lectures: List[str]
    ) -> List[str]:
        """
        Load all flashcard IDs for the given lectures from JSON files.
        
        Args:
            course_id: Course identifier
            exam_lectures: List of lecture IDs
            
        Returns:
            List of flashcard IDs
        """
        flashcard_ids = []
        
        # Base path to courses
        base_path = Path(__file__).parent.parent.parent / "courses"
        course_path = base_path / course_id / "cognitive_flashcards"
        
        for lecture_id in exam_lectures:
            lecture_folder = course_path / lecture_id
            flashcard_file = lecture_folder / f"{lecture_id}_cognitive_flashcards_only.json"
            
            if flashcard_file.exists():
                try:
                    with open(flashcard_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        flashcards = data.get("flashcards", []) if isinstance(data, dict) else data
                        
                        for flashcard in flashcards:
                            if "flashcard_id" in flashcard:
                                flashcard_ids.append(flashcard["flashcard_id"])
                except Exception as e:
                    logger.error(f"Error loading flashcards from {flashcard_file}: {e}")
        
        return flashcard_ids
    
    async def _fetch_user_flashcard_performances(
        self,
        user_id: str,
        flashcard_ids: List[str]
    ) -> List[UserFlashcardPerformance]:
        """Fetch all flashcard performance documents for the user."""
        cursor = self.flashcard_perf_collection.find({
            "user_id": user_id,
            "flashcard_id": {"$in": flashcard_ids}
        })
        
        perf_docs = await cursor.to_list(length=None)
        return [UserFlashcardPerformance(**doc) for doc in perf_docs]
    
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
        readiness_doc = await self.exam_readiness_collection.find_one({
            "user_id": user_id,
            "exam_id": exam_id
        })
        
        if readiness_doc:
            return UserExamReadiness(**readiness_doc)
        return None


def get_readiness_v2_service(db=None) -> ReadinessV2Service:
    """Dependency injection helper."""
    from app.database import get_database
    if db is None:
        db = get_database()
    return ReadinessV2Service(db)

