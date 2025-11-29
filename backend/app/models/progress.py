"""Deck progress tracking models.

These were originally shaped like MongoDB documents. Progress is now
tracked in PostgreSQL tables (e.g., `user_deck_progress`), but we keep
an optional string `id` for compatibility with any legacy JSON.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class DeckProgress(BaseModel):
    """Deck progress document model."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="UUID v4 string for user identification")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_1-3")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress as float 0.0 to 1.0")
    cards_studied: int = Field(default=0, ge=0)
    total_cards: int = Field(..., ge=1)
    last_studied: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    study_streak: int = Field(default=0, ge=0, description="Consecutive study days")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class ProgressUpdate(BaseModel):
    """Progress update request model."""
    
    deck_id: str = Field(..., description="Deck identifier")
    course_id: str = Field(..., description="Course identifier")
    progress: float = Field(..., ge=0.0, le=1.0)
    cards_studied: int = Field(..., ge=0)
    total_cards: int = Field(..., ge=1)

class ProgressResponse(BaseModel):
    """Progress response model."""
    
    user_id: str
    deck_id: str
    course_id: str
    progress: float
    cards_studied: int
    total_cards: int
    last_studied: datetime
    study_streak: int
