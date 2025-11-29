"""Flashcard feedback model for like/dislike tracking.

NOTE:
- Legacy versions of this model used MongoDB's ObjectId (`bson.ObjectId`)
  for the `_id` field.
- The current analytics backend uses PostgreSQL only, and all feedback
  persistence is handled via `BookmarkFeedbackRepository` and JSON/ints.
- We keep an optional `id` field (aliased to `_id`) as a simple string
  for backwards compatibility with any old JSON documents, but we no
  longer depend on `bson` or MongoDB.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class FlashcardFeedback(BaseModel):
    """Flashcard feedback document model."""
    
    # Optional document identifier, kept as string for backwards compatibility
    # with any legacy JSON that included a Mongo-style `_id`.
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="UUID v4 string for user identification")
    session_id: str = Field(..., description="Study session identifier")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_1-3")
    flashcard_index: int = Field(..., ge=0, description="0-based index of flashcard in deck")
    rating: int = Field(..., description="1 for like, -1 for dislike")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")
    flashcard_index: int = Field(..., ge=0, description="Flashcard index in deck")
    session_id: str = Field(..., description="Current study session ID")
    rating: int = Field(..., description="1 for like, -1 for dislike")

class FeedbackResponse(BaseModel):
    """Response model for feedback operations."""
    
    user_id: str
    course_id: str
    deck_id: str
    flashcard_index: int
    session_id: str
    rating: int
    created_at: datetime

class UserFeedbackSummary(BaseModel):
    """Summary of a user's feedback for UI state management."""
    
    course_id: str
    deck_id: str
    flashcard_index: int
    rating: int
