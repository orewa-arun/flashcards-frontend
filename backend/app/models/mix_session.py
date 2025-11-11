"""Models for Mix Mode adaptive study sessions."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class MixActivity(BaseModel):
    """A single activity in the mix session queue."""
    type: str = Field(..., description="Activity type: 'question' or 'flashcard'")
    flashcard_id: str = Field(..., description="The flashcard this activity relates to")
    level: str = Field(default="medium", description="Difficulty level for questions (easy, medium, hard, boss)")
    is_follow_up: bool = Field(default=False, description="Whether this is a follow-up remediation question")
    question_hash: Optional[str] = Field(None, description="Hash of the specific question to display (if pre-selected)")


class MixSession(BaseModel):
    """Session document for tracking an active mix mode study session."""
    session_id: str = Field(..., description="Unique identifier for this session")
    user_id: str = Field(..., description="Firebase UID of the user")
    course_id: str = Field(..., description="Course identifier (e.g., MS5150)")
    deck_ids: List[str] = Field(..., description="List of deck/lecture IDs included in this session")
    status: str = Field(default="in_progress", description="Session status: in_progress, completed, abandoned")
    
    # Master plan for the session
    flashcard_master_order: List[str] = Field(
        default_factory=list,
        description="Ordered list of flashcard IDs sorted by relevance_score"
    )
    
    # Dynamic activity queue
    activity_queue: List[MixActivity] = Field(
        default_factory=list,
        description="Queue of upcoming activities"
    )
    
    # Round tracking
    seen_in_current_round: List[str] = Field(
        default_factory=list,
        description="Flashcard IDs that have been presented in the current round"
    )
    current_round: int = Field(default=1, description="Current round number")
    
    # Question tracking to prevent repeats
    asked_question_hashes: List[str] = Field(
        default_factory=list,
        description="Hashes of questions already asked in this session"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "mix_session_123",
                "user_id": "user_firebase_uid",
                "course_id": "MS5150",
                "deck_ids": ["SI_lec_1", "SI_lec_2"],
                "status": "in_progress",
                "flashcard_master_order": ["SI_lec_1_15", "SI_lec_1_3", "SI_lec_2_8"],
                "current_round": 1
            }
        }


class UserQuestionPerformance(BaseModel):
    """Tracks the user's last performance on a specific question."""
    user_id: str = Field(..., description="Firebase UID")
    question_content_hash: str = Field(..., description="Hash of the question text")
    flashcard_id: str = Field(..., description="Source flashcard ID")
    level: str = Field(..., description="Question difficulty level")
    is_correct: bool = Field(..., description="Whether the user answered correctly on last attempt")
    last_attempted: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_firebase_uid",
                "question_content_hash": "abc123def456",
                "flashcard_id": "SI_lec_1_15",
                "level": "medium",
                "is_correct": True
            }
        }


class MixSessionStartRequest(BaseModel):
    """Request model for starting a new mix session."""
    course_id: str = Field(..., description="Course identifier")
    deck_ids: List[str] = Field(..., description="List of deck/lecture IDs to include")


class MixSessionStartResponse(BaseModel):
    """Response model for starting a new mix session."""
    session_id: str = Field(..., description="Unique session identifier")
    total_flashcards: int = Field(..., description="Total number of flashcards in the session")


class MixActivityResponse(BaseModel):
    """Response model for the next activity in the session."""
    activity_type: str = Field(..., description="Type: 'question' or 'flashcard'")
    flashcard_id: str = Field(..., description="The flashcard ID")
    
    # For question activities
    question: Optional[dict] = Field(None, description="The full question object if activity_type is 'question'")
    level: Optional[str] = Field(None, description="Question difficulty level")
    is_follow_up: Optional[bool] = Field(None, description="Whether this is a follow-up remediation question")
    
    # For flashcard activities
    flashcard_content: Optional[dict] = Field(None, description="The full flashcard content if activity_type is 'flashcard'")
    
    # Session progress
    round_number: int = Field(..., description="Current round number")
    progress: dict = Field(..., description="Progress information")


class MixAnswerSubmission(BaseModel):
    """Request model for submitting an answer in mix mode."""
    flashcard_id: str = Field(..., description="The flashcard ID this question belongs to")
    question_hash: str = Field(..., description="Hash of the question text")
    level: str = Field(..., description="Question difficulty level")
    user_answer: str | List[str] = Field(..., description="The user's answer")
    is_follow_up: bool = Field(default=False, description="Whether this was a follow-up question")


class MixAnswerResponse(BaseModel):
    """Response model for answer submission."""
    is_correct: bool = Field(..., description="Whether the answer was correct")
    correct_answer: str | List[str] = Field(..., description="The correct answer")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")
    points_earned: float = Field(..., description="Points earned for this answer")

