"""
Configuration Management for Flashcard Generator
Loads settings from .env file and provides easy access
"""

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv  # type: ignore
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Falling back to system environment variables only.")


class Config:
    """Application configuration."""
    
    # --- Gemini API ---
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # ==================== Directory Configuration ====================
    INPUT_DIR: str = os.getenv("INPUT_DIR", "./slides")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./flashcards_output")
    PROMPTS_DIR: str = os.getenv("PROMPTS_DIR", "./prompts")
    
    # ==================== Processing Configuration ====================
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "4000"))
    
    # ==================== Batch Processing Configuration ====================
    # Enable batch processing for concurrent API calls
    BATCH_PROCESSING_ENABLED: bool = os.getenv("BATCH_PROCESSING_ENABLED", "true").lower() == "true"
    # Maximum number of concurrent API requests
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    # Batch size for grouping tasks (0 = no limit, process all at once)
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "0"))
    
    # ==================== LaTeX Configuration ====================
    LATEX_ENABLED: bool = os.getenv("LATEX_ENABLED", "true").lower() == "true"
    LATEX_COMPILE_COMMAND: str = os.getenv("LATEX_COMPILE_COMMAND", "pdflatex")
    
    # ==================== Anki Configuration ====================
    ANKI_ENABLED: bool = os.getenv("ANKI_ENABLED", "true").lower() == "true"
    
    # --- Anki ---
    ANKI_DECK_NAME: str = os.getenv("ANKI_DECK_NAME", "Generated Flashcards")
    
    # ==================== Output Formats ====================
    GENERATE_JSON: bool = os.getenv("GENERATE_JSON", "true").lower() == "true"
    GENERATE_TXT: bool = os.getenv("GENERATE_TXT", "true").lower() == "true"
    GENERATE_CSV: bool = os.getenv("GENERATE_CSV", "true").lower() == "true"
    GENERATE_TEX: bool = os.getenv("GENERATE_TEX", "true").lower() == "true"
    GENERATE_ANKI: bool = os.getenv("GENERATE_ANKI", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate configuration settings.
        Returns (is_valid, error_message)
        """
        if not cls.GEMINI_API_KEY:
            return False, "GEMINI_API_KEY is not set. Please set it in .env file or environment."
        
        if cls.MAX_CHUNK_SIZE < 100:
            return False, "MAX_CHUNK_SIZE must be at least 100 characters."
        
        return True, None
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.INPUT_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.PROMPTS_DIR, exist_ok=True)
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)."""
        print("\n⚙️  Configuration:")
        print(f"  • Model: {cls.GEMINI_MODEL}")
        print(f"  • Input Directory: {cls.INPUT_DIR}")
        print(f"  • Output Directory: {cls.OUTPUT_DIR}")
        print(f"  • Max Chunk Size: {cls.MAX_CHUNK_SIZE} chars")
        print(f"  • Batch Processing: {'Enabled' if cls.BATCH_PROCESSING_ENABLED else 'Disabled'}")
        if cls.BATCH_PROCESSING_ENABLED:
            print(f"  • Max Concurrent Requests: {cls.MAX_CONCURRENT_REQUESTS}")
            print(f"  • Batch Size: {cls.BATCH_SIZE if cls.BATCH_SIZE > 0 else 'Unlimited'}")
        print(f"  • LaTeX Enabled: {cls.LATEX_ENABLED}")
        print(f"  • Anki Enabled: {cls.ANKI_ENABLED}")
        api_key_preview = cls.GEMINI_API_KEY[:10] + "..." if cls.GEMINI_API_KEY else "NOT SET"
        print(f"  • API Key: {api_key_preview}")

