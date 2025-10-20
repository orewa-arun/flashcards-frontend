"""Deck progress tracking models."""

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

class DeckProgress(BaseModel):
    """Deck progress document model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
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
