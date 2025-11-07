"""Data models for user profiles and enrollment."""

from typing import List
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile with enrolled courses."""
    user_id: str
    enrolled_courses: List[str] = Field(default_factory=list)


class EnrollmentResponse(BaseModel):
    """Response model for enrollment operations."""
    success: bool
    message: str
    enrolled_courses: List[str]










