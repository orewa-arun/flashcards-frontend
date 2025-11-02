"""Bookmark model for flashcard bookmarking."""

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

class Bookmark(BaseModel):
    """Bookmark document model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
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
