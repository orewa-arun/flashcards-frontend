"""
The Exam Readiness Engine - The Core Moat.

This service calculates the Trinity scores (Coverage, Mastery, Momentum)
and provides actionable recommendations for exam preparation.
"""
import math
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set, Optional
from pathlib import Path
from collections import defaultdict

from app.models.exam_readiness import (
    ExamReadinessScore,
    ReadinessBreakdown,
    PillarScore,
)
from motor.motor_asyncio import AsyncIOMotorDatabase


class ExamReadinessService:
    """
    The Engine.
    
    This class embodies the strategic intelligence layer of the platform.
    It transforms raw quiz attempt data into the Trinity scores.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        
        # Weighting for the final score
        self.COVERAGE_WEIGHT = 0.5
        self.MASTERY_WEIGHT = 0.3
        self.MOMENTUM_WEIGHT = 0.2
        
        # Level weights for mastery calculation
        self.LEVEL_WEIGHTS = {
            "easy": 1,
            "medium": 2,
            "hard": 3,
            "boss": 4,
        }
        
        # Exponential decay for momentum (half-life of 7 days)
        self.MOMENTUM_HALF_LIFE_DAYS = 7.0
    
    async def calculate_exam_readiness(
        self,
        user_id: str,
        course_id: str,
        exam_id: str,
        exam_lectures: List[str]
    ) -> ExamReadinessScore:
        """
        The main calculation engine.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            exam_id: Exam identifier
            exam_lectures: List of lecture IDs covered in this exam
        
        Returns:
            ExamReadinessScore with Trinity breakdown and recommendations
        """
        # Step 1: Load all flashcards for the exam's lectures
        flashcards_by_lecture = await self._load_flashcards_for_lectures(
            course_id, exam_lectures
        )
        
        # Step 2: Get all quiz attempts for this user and course
        attempts = await self._get_user_quiz_attempts(user_id, course_id)
        
        # Step 3: Calculate the Trinity
        coverage_score = await self._calculate_coverage(
            exam_lectures, flashcards_by_lecture, attempts
        )
        
        mastery_score = await self._calculate_mastery(
            exam_lectures, flashcards_by_lecture, attempts
        )
        
        momentum_score = await self._calculate_momentum(
            exam_lectures, flashcards_by_lecture, attempts
        )
        
        # Step 4: Calculate overall weighted score
        overall = (
            coverage_score.score * self.COVERAGE_WEIGHT +
            mastery_score.score * self.MASTERY_WEIGHT +
            momentum_score.score * self.MOMENTUM_WEIGHT
        )
        
        # Step 5: Generate recommendation
        recommendation, action_type = self._generate_recommendation(
            coverage_score, mastery_score, momentum_score
        )
        
        # Step 6: Determine urgency
        urgency_level = self._determine_urgency(overall)
        
        # Step 7: Extract metadata for UI
        covered_lectures, uncovered_lectures = self._get_coverage_metadata(
            exam_lectures, flashcards_by_lecture, attempts
        )
        
        weak_lectures = self._get_weak_lectures(
            exam_lectures, flashcards_by_lecture, attempts
        )
        
        return ExamReadinessScore(
            overall_score=round(overall, 2),
            breakdown=ReadinessBreakdown(
                coverage=coverage_score,
                mastery=mastery_score,
                momentum=momentum_score
            ),
            recommendation=recommendation,
            action_type=action_type,
            urgency_level=urgency_level,
            covered_lectures=covered_lectures,
            uncovered_lectures=uncovered_lectures,
            weak_lectures=weak_lectures
        )
    
    async def _load_flashcards_for_lectures(
        self,
        course_id: str,
        lecture_ids: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Load all flashcards for the given lectures.
        
        Returns:
            Dict mapping lecture_id -> list of flashcards with flashcard_id
        """
        flashcards_by_lecture = {}
        
        # Base path to courses
        base_path = Path("/Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai/courses")
        course_path = base_path / course_id / "cognitive_flashcards"
        
        for lecture_id in lecture_ids:
            # Find the flashcards_only.json file for this lecture
            lecture_folder = course_path / lecture_id
            flashcard_file = lecture_folder / f"{lecture_id}_cognitive_flashcards_only.json"
            
            if flashcard_file.exists():
                with open(flashcard_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extract the flashcards array from the JSON structure
                    flashcards = data.get("flashcards", []) if isinstance(data, dict) else data
                    flashcards_by_lecture[lecture_id] = flashcards
            else:
                flashcards_by_lecture[lecture_id] = []
        
        return flashcards_by_lecture
    
    async def _get_user_quiz_attempts(
        self,
        user_id: str,
        course_id: str
    ) -> List[Dict]:
        """Get all quiz attempts for this user and course."""
        collection = self.db["quiz_results"]
        cursor = collection.find({
            "firebase_uid": user_id,
            "course_id": course_id
        })
        return await cursor.to_list(length=None)
    
    async def _calculate_coverage(
        self,
        exam_lectures: List[str],
        flashcards_by_lecture: Dict[str, List[Dict]],
        attempts: List[Dict]
    ) -> PillarScore:
        """
        Pillar 1: Coverage Score.
        
        What percentage of flashcards from exam lectures have been quizzed on?
        """
        # Get all flashcard IDs from exam lectures
        all_flashcard_ids = set()
        for lecture_id in exam_lectures:
            for flashcard in flashcards_by_lecture.get(lecture_id, []):
                if "flashcard_id" in flashcard:
                    all_flashcard_ids.add(flashcard["flashcard_id"])
        
        if not all_flashcard_ids:
            return PillarScore(
                score=0.0,
                details="No flashcards found for exam lectures"
            )
        
        # Get all flashcard IDs the user has been quizzed on
        quizzed_flashcard_ids = set()
        for attempt in attempts:
            for question_attempt in attempt.get("question_results", []):
                source_id = question_attempt.get("source_flashcard_id")
                if source_id and source_id in all_flashcard_ids:
                    quizzed_flashcard_ids.add(source_id)
        
        coverage_percentage = (len(quizzed_flashcard_ids) / len(all_flashcard_ids)) * 100
        
        details = (
            f"You've been quizzed on {len(quizzed_flashcard_ids)} out of "
            f"{len(all_flashcard_ids)} concepts for this exam."
        )
        
        return PillarScore(
            score=round(coverage_percentage, 2),
            details=details
        )
    
    async def _calculate_mastery(
        self,
        exam_lectures: List[str],
        flashcards_by_lecture: Dict[str, List[Dict]],
        attempts: List[Dict]
    ) -> PillarScore:
        """
        Pillar 2: Mastery Score.
        
        Weighted accuracy score based on question difficulty levels.
        """
        # Get all flashcard IDs from exam lectures
        all_flashcard_ids = set()
        for lecture_id in exam_lectures:
            for flashcard in flashcards_by_lecture.get(lecture_id, []):
                if "flashcard_id" in flashcard:
                    all_flashcard_ids.add(flashcard["flashcard_id"])
        
        if not all_flashcard_ids:
            return PillarScore(
                score=0.0,
                details="No flashcards found for exam lectures"
            )
        
        # Calculate weighted points
        total_points = 0
        max_points = 0
        
        for attempt in attempts:
            # Extract difficulty level (e.g., "level_4" -> "boss")
            difficulty = attempt.get("difficulty", "medium")
            if difficulty.startswith("level_"):
                level_num = int(difficulty.split("_")[1])
                level_map = {1: "easy", 2: "medium", 3: "hard", 4: "boss"}
                level = level_map.get(level_num, "medium")
            else:
                level = difficulty.lower()
            
            level_weight = self.LEVEL_WEIGHTS.get(level, 2)
            
            for question_attempt in attempt.get("question_results", []):
                source_id = question_attempt.get("source_flashcard_id")
                if source_id and source_id in all_flashcard_ids:
                    max_points += level_weight
                    if question_attempt.get("is_correct", False):
                        total_points += level_weight
        
        if max_points == 0:
            return PillarScore(
                score=0.0,
                details="No quiz attempts found for exam concepts"
            )
        
        mastery_percentage = (total_points / max_points) * 100
        
        details = (
            f"You've earned {total_points} out of {max_points} weighted points "
            f"across all difficulty levels."
        )
        
        return PillarScore(
            score=round(mastery_percentage, 2),
            details=details
        )
    
    async def _calculate_momentum(
        self,
        exam_lectures: List[str],
        flashcards_by_lecture: Dict[str, List[Dict]],
        attempts: List[Dict]
    ) -> PillarScore:
        """
        Pillar 3: Momentum Score.
        
        Time-decayed accuracy score. Recent performance matters more.
        """
        # Get all flashcard IDs from exam lectures
        all_flashcard_ids = set()
        for lecture_id in exam_lectures:
            for flashcard in flashcards_by_lecture.get(lecture_id, []):
                if "flashcard_id" in flashcard:
                    all_flashcard_ids.add(flashcard["flashcard_id"])
        
        if not all_flashcard_ids:
            return PillarScore(
                score=0.0,
                details="No flashcards found for exam lectures"
            )
        
        now = datetime.now(timezone.utc)
        
        # Calculate time-weighted accuracy
        weighted_correct = 0.0
        weighted_total = 0.0
        
        for attempt in attempts:
            # Get completed_at timestamp (stored as ISO string in quiz_results)
            completed_at = attempt.get("completed_at")
            if not completed_at:
                continue
            
            # Parse ISO timestamp string to datetime
            if isinstance(completed_at, str):
                # Remove 'Z' if present and parse
                attempt_time = datetime.fromisoformat(completed_at.replace('Z', ''))
                # Make timezone-aware if it isn't already
                if attempt_time.tzinfo is None:
                    attempt_time = attempt_time.replace(tzinfo=timezone.utc)
            else:
                attempt_time = completed_at
                # Make timezone-aware if it isn't already
                if attempt_time.tzinfo is None:
                    attempt_time = attempt_time.replace(tzinfo=timezone.utc)
            
            # Calculate decay factor (exponential decay with 7-day half-life)
            age_days = (now - attempt_time).total_seconds() / 86400
            decay_factor = math.exp(-math.log(2) * age_days / self.MOMENTUM_HALF_LIFE_DAYS)
            
            for question_attempt in attempt.get("question_results", []):
                source_id = question_attempt.get("source_flashcard_id")
                if source_id and source_id in all_flashcard_ids:
                    weighted_total += decay_factor
                    if question_attempt.get("is_correct", False):
                        weighted_correct += decay_factor
        
        if weighted_total == 0:
            return PillarScore(
                score=0.0,
                details="No recent quiz attempts found for exam concepts"
            )
        
        momentum_percentage = (weighted_correct / weighted_total) * 100
        
        details = (
            f"Your recent performance shows {round(momentum_percentage, 1)}% accuracy, "
            f"with recent attempts weighted more heavily."
        )
        
        return PillarScore(
            score=round(momentum_percentage, 2),
            details=details
        )
    
    def _generate_recommendation(
        self,
        coverage: PillarScore,
        mastery: PillarScore,
        momentum: PillarScore
    ) -> tuple[str, str]:
        """
        Generate actionable recommendation based on the weakest pillar.
        
        Returns:
            (recommendation_text, action_type)
        """
        # Find the weakest pillar
        pillars = [
            ("coverage", coverage.score, "You have uncovered lectures. Focus on these first to build a strong foundation."),
            ("mastery", mastery.score, "Your accuracy needs improvement. Let's reinforce the concepts you're struggling with."),
            ("momentum", momentum.score, "Your performance has dipped recently. Let's do a quick review to sharpen your skills.")
        ]
        
        weakest_pillar, weakest_score, weakest_message = min(pillars, key=lambda x: x[1])
        
        # If all scores are good (>80), give encouragement
        if weakest_score > 80:
            return (
                "You're in great shape! Keep practicing to maintain your momentum.",
                "maintenance"
            )
        
        return (weakest_message, weakest_pillar)
    
    def _determine_urgency(self, overall_score: float) -> str:
        """Determine urgency level based on overall score."""
        if overall_score >= 75:
            return "low"
        elif overall_score >= 50:
            return "medium"
        else:
            return "high"
    
    def _get_coverage_metadata(
        self,
        exam_lectures: List[str],
        flashcards_by_lecture: Dict[str, List[Dict]],
        attempts: List[Dict]
    ) -> tuple[List[str], List[str]]:
        """
        Get lists of covered and uncovered lecture IDs.
        
        Returns:
            (covered_lectures, uncovered_lectures)
        """
        # Get flashcard IDs by lecture
        flashcard_to_lecture = {}
        for lecture_id in exam_lectures:
            for flashcard in flashcards_by_lecture.get(lecture_id, []):
                if "flashcard_id" in flashcard:
                    flashcard_to_lecture[flashcard["flashcard_id"]] = lecture_id
        
        # Track which lectures have been quizzed
        quizzed_lectures = set()
        for attempt in attempts:
            for question_attempt in attempt.get("question_results", []):
                source_id = question_attempt.get("source_flashcard_id")
                if source_id and source_id in flashcard_to_lecture:
                    quizzed_lectures.add(flashcard_to_lecture[source_id])
        
        covered = list(quizzed_lectures)
        uncovered = [lec for lec in exam_lectures if lec not in quizzed_lectures]
        
        return (covered, uncovered)
    
    def _get_weak_lectures(
        self,
        exam_lectures: List[str],
        flashcards_by_lecture: Dict[str, List[Dict]],
        attempts: List[Dict]
    ) -> List[str]:
        """
        Get list of lecture IDs where accuracy is below 60%.
        
        Returns:
            List of lecture IDs sorted by weakness (worst first)
        """
        # Get flashcard IDs by lecture
        flashcard_to_lecture = {}
        for lecture_id in exam_lectures:
            for flashcard in flashcards_by_lecture.get(lecture_id, []):
                if "flashcard_id" in flashcard:
                    flashcard_to_lecture[flashcard["flashcard_id"]] = lecture_id
        
        # Track accuracy by lecture
        lecture_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        
        for attempt in attempts:
            for question_attempt in attempt.get("question_results", []):
                source_id = question_attempt.get("source_flashcard_id")
                if source_id and source_id in flashcard_to_lecture:
                    lecture_id = flashcard_to_lecture[source_id]
                    lecture_stats[lecture_id]["total"] += 1
                    if question_attempt.get("is_correct", False):
                        lecture_stats[lecture_id]["correct"] += 1
        
        # Calculate accuracy and filter weak lectures
        weak_lectures = []
        for lecture_id, stats in lecture_stats.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                if accuracy < 0.6:  # Below 60%
                    weak_lectures.append((lecture_id, accuracy))
        
        # Sort by accuracy (worst first)
        weak_lectures.sort(key=lambda x: x[1])
        
        return [lecture_id for lecture_id, _ in weak_lectures]

