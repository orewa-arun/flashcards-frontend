"""Configuration settings for the FastAPI analytics backend."""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings."""
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "study_analytics")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:5173,http://localhost:3000"
    ).split(",")
    
    # Collections
    USERS_COLLECTION = "users"
    DECK_PROGRESS_COLLECTION = "deck_progress" 
    QUIZ_RESULTS_COLLECTION = "quiz_results"
    STUDY_SESSIONS_COLLECTION = "study_sessions"
    BOOKMARKS_COLLECTION = "bookmarks"
    FLASHCARD_FEEDBACK_COLLECTION = "flashcard_feedback"

# Global settings instance
settings = Settings()
