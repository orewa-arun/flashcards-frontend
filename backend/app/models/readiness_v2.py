"""
Data models for Exam Readiness Engine V2.

This module defines the persistent, flashcard-centric performance tracking models.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PerformanceByLevel(BaseModel):
    """Performance metrics for a specific difficulty level."""
    attempts: int = 0
    correct: int = 0
    points: float = Field(default=0.0, description="Total points earned at this level (supports partial credit)")


class RecentAttempt(BaseModel):
    """A single recent quiz attempt for momentum calculation."""
    timestamp: datetime
    level: str  # easy, medium, hard, boss
    is_correct: bool
    points_earned: float = Field(default=0.0, description="Points earned for this attempt (can be negative, supports partial credit). Defaults to 0.0 for backward compatibility.")


class UserFlashcardPerformance(BaseModel):
    """
    Granular performance tracking for a single user on a single flashcard.
    
    This is the source of truth for all performance data. One document exists
    for every (user, flashcard) pair that has been quizzed.
    """
    user_id: str = Field(..., description="Firebase UID")
    flashcard_id: str = Field(..., description="Unique flashcard identifier (e.g., SI_lec_1_15)")
    course_id: str = Field(..., description="Course identifier (e.g., MS5150)")
    lecture_id: str = Field(..., description="Lecture identifier (e.g., SI_lec_1)")
    
    # Raw performance data
    performance_by_level: Dict[str, PerformanceByLevel] = Field(
        default_factory=lambda: {
            "easy": PerformanceByLevel(points=0.0),
            "medium": PerformanceByLevel(points=0.0),
            "hard": PerformanceByLevel(points=0.0),
            "boss": PerformanceByLevel(points=0.0)
        },
        description="Performance broken down by difficulty level"
    )
    
    recent_attempts: List[RecentAttempt] = Field(
        default_factory=list,
        description="Capped list of recent attempts for momentum calculation"
    )
    
    # Pre-calculated scores for this flashcard
    coverage_score: float = Field(default=0.0, description="Coverage points earned (capped at 2)")
    accuracy_score: float = Field(default=0.0, description="Cumulative accuracy points (can be negative, supports partial credit)")
    momentum_score: float = Field(default=0.0, description="Time-weighted accuracy score (0-1)")
    total_points_earned: float = Field(default=0.0, description="Total points earned across all attempts (same as accuracy_score, stored for clarity)")
    comfortability_score: float = Field(default=0.0, description="Comfortability score based on recent performance")
    question_next_level: str = Field(default="easy", description="Recommended next question difficulty level (easy, medium, hard, boss)")
    
    # State tracking
    is_weak: bool = Field(default=False, description="Whether this flashcard is currently marked as weak")
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-firebase-uid-123",
                "flashcard_id": "SI_lec_1_15",
                "course_id": "MS5150",
                "lecture_id": "SI_lec_1",
                "performance_by_level": {
                    "easy": {"attempts": 5, "correct": 4},
                    "medium": {"attempts": 3, "correct": 3},
                    "hard": {"attempts": 2, "correct": 1},
                    "boss": {"attempts": 1, "correct": 0}
                },
                "coverage_score": 2.0,
                "accuracy_score": 9.5,
                "momentum_score": 0.85,
                "total_points_earned": 9.5,
                "comfortability_score": 3.2,
                "question_next_level": "hard",
                "is_weak": True,
                "recent_attempts": [
                    {
                        "timestamp": "2024-01-15T10:30:00Z",
                        "level": "hard",
                        "is_correct": True,
                        "points_earned": 3.0
                    },
                    {
                        "timestamp": "2024-01-15T10:35:00Z",
                        "level": "hard",
                        "is_correct": False,
                        "points_earned": -1.0
                    }
                ]
            }
        }


class WeakFlashcard(BaseModel):
    """Summary of a weak flashcard for UI display."""
    flashcard_id: str
    accuracy_score: float


class RawScores(BaseModel):
    """Raw aggregated scores before normalization."""
    coverage_total: float = Field(..., description="Sum of all coverage_score values")
    accuracy_total: float = Field(..., description="Sum of all accuracy_score values")
    momentum_total: float = Field(..., description="Sum of all momentum_score values")


class MaxPossibleScores(BaseModel):
    """Maximum possible scores for normalization."""
    coverage: float = Field(..., description="Max possible coverage points")
    accuracy: int = Field(..., description="Max possible accuracy points (always whole number)")
    momentum: float = Field(..., description="Max possible momentum score")


class UserExamReadiness(BaseModel):
    """
    Aggregated exam readiness score for a specific user and exam.
    
    This document is pre-calculated and cached for fast retrieval.
    It aggregates data from multiple UserFlashcardPerformance documents.
    """
    user_id: str = Field(..., description="Firebase UID")
    exam_id: str = Field(..., description="Exam identifier from timetable")
    course_id: str = Field(..., description="Course identifier")
    
    # Final scores
    overall_readiness_score: float = Field(..., ge=0, le=100, description="Final weighted score (0-100)")
    coverage_factor: float = Field(..., ge=0, le=1, description="Normalized coverage score (0-1)")
    accuracy_factor: float = Field(..., ge=0, le=1, description="Normalized accuracy score (0-1)")
    momentum_factor: float = Field(..., ge=0, le=1, description="Normalized momentum score (0-1)")
    
    # Raw data for transparency
    raw_scores: RawScores
    max_possible_scores: MaxPossibleScores
    
    # Actionable metadata
    weak_flashcards: List[WeakFlashcard] = Field(default_factory=list)
    total_flashcards_in_exam: int = Field(..., description="Total flashcards covered by this exam")
    flashcards_attempted: int = Field(..., description="Number of flashcards user has been quizzed on")
    
    last_calculated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user-firebase-uid-123",
                "exam_id": "midterm_exam_1",
                "course_id": "MS5150",
                "overall_readiness_score": 75.4,
                "coverage_factor": 0.9,
                "accuracy_factor": 0.72,
                "momentum_factor": 0.65,
                "raw_scores": {
                    "coverage_total": 45.0,
                    "accuracy_total": 207.5,
                    "momentum_total": 13.0
                },
                "max_possible_scores": {
                    "coverage": 50.0,
                    "accuracy": 287,
                    "momentum": 20.0
                },
                "weak_flashcards": [
                    {"flashcard_id": "SI_lec_1_15", "accuracy_score": -1}
                ],
                "total_flashcards_in_exam": 25,
                "flashcards_attempted": 23
            }
        }

