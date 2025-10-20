"""Quiz result tracking models."""

from datetime import datetime, timezone
from typing import List, Optional, Any
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

class QuestionResult(BaseModel):
    """Individual question result."""
    
    question_number: int
    question : Any
    question_type: str  # mcq, sequencing, categorization, etc.
    user_answer: Any  # Can be string, list, dict depending on question type
    correct_answer: Any
    is_correct: bool
    time_taken: Optional[int] = None  # seconds

class QuizResult(BaseModel):
    """Quiz result document model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., description="UUID v4 string for user identification")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_1-3")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    score: int = Field(..., ge=0, description="Number of correct answers")
    total_questions: int = Field(..., ge=1, description="Total number of questions")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage score")
    time_taken: int = Field(..., ge=0, description="Total time in seconds")
    question_results: List[QuestionResult] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class QuizSubmission(BaseModel):
    """Quiz submission request model."""
    
    deck_id: str = Field(..., description="Deck identifier")
    course_id: str = Field(..., description="Course identifier")
    score: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=1)
    time_taken: int = Field(..., ge=0, description="Total time in seconds")
    question_results: Optional[List[QuestionResult]] = Field(default_factory=list)

class QuizResultResponse(BaseModel):
    """Quiz result response model."""
    
    user_id: str
    deck_id: str
    course_id: str
    score: int
    total_questions: int
    percentage: float
    time_taken: int
    completed_at: datetime
