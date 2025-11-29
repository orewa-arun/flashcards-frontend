"""Bookmark model for flashcard bookmarking.

Legacy note:
- This model previously used MongoDB's `ObjectId` for the `_id` field.
- The new v1.3 analytics backend stores bookmarks in PostgreSQL
  (`bookmarks` table) and does not use Mongo.
- We keep `id` as an optional string (alias `_id`) only so any old
  Mongo-shaped JSON remains deserializable.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Bookmark(BaseModel):
    """Bookmark document model."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    firebase_uid: str = Field(..., description="Firebase user ID")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_1-3")
    flashcard_index: int = Field(..., ge=0, description="0-based index of flashcard in deck")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class BookmarkRequest(BaseModel):
    """Request model for adding/removing bookmarks."""
    
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")
    flashcard_index: int = Field(..., ge=0, description="Flashcard index in deck")

class BookmarkResponse(BaseModel):
    """Response model for bookmark operations."""
    
    firebase_uid: str
    course_id: str
    deck_id: str
    flashcard_index: int
    created_at: datetime
    flashcard_data: Optional[dict] = Field(None, description="Full flashcard content from JSON")
