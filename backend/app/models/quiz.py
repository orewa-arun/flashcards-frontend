"""Quiz result tracking models.

Originally, quiz results were stored in MongoDB and used `ObjectId`
for `_id`. In the current architecture, results live in PostgreSQL
(`quiz_results` table). We keep an optional string `id` aliasing `_id`
for any old JSON payloads, but remove all `bson`/MongoDB dependencies.
"""

from datetime import datetime, timezone
from typing import List, Optional, Any
from pydantic import BaseModel, Field

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
    
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="UUID v4 string for user identification")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_1-3")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    difficulty: str = Field(default="medium", description="Quiz difficulty: medium or hard")
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
    difficulty: str
    score: int
    total_questions: int
    percentage: float
    time_taken: int
    completed_at: datetime
