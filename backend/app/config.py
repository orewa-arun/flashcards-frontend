"""Configuration settings for the FastAPI analytics backend."""

import os
import json
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _parse_questions_per_flashcard(env_value: str) -> Dict[str, int]:
    """Parse QUESTIONS_PER_FLASHCARD from JSON string."""
    default = {"easy": 2, "medium": 2, "hard": 2, "boss": 2}
    if not env_value:
        return default
    try:
        parsed = json.loads(env_value)
        # Validate structure
        for level in ["easy", "medium", "hard", "boss"]:
            if level not in parsed or not isinstance(parsed[level], int):
                return default
        return parsed
    except (json.JSONDecodeError, TypeError):
        return default


def _parse_chunk_size_by_level(env_value: str) -> Dict[str, int]:
    """Parse QUIZ_CHUNK_SIZE_BY_LEVEL from JSON string."""
    # Default: slightly smaller chunks for higher levels
    default = {"easy": 6, "medium": 4, "hard": 3, "boss": 2}
    if not env_value:
        return default
    try:
        parsed = json.loads(env_value)
        # Validate structure
        for level in ["easy", "medium", "hard", "boss"]:
            if level not in parsed or not isinstance(parsed[level], int):
                return default
        return parsed
    except (json.JSONDecodeError, TypeError):
        return default


class Settings:
    """Application settings."""
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "study_analytics")
    
    # PostgreSQL Configuration
    POSTGRES_URL: str = os.getenv(
        "POSTGRES_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/self_learning_ai"
    )
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:5173,http://localhost:3000"
    ).split(",")
    
    # RAG Backend Configuration
    RAG_API_BASE_URL: str = os.getenv("RAG_API_BASE_URL", "http://localhost:8001")
    
    # Cloudflare R2 Configuration
    CLOUDFLARE_R2_ACCESS_KEY_ID: str = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID", "")
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: str = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY", "")
    CLOUDFLARE_R2_ENDPOINT_URL: str = os.getenv("CLOUDFLARE_R2_ENDPOINT_URL", "")
    CLOUDFLARE_R2_BUCKET_NAME: str = os.getenv("CLOUDFLARE_R2_BUCKET_NAME", "course-content")
    
    # AI Model Configuration
    MODEL_ANALYSIS: str = os.getenv("MODEL_ANALYSIS", "gemini-2.0-flash-exp")
    MODEL_FLASHCARDS: str = os.getenv("MODEL_FLASHCARDS", "claude-3-haiku-20240307")
    MODEL_QUIZ: str = os.getenv("MODEL_QUIZ", "gemini-2.0-flash-exp")
    
    # AI API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Analysis Batching Configuration
    ANALYSIS_BATCH_SIZE: int = int(os.getenv("ANALYSIS_BATCH_SIZE", "5"))
    ANALYSIS_MAX_CONCURRENCY: int = int(os.getenv("ANALYSIS_MAX_CONCURRENCY", "3"))
    ANALYSIS_BATCH_DELAY_MS: int = int(os.getenv("ANALYSIS_BATCH_DELAY_MS", "500"))
    
    # Quiz Generation Configuration
    # QUESTIONS_PER_FLASHCARD: JSON mapping of level -> questions count
    # Example: '{"easy": 3, "medium": 2, "hard": 1, "boss": 1}'
    QUESTIONS_PER_FLASHCARD: Dict[str, int] = _parse_questions_per_flashcard(
        os.getenv("QUESTIONS_PER_FLASHCARD", "")
    )
    # Base chunk size for quiz generation (flashcards per API call)
    # Used as a fallback when per-level config is not provided
    QUIZ_CHUNK_SIZE: int = int(os.getenv("QUIZ_CHUNK_SIZE", "4"))
    # Optional per-level chunk size override so higher levels can start smaller
    # Example: '{"easy": 6, "medium": 4, "hard": 3, "boss": 2}'
    QUIZ_CHUNK_SIZE_BY_LEVEL: Dict[str, int] = _parse_chunk_size_by_level(
        os.getenv("QUIZ_CHUNK_SIZE_BY_LEVEL", "")
    )
    # Maximum concurrent API calls for parallel quiz generation
    QUIZ_MAX_CONCURRENCY: int = int(os.getenv("QUIZ_MAX_CONCURRENCY", "4"))
    
    # Collections
    USERS_COLLECTION = "users"
    DECK_PROGRESS_COLLECTION = "deck_progress" 
    QUIZ_RESULTS_COLLECTION = "quiz_results"
    STUDY_SESSIONS_COLLECTION = "study_sessions"
    BOOKMARKS_COLLECTION = "bookmarks"
    FLASHCARD_FEEDBACK_COLLECTION = "flashcard_feedback"

# Global settings instance
settings = Settings()
