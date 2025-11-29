"""User data models for analytics tracking.

Legacy note:
- Earlier versions used MongoDB documents with `bson.ObjectId` as `_id`.
- The current analytics backend stores users in PostgreSQL (`users` table)
  and no longer depends on MongoDB.

We keep `id` as an optional string (alias `_id`) so that any legacy
Mongo-shaped JSON can still be deserialized, but we remove the `bson`
dependency entirely.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    """User document model."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    firebase_uid: str = Field(..., description="Firebase UID for user identification")
    email: Optional[str] = Field(None, description="User's email address")
    name: Optional[str] = Field(None, description="User's display name")
    picture: Optional[str] = Field(None, description="User's profile picture URL")
    email_verified: bool = Field(default=False, description="Whether email is verified")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_decks_studied: int = Field(default=0)
    total_quiz_attempts: int = Field(default=0)
    
    # Legacy field for backward compatibility (will be removed later)
    user_id: Optional[str] = Field(None, description="Legacy UUID v4 string (deprecated)")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class UserSummary(BaseModel):
    """User summary for API responses."""
    
    firebase_uid: str
    email: Optional[str]
    name: Optional[str]
    picture: Optional[str]
    total_decks_studied: int
    total_quiz_attempts: int
    created_at: datetime
    last_active: datetime

class UserCreate(BaseModel):
    """User creation model."""
    
    firebase_uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool = False
