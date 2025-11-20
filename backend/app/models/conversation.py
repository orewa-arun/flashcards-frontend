"""Conversation data models for AI Tutor chat management."""

from datetime import datetime, timezone
from typing import Optional, Any, List
from pydantic import BaseModel, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: Any
    ) -> JsonSchemaValue:
        return {"type": "string"}


class Message(BaseModel):
    """Individual message in a conversation."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: str = Field(..., description="ID of the conversation this message belongs to")
    role: str = Field(..., description="Message sender role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class Conversation(BaseModel):
    """Conversation metadata model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
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

