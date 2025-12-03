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
            course_repository_link TEXT,
            repository_created_by TEXT,
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
            consolidated_structured_analysis JSONB,
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
    
    # ==================== CHAT & CONVERSATIONS ====================
    
    # SQL for creating conversations table
    create_conversations_table = """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            conversation_id UUID UNIQUE NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            lecture_id VARCHAR(255) NOT NULL,
            title TEXT NOT NULL DEFAULT 'New Chat',
            notes TEXT DEFAULT '',
            message_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_conversations_user_course_lecture ON conversations(user_id, course_id, lecture_id);
    """
    
    # SQL for creating messages table
    create_messages_table = """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_timestamp ON messages(conversation_id, timestamp);
    """
    
    # ==================== USER ANALYTICS & PROGRESS ====================
    
    # SQL for creating user_deck_progress table (spaced repetition / flashcard review)
    create_user_deck_progress_table = """
        CREATE TABLE IF NOT EXISTS user_deck_progress (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            deck_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            progress FLOAT NOT NULL DEFAULT 0.0,
            cards_studied INTEGER NOT NULL DEFAULT 0,
            total_cards INTEGER NOT NULL DEFAULT 0,
            last_studied TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            study_streak INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, deck_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_deck_progress_user_id ON user_deck_progress(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_deck_progress_user_deck ON user_deck_progress(user_id, deck_id);
    """
    
    # SQL for creating user_quiz_attempts table (granular question history)
    create_user_quiz_attempts_table = """
        CREATE TABLE IF NOT EXISTS user_quiz_attempts (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            lecture_id VARCHAR(255) NOT NULL,
            flashcard_id VARCHAR(255) NOT NULL,
            question_hash VARCHAR(64) NOT NULL,
            is_correct BOOLEAN NOT NULL,
            partial_credit FLOAT DEFAULT 0.0,
            time_taken_seconds INTEGER,
            difficulty_level VARCHAR(50),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_quiz_attempts_user_id ON user_quiz_attempts(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_quiz_attempts_flashcard ON user_quiz_attempts(user_id, flashcard_id);
        CREATE INDEX IF NOT EXISTS idx_user_quiz_attempts_lecture ON user_quiz_attempts(user_id, course_id, lecture_id);
        CREATE INDEX IF NOT EXISTS idx_user_quiz_attempts_timestamp ON user_quiz_attempts(user_id, timestamp DESC);
    """
    
    # SQL for creating user_flashcard_performance table (aggregated stats for adaptive quizzes)
    create_user_flashcard_performance_table = """
        CREATE TABLE IF NOT EXISTS user_flashcard_performance (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            flashcard_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            lecture_id VARCHAR(255) NOT NULL,
            is_weak BOOLEAN NOT NULL DEFAULT FALSE,
            next_level VARCHAR(50) NOT NULL DEFAULT 'easy',
            coverage_score FLOAT NOT NULL DEFAULT 0.0,
            accuracy_score FLOAT NOT NULL DEFAULT 0.0,
            momentum_score FLOAT NOT NULL DEFAULT 0.0,
            comfortability_score FLOAT NOT NULL DEFAULT 0.0,
            total_points_earned FLOAT NOT NULL DEFAULT 0.0,
            performance_data JSONB DEFAULT '{}'::jsonb,
            last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, flashcard_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_flashcard_performance_user_id ON user_flashcard_performance(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_flashcard_performance_flashcard ON user_flashcard_performance(user_id, flashcard_id);
        CREATE INDEX IF NOT EXISTS idx_user_flashcard_performance_weak ON user_flashcard_performance(user_id, is_weak);
        CREATE INDEX IF NOT EXISTS idx_user_flashcard_performance_lecture ON user_flashcard_performance(user_id, course_id, lecture_id);
    """
    
    # ==================== USER MANAGEMENT ====================
    
    # SQL for creating users table (Firebase users)
    create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            firebase_uid VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255),
            name VARCHAR(255),
            picture TEXT,
            email_verified BOOLEAN NOT NULL DEFAULT FALSE,
            total_decks_studied INTEGER NOT NULL DEFAULT 0,
            total_quiz_attempts INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_active TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """
    
    # SQL for creating user_profiles table (course enrollment)
    create_user_profiles_table = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) UNIQUE NOT NULL,
            enrolled_courses JSONB DEFAULT '[]'::jsonb,
            preferences JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
    """
    
    # ==================== BOOKMARKS & FEEDBACK ====================
    
    # SQL for creating bookmarks table
    create_bookmarks_table = """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id SERIAL PRIMARY KEY,
            firebase_uid VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            deck_id VARCHAR(255) NOT NULL,
            flashcard_index INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(firebase_uid, course_id, deck_id, flashcard_index)
        );
        
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(firebase_uid);
        CREATE INDEX IF NOT EXISTS idx_bookmarks_user_course ON bookmarks(firebase_uid, course_id);
    """
    
    # SQL for creating flashcard_feedback table
    create_flashcard_feedback_table = """
        CREATE TABLE IF NOT EXISTS flashcard_feedback (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            deck_id VARCHAR(255) NOT NULL,
            flashcard_index INTEGER NOT NULL,
            session_id VARCHAR(255),
            rating INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, course_id, deck_id, flashcard_index)
        );
        
        CREATE INDEX IF NOT EXISTS idx_flashcard_feedback_user ON flashcard_feedback(user_id);
        CREATE INDEX IF NOT EXISTS idx_flashcard_feedback_user_course ON flashcard_feedback(user_id, course_id);
    """
    
    # ==================== QUIZ SYSTEM ====================
    
    # SQL for creating quiz_sessions table (active quiz state)
    create_quiz_sessions_table = """
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id SERIAL PRIMARY KEY,
            quiz_id UUID UNIQUE NOT NULL,
            firebase_uid VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            deck_id VARCHAR(255) NOT NULL,
            difficulty VARCHAR(50) NOT NULL DEFAULT 'medium',
            questions JSONB NOT NULL DEFAULT '[]'::jsonb,
            completed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        
        CREATE INDEX IF NOT EXISTS idx_quiz_sessions_quiz_id ON quiz_sessions(quiz_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user ON quiz_sessions(firebase_uid);
        CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user_active ON quiz_sessions(firebase_uid, completed);
    """
    
    # SQL for creating quiz_results table (completed quiz history)
    create_quiz_results_table = """
        CREATE TABLE IF NOT EXISTS quiz_results (
            id SERIAL PRIMARY KEY,
            firebase_uid VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            lecture_id VARCHAR(255) NOT NULL,
            deck_id VARCHAR(255) NOT NULL,
            quiz_id UUID,
            difficulty VARCHAR(50) NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage FLOAT NOT NULL,
            time_taken INTEGER,
            question_results JSONB NOT NULL DEFAULT '[]'::jsonb,
            completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_quiz_results_user ON quiz_results(firebase_uid);
        CREATE INDEX IF NOT EXISTS idx_quiz_results_user_course ON quiz_results(firebase_uid, course_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_results_user_lecture ON quiz_results(firebase_uid, course_id, lecture_id);
        CREATE INDEX IF NOT EXISTS idx_quiz_results_completed ON quiz_results(firebase_uid, completed_at DESC);
    """
    
    # ==================== EXAM READINESS ====================
    
    # SQL for creating user_exam_readiness table
    create_user_exam_readiness_table = """
        CREATE TABLE IF NOT EXISTS user_exam_readiness (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            exam_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            overall_readiness_score FLOAT NOT NULL DEFAULT 0.0,
            coverage_factor FLOAT NOT NULL DEFAULT 0.0,
            accuracy_factor FLOAT NOT NULL DEFAULT 0.0,
            momentum_factor FLOAT NOT NULL DEFAULT 0.0,
            raw_scores JSONB DEFAULT '{}'::jsonb,
            max_possible_scores JSONB DEFAULT '{}'::jsonb,
            weak_flashcards JSONB DEFAULT '[]'::jsonb,
            total_flashcards_in_exam INTEGER NOT NULL DEFAULT 0,
            flashcards_attempted INTEGER NOT NULL DEFAULT 0,
            last_calculated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, exam_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_exam_readiness_user ON user_exam_readiness(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_exam_readiness_user_exam ON user_exam_readiness(user_id, exam_id);
        CREATE INDEX IF NOT EXISTS idx_user_exam_readiness_course ON user_exam_readiness(user_id, course_id);
    """
    
    # SQL for creating course_timetables table
    create_course_timetables_table = """
        CREATE TABLE IF NOT EXISTS course_timetables (
            id SERIAL PRIMARY KEY,
            course_id VARCHAR(255) UNIQUE NOT NULL,
            exams JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_course_timetables_course ON course_timetables(course_id);
    """
    
    # ==================== MIX MODE SESSIONS ====================
    
    # SQL for creating mix_sessions table
    create_mix_sessions_table = """
        CREATE TABLE IF NOT EXISTS mix_sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            course_id VARCHAR(255) NOT NULL,
            deck_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            current_round INTEGER NOT NULL DEFAULT 1,
            flashcard_master_order JSONB NOT NULL DEFAULT '[]'::jsonb,
            activity_queue JSONB NOT NULL DEFAULT '[]'::jsonb,
            seen_in_current_round JSONB NOT NULL DEFAULT '[]'::jsonb,
            asked_question_hashes JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_mix_sessions_session_id ON mix_sessions(session_id);
        CREATE INDEX IF NOT EXISTS idx_mix_sessions_user ON mix_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_mix_sessions_user_status ON mix_sessions(user_id, status);
    """
    
    # ==================== COURSE REPOSITORY HISTORY ====================
    
    # SQL for creating course_repository_history table (audit trail for repository link changes)
    create_course_repository_history_table = """
        CREATE TABLE IF NOT EXISTS course_repository_history (
            id SERIAL PRIMARY KEY,
            course_code VARCHAR(255) NOT NULL REFERENCES courses(course_code) ON DELETE CASCADE,
            repository_link TEXT NOT NULL,
            updated_by_name TEXT,
            updated_by_uid VARCHAR(255),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_repo_history_course_code ON course_repository_history(course_code);
        CREATE INDEX IF NOT EXISTS idx_repo_history_updated_at ON course_repository_history(course_code, updated_at DESC);
    """
    
    async with _pool.acquire() as conn:
        # Content tables
        await conn.execute(create_courses_table)
        await conn.execute(create_lectures_table)
        
        # Chat & Conversations tables
        await conn.execute(create_conversations_table)
        await conn.execute(create_messages_table)
        
        # User Analytics & Progress tables
        await conn.execute(create_user_deck_progress_table)
        await conn.execute(create_user_quiz_attempts_table)
        await conn.execute(create_user_flashcard_performance_table)
        
        # User Management tables
        await conn.execute(create_users_table)
        await conn.execute(create_user_profiles_table)
        
        # Bookmarks & Feedback tables
        await conn.execute(create_bookmarks_table)
        await conn.execute(create_flashcard_feedback_table)
        
        # Quiz System tables
        await conn.execute(create_quiz_sessions_table)
        await conn.execute(create_quiz_results_table)
        
        # Exam Readiness tables
        await conn.execute(create_user_exam_readiness_table)
        await conn.execute(create_course_timetables_table)
        
        # Mix Mode tables
        await conn.execute(create_mix_sessions_table)
        
        # Course Repository History table
        await conn.execute(create_course_repository_history_table)
        
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
