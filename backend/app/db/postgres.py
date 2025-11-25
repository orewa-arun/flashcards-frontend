"""PostgreSQL database connection using asyncpg for high performance."""

import logging
from typing import Optional
import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_postgres_pool() -> asyncpg.Pool:
    """
    Get the global connection pool.
    
    Returns:
        asyncpg.Pool: Database connection pool
    """
    global _pool
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_postgres_db() first.")
    return _pool


async def init_postgres_db():
    """Initialize PostgreSQL connection pool and create tables."""
    global _pool
    
    try:
        # Parse the SQLAlchemy URL to asyncpg format
        # postgresql+asyncpg://user:pass@host:port/dbname -> postgresql://user:pass@host:port/dbname
        db_url = settings.POSTGRES_URL.replace("+asyncpg", "")
        
        # Create connection pool
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        logger.info("PostgreSQL connection pool created successfully")
        
        # Create tables
        await _create_tables()
        
        logger.info("PostgreSQL database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL database: {str(e)}")
        raise


async def _create_tables():
    """Create database tables if they don't exist."""
    global _pool
    
    # SQL for creating courses table
    create_courses_table = """
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            course_code VARCHAR(255) UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            instructor TEXT,
            additional_info TEXT,
            reference_textbooks JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_courses_course_code ON courses(course_code);
    """
    
    # SQL for creating lectures table
    create_lectures_table = """
        CREATE TABLE IF NOT EXISTS lectures (
            id SERIAL PRIMARY KEY,
            course_code VARCHAR(255) NOT NULL REFERENCES courses(course_code) ON DELETE CASCADE,
            lecture_title TEXT NOT NULL,
            r2_pdf_path TEXT NOT NULL,
            structured_analysis JSONB,
            flashcards JSONB,
            quizzes JSONB,
            analysis_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            flashcard_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            quiz_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            qdrant_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            error_log JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_lectures_course_code ON lectures(course_code);
        CREATE INDEX IF NOT EXISTS idx_lecture_analysis_status ON lectures(analysis_status);
        CREATE INDEX IF NOT EXISTS idx_lecture_flashcard_status ON lectures(flashcard_status);
        CREATE INDEX IF NOT EXISTS idx_lecture_quiz_status ON lectures(quiz_status);
        CREATE INDEX IF NOT EXISTS idx_lecture_qdrant_status ON lectures(qdrant_status);
    """
    
    async with _pool.acquire() as conn:
        await conn.execute(create_courses_table)
        await conn.execute(create_lectures_table)
        logger.info("Database tables created/verified successfully")


async def close_postgres_db():
    """Close PostgreSQL connection pool."""
    global _pool
    
    if _pool:
        try:
            await _pool.close()
            logger.info("PostgreSQL connection pool closed")
        except Exception as e:
            logger.error(f"Failed to close PostgreSQL pool: {str(e)}")
            raise
