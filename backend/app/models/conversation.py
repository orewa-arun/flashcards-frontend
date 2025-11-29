"""Conversation data models for AI Tutor chat management.

These models are used as Pydantic schemas for the conversation API.

MongoDB note:
- Earlier iterations used MongoDB with `bson.ObjectId` as `_id`.
- The current implementation stores conversations/messages in PostgreSQL
  (`conversations` and `messages` tables) via `ConversationService`.
- We keep an optional string `id` aliased to `_id` purely for
  compatibility with any old JSON; no `bson` dependency remains.
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Individual message in a conversation."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    conversation_id: str = Field(..., description="ID of the conversation this message belongs to")
    role: str = Field(..., description="Message sender role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class Conversation(BaseModel):
    """Conversation metadata model."""
    
    id: Optional[str] = Field(default=None, alias="_id")
    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="Firebase UID of the user")
    course_id: str = Field(..., description="Course identifier (e.g., MS5260)")
    lecture_id: str = Field(..., description="Lecture identifier (e.g., MIS_lec_1-3)")
    title: str = Field(default="New Chat", description="Conversation title")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = Field(default=0, description="Number of messages in conversation")
    notes: str = Field(default="", description="User-authored notes for this conversation")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ConversationSummary(BaseModel):
    """Conversation summary for list views."""
    
    conversation_id: str
    title: str
    course_id: str
    lecture_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationWithMessages(BaseModel):
    """Full conversation with all messages."""
    
    conversation_id: str
    title: str
    course_id: str
    lecture_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[dict]
    notes: str


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    
    course_id: str
    lecture_id: str


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    
    message: str
    conversation_id: str


class SendMessageResponse(BaseModel):
    """Response after sending a message."""
    
    conversation_id: str
    message_id: str
    answer: str

