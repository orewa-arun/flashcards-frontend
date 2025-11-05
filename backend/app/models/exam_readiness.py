"""
Pydantic models for Exam Readiness Score (The Trinity Engine).
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class PillarScore(BaseModel):
    """Individual pillar score with metadata."""
    score: float = Field(..., ge=0, le=100, description="Score from 0-100")
    details: str = Field(..., description="Human-readable explanation of the score")


class ReadinessBreakdown(BaseModel):
    """Detailed breakdown of the three readiness pillars."""
    coverage: PillarScore
    mastery: PillarScore
    momentum: PillarScore


class ExamReadinessScore(BaseModel):
    """
    The complete Exam Readiness Engine response.
    
    This is the core of our moat - the secret sauce that transforms
    raw quiz data into actionable strategic intelligence.
    """
    overall_score: float = Field(..., ge=0, le=100, description="Weighted average of the Trinity")
    breakdown: ReadinessBreakdown
    recommendation: str = Field(..., description="Actionable next step for the user")
    action_type: str = Field(..., description="Type of recommended action: 'coverage', 'mastery', or 'momentum'")
    
    # Metadata for UI rendering
    urgency_level: str = Field(..., description="'low', 'medium', or 'high' based on overall score")
    covered_lectures: List[str] = Field(default_factory=list, description="Lecture IDs user has been quizzed on")
    uncovered_lectures: List[str] = Field(default_factory=list, description="Lecture IDs user has not been quizzed on")
    weak_lectures: List[str] = Field(default_factory=list, description="Lecture IDs where mastery is low")


class ReadinessQueryParams(BaseModel):
    """Parameters for calculating exam readiness."""
    exam_id: str = Field(..., description="The exam identifier from the timetable")
    course_id: str = Field(..., description="The course this exam belongs to")

