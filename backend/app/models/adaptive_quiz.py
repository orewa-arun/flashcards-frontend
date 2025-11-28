"""Models for adaptive quiz generation and concept-level performance tracking."""

from datetime import datetime, timezone
from typing import List, Optional, Any, Dict, Union, Literal
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


class FlashcardPerformance(BaseModel):
    """Performance tracking for a single flashcard within a deck."""
    
    flashcard_id: str = Field(..., description="Unique flashcard identifier (e.g., SI_lec_1_15)")
    times_attempted: int = Field(default=0, ge=0, description="Number of times questions from this flashcard were attempted")
    times_correct: int = Field(default=0, ge=0, description="Number of times answered correctly")
    times_incorrect: int = Field(default=0, ge=0, description="Number of times answered incorrectly")
    last_attempted: Optional[datetime] = Field(None, description="Last time this flashcard was quizzed")
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage for this flashcard."""
        if self.times_attempted == 0:
            return 0.0
        return (self.times_correct / self.times_attempted) * 100


class UserDeckPerformance(BaseModel):
    """Document model for tracking user's performance across all flashcards in a deck."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    firebase_uid: str = Field(..., description="Firebase UID for user identification")
    course_id: str = Field(..., description="Course identifier, e.g., MS5260")
    deck_id: str = Field(..., description="Deck identifier, e.g., MIS_lec_4")
    total_flashcards: int = Field(..., ge=1, description="Total number of flashcards in the deck")
    flashcards_performance: List[FlashcardPerformance] = Field(default_factory=list)
    total_quiz_attempts: int = Field(default=0, ge=0, description="Total number of quiz attempts for this deck")
    last_quiz_date: Optional[datetime] = Field(None, description="Last time user took a quiz on this deck")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ExplanationStep(BaseModel):
    """A single step in a step-by-step explanation."""
    
    step: int = Field(..., description="Step number")
    title: str = Field(..., description="Title of this step")
    content: str = Field(..., description="Explanation content for this step")
    latex: Optional[str] = Field(None, description="LaTeX formula or equation for this step")
    diagram: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Diagram code (Mermaid/Graphviz) or plot spec (matplotlib/plotly)")
    diagram_type: Optional[str] = Field(None, description="Type of diagram: mermaid, graphviz, matplotlib, plotly, image")
    diagram_image: Optional[str] = Field(None, description="Base64 encoded image or file path for rendered diagrams")


class EnhancedExplanation(BaseModel):
    """Rich, multi-modal explanation with diagrams and step-by-step breakdowns."""
    
    text: str = Field(..., description="Brief text explanation")
    step_by_step: Optional[List[ExplanationStep]] = Field(default_factory=list, description="Step-by-step breakdown")
    interpretation: Optional[str] = Field(None, description="Interpretation of the result")
    business_context: Optional[str] = Field(None, description="Business context or real-world application")
    diagrams: Optional[Dict[str, str]] = Field(default_factory=dict, description="Additional diagrams: diagram_type -> file_path or base64")


class NumericalAnswer(BaseModel):
    """Answer specification for numerical questions."""
    
    value: Union[float, List[float]] = Field(..., description="Single value or range [lower, upper]")
    tolerance: float = Field(0.01, description="Acceptable tolerance for numeric answers")
    units: Optional[str] = Field(None, description="Units for the answer (e.g., 'units', '%', 'dollars')")


class QuizGenerationRequest(BaseModel):
    """Request model for generating a new quiz."""
    
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")
    num_questions: Optional[int] = Field(20, ge=10, le=50, description="Number of questions to generate")
    difficulty: Optional[str] = Field("medium", description="Quiz difficulty: 'medium' or 'hard'")


