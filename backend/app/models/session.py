"""Study session tracking models."""

from datetime import datetime, timezone
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId
from uuid import uuid4

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
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: Any
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())

class QuizData(BaseModel):
    """Quiz data within a study session."""
    
    quiz_duration_seconds: Optional[int] = Field(None, ge=0, description="Time taken to complete quiz in seconds")
    score: Optional[int] = Field(None, ge=0, description="Number of correct answers")
    total_questions: Optional[int] = Field(None, ge=1, description="Total number of questions in quiz")
    percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentage score")
    question_results: Optional[list] = Field(default_factory=list, description="Detailed per-question results")

class StudySession(BaseModel):
    """Study session document model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique session identifier")
    user_id: str = Field(..., description="UUID v4 string for user identification")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_1-3")
    
    session_start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    study_duration_seconds: Optional[int] = Field(None, ge=0, description="Time spent studying flashcards in seconds")
    
    quiz_data: QuizData = Field(default_factory=QuizData)
    
    is_completed: bool = Field(default=False, description="True when both study and quiz are complete")
    completed_at: Optional[datetime] = Field(None, description="When the session was completed")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class SessionStartRequest(BaseModel):
    """Request model for starting a new study session."""
    
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")

class SessionStartResponse(BaseModel):
    """Response model for session start."""
    
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(default="Session started successfully")

class SessionUpdateRequest(BaseModel):
    """Request model for updating a study session."""
    
    session_id: str = Field(..., description="Session identifier to update")
    study_duration_seconds: Optional[int] = Field(None, ge=0, description="Study duration in seconds")
    quiz_data: Optional[QuizData] = Field(None, description="Quiz completion data")
    is_completed: Optional[bool] = Field(None, description="Mark session as completed")

class SessionUpdateResponse(BaseModel):
    """Response model for session update."""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")
    study_duration_seconds: Optional[int] = Field(None)
    quiz_data: QuizData = Field(...)
    is_completed: bool = Field(...)
    total_session_time_seconds: Optional[int] = Field(None, description="Combined study + quiz time")
    message: str = Field(default="Session updated successfully")

class SessionSummaryResponse(BaseModel):
    """Complete session summary response."""
    
    session_id: str = Field(..., description="Session identifier") 
    user_id: str = Field(..., description="User identifier")
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")
    session_start_time: datetime = Field(..., description="When session started")
    study_duration_seconds: Optional[int] = Field(None, description="Study time in seconds")
    quiz_duration_seconds: Optional[int] = Field(None, description="Quiz time in seconds")
    total_session_time_seconds: Optional[int] = Field(None, description="Total session time")
    quiz_score: Optional[int] = Field(None, description="Quiz score")
    quiz_total_questions: Optional[int] = Field(None, description="Total quiz questions")
    quiz_percentage: Optional[float] = Field(None, description="Quiz percentage")
    is_completed: bool = Field(..., description="Session completion status")
    completed_at: Optional[datetime] = Field(None, description="When completed")
