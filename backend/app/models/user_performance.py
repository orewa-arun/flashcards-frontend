"""User performance tracking models for adaptive quiz engine."""

from datetime import datetime
from typing import Dict, Optional, Union, List
from pydantic import BaseModel, Field


class FlashcardPerformance(BaseModel):
    """Performance metrics for a specific flashcard."""
    correct: int = 0
    incorrect: int = 0
    last_attempted: Optional[datetime] = None


class QuestionPerformance(BaseModel):
    """Performance metrics for a specific question."""
    correct: int = 0
    incorrect: int = 0


class UserPerformanceDocument(BaseModel):
    """MongoDB document for tracking user performance in a lecture."""
    user_id: str
    course_id: str
    lecture_id: str
    flashcards: Dict[str, FlashcardPerformance] = Field(default_factory=dict)
    questions: Dict[str, QuestionPerformance] = Field(default_factory=dict)


class QuizSessionRequest(BaseModel):
    """Request model for starting a quiz session."""
    course_id: str
    lecture_id: str
    level: int  # 1-4
    size: int = 20  # Number of questions


class QuizAnswerSubmission(BaseModel):
    """Model for submitting a quiz answer."""
    course_id: str
    lecture_id: str
    question_hash: str
    flashcard_id: str
    is_correct: bool
    level: int
    question_text: Optional[str] = None  # For snapshot storage
    options: Optional[Dict[str, str]] = None  # For snapshot storage


class QuestionResult(BaseModel):
    """Model for a single question result in the quiz session."""
    question_text: str
    user_answer: Union[str, List[str]]  # String for MCQ, array for MCA
    correct_answer: Union[str, List[str]]  # String for MCQ, array for MCA
    is_correct: bool
    explanation: str
    source_flashcard_id: Optional[str] = None


class QuizSessionCompletion(BaseModel):
    """Model for completing a quiz session and saving to history."""
    course_id: str
    lecture_id: str
    level: int
    score: int
    total_questions: int
    time_taken_seconds: int
    question_results: list[QuestionResult]