class QuizQuestion(BaseModel):
    """A single quiz question with metadata."""
    
    question_id: str = Field(..., description="Unique identifier for this question instance")
    source_flashcard_id: str = Field(..., description="ID of the source flashcard (e.g., SI_lec_1_15)")
    question_type: str = Field(..., description="Type: mcq, mca, scenario_mcq, sequencing, categorization, matching, numerical")
    question: Any = Field(..., description="The question content")
    options: Optional[List[str]] = Field(None, description="Options for MCQ questions")
    items: Optional[List[Any]] = Field(None, description="Items for sequencing/categorization")
    categories: Optional[List[str]] = Field(None, description="Categories for categorization questions")
    scenario: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Scenario for scenario_mcq or numerical questions")
    premises: Optional[List[str]] = Field(None, description="Premises for matching questions")
    responses: Optional[List[str]] = Field(None, description="Responses for matching questions")
    correct_answer: Union[List[str], NumericalAnswer] = Field(..., description="The correct answer as an array (1 element for mcq, 2+ for mca) or NumericalAnswer for numerical questions")
    explanation: Optional[Union[str, EnhancedExplanation]] = Field(None, description="Explanation - can be simple string or enhanced explanation with diagrams")


class NumericalQuestion(BaseModel):
    """A numerical question requiring calculation."""
    
    type: Literal["numerical"] = Field("numerical", description="Question type identifier")
    question_text: str = Field(..., description="The question text")
    scenario: Optional[Dict[str, Any]] = Field(None, description="Scenario with context and given_data")
    answer: NumericalAnswer = Field(..., description="Answer specification with value, tolerance, and units")
    explanation: EnhancedExplanation = Field(..., description="Rich explanation with step-by-step solution")
    source_flashcard_id: str = Field(..., description="ID of the source flashcard")


class QuizGenerationResponse(BaseModel):
    """Response model for generated quiz."""
    
    quiz_id: str = Field(..., description="Unique identifier for this quiz session")
    course_id: str = Field(...)
    deck_id: str = Field(...)
    difficulty: str = Field(..., description="Quiz difficulty level")
    questions: List[QuizQuestion] = Field(..., description="List of quiz questions")
    total_questions: int = Field(..., description="Total number of questions in quiz")
    quiz_attempt_number: int = Field(..., description="Which attempt this is for the user on this deck")


class QuizAnswerSubmission(BaseModel):
    """User's answer to a single question."""
    
    question_id: str = Field(..., description="ID of the question being answered")
    user_answer: Any = Field(..., description="User's answer (can be string, list, dict)")


class QuizSubmissionRequest(BaseModel):
    """Request model for submitting completed quiz."""
    
    quiz_id: str = Field(..., description="The quiz session ID")
    course_id: str = Field(..., description="Course identifier")
    deck_id: str = Field(..., description="Deck identifier")
    difficulty: Optional[str] = Field("medium", description="Quiz difficulty level")
    answers: List[QuizAnswerSubmission] = Field(..., description="List of user answers")
    time_taken_seconds: int = Field(..., ge=0, description="Total time taken to complete quiz")


class QuestionResult(BaseModel):
    """Result for a single question."""
    
    question_id: str
    source_flashcard_id: str = Field(..., description="ID of the source flashcard")
    question_type: str
    question: Any = Field(..., description="The question text/content")
    options: Optional[List[str]] = Field(None, description="Options for MCQ questions")
    user_answer: Any
    correct_answer: Any
    is_correct: bool
    partial_credit_score: Optional[float] = Field(None, description="Partial credit score for MCA questions (0.0 to 1.0)")
    time_taken: Optional[int] = Field(None, description="Time taken to answer in seconds")


class FlashcardWeakness(BaseModel):
    """Summary of user's weakness in a flashcard."""
    
    flashcard_id: str
    times_attempted: int
    times_correct: int
    times_incorrect: int
    accuracy: float


class QuizSubmissionResponse(BaseModel):
    """Response model for quiz submission."""
    
    quiz_id: str
    firebase_uid: str
    course_id: str
    deck_id: str
    difficulty: str = Field(..., description="Quiz difficulty level")
    score: int = Field(..., description="Number of correct answers")
    total_questions: int
    percentage: float
    time_taken_seconds: int
    question_results: List[QuestionResult]
    weak_flashcards: List[FlashcardWeakness] = Field(..., description="Flashcards the user needs to review")
    completed_at: datetime
    quiz_attempt_number: int

