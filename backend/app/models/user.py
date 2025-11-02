"""User data models for analytics tracking."""

from datetime import datetime, timezone
from typing import Optional, Any
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

class User(BaseModel):
    """User document model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
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
