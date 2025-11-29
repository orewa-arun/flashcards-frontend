"""
Bookmark and Feedback repository - PostgreSQL queries for bookmarks and flashcard feedback.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger(__name__)


class BookmarkFeedbackRepository:
    """Repository for bookmark and feedback database operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Bookmarks Operations ====================
    
    async def add_bookmark(
        self,
        firebase_uid: str,
        course_id: str,
        deck_id: str,
        flashcard_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Add a flashcard bookmark.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            flashcard_index: Index of the flashcard
            
        Returns:
            Created bookmark dict or None if already exists
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO bookmarks (firebase_uid, course_id, deck_id, flashcard_index, created_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (firebase_uid, course_id, deck_id, flashcard_index) DO NOTHING
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                firebase_uid, course_id, deck_id, flashcard_index, now
            )
            
            if not row:
                # Bookmark already exists
                return None
            
            logger.info(f"Added bookmark for user {firebase_uid}: {course_id}/{deck_id}/{flashcard_index}")
            return dict(row)
    
    async def remove_bookmark(
        self,
        firebase_uid: str,
        course_id: str,
        deck_id: str,
        flashcard_index: int
    ) -> bool:
        """
        Remove a flashcard bookmark.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            flashcard_index: Index of the flashcard
            
        Returns:
            True if bookmark was removed, False if not found
        """
        query = """
            DELETE FROM bookmarks
            WHERE firebase_uid = $1 AND course_id = $2 AND deck_id = $3 AND flashcard_index = $4
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                firebase_uid, course_id, deck_id, flashcard_index
            )
            
            if row:
                logger.info(f"Removed bookmark for user {firebase_uid}: {course_id}/{deck_id}/{flashcard_index}")
                return True
            return False
    
    async def get_user_bookmarks(
        self,
        firebase_uid: str,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all bookmarks for a user.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Optional course filter
            
        Returns:
            List of bookmark dicts
        """
        if course_id:
            query = """
                SELECT id, firebase_uid, course_id, deck_id, flashcard_index, created_at
                FROM bookmarks
                WHERE firebase_uid = $1 AND course_id = $2
                ORDER BY created_at DESC
            """
            params = [firebase_uid, course_id]
        else:
            query = """
                SELECT id, firebase_uid, course_id, deck_id, flashcard_index, created_at
                FROM bookmarks
                WHERE firebase_uid = $1
                ORDER BY created_at DESC
            """
            params = [firebase_uid]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def bookmark_exists(
        self,
        firebase_uid: str,
        course_id: str,
        deck_id: str,
        flashcard_index: int
    ) -> bool:
        """
        Check if a bookmark exists.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            flashcard_index: Index of the flashcard
            
        Returns:
            True if bookmark exists
        """
        query = """
            SELECT id FROM bookmarks
            WHERE firebase_uid = $1 AND course_id = $2 AND deck_id = $3 AND flashcard_index = $4
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                firebase_uid, course_id, deck_id, flashcard_index
            )
            return row is not None
    
    # ==================== Feedback Operations ====================
    
    async def submit_feedback(
        self,
        user_id: str,
        course_id: str,
        deck_id: str,
        flashcard_index: int,
        rating: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit or update feedback for a flashcard.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            flashcard_index: Index of the flashcard
            rating: Rating value (1 for like, -1 for dislike)
            session_id: Optional session identifier
            
        Returns:
            Feedback dict
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO flashcard_feedback (
                user_id, course_id, deck_id, flashcard_index, session_id, rating, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (user_id, course_id, deck_id, flashcard_index)
            DO UPDATE SET
                rating = $6,
                session_id = $5,
                created_at = $7
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, course_id, deck_id, flashcard_index, session_id, rating, now
            )
            
            logger.info(f"Submitted feedback for user {user_id}: {course_id}/{deck_id}/{flashcard_index} = {rating}")
            return dict(row)
    
    async def get_user_feedback(
        self,
        user_id: str,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all feedback for a user.
        
        Args:
            user_id: Firebase user ID
            course_id: Optional course filter
            
        Returns:
            List of feedback dicts
        """
        if course_id:
            query = """
                SELECT id, user_id, course_id, deck_id, flashcard_index, session_id, rating, created_at
                FROM flashcard_feedback
                WHERE user_id = $1 AND course_id = $2
                ORDER BY created_at DESC
            """
            params = [user_id, course_id]
        else:
            query = """
                SELECT id, user_id, course_id, deck_id, flashcard_index, session_id, rating, created_at
                FROM flashcard_feedback
                WHERE user_id = $1
                ORDER BY created_at DESC
            """
            params = [user_id]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_feedback_for_flashcard(
        self,
        user_id: str,
        course_id: str,
        deck_id: str,
        flashcard_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get feedback for a specific flashcard.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            flashcard_index: Index of the flashcard
            
        Returns:
            Feedback dict or None
        """
        query = """
            SELECT id, user_id, course_id, deck_id, flashcard_index, session_id, rating, created_at
            FROM flashcard_feedback
            WHERE user_id = $1 AND course_id = $2 AND deck_id = $3 AND flashcard_index = $4
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, course_id, deck_id, flashcard_index
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def clear_feedback(
        self,
        user_id: str,
        course_id: str,
        deck_id: str,
        flashcard_index: int
    ) -> bool:
        """
        Clear/remove feedback for a specific flashcard.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            flashcard_index: Index of the flashcard
            
        Returns:
            True if feedback was removed, False if not found
        """
        query = """
            DELETE FROM flashcard_feedback
            WHERE user_id = $1 AND course_id = $2 AND deck_id = $3 AND flashcard_index = $4
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, course_id, deck_id, flashcard_index
            )
            
            if row:
                logger.info(f"Cleared feedback for user {user_id}: {course_id}/{deck_id}/{flashcard_index}")
                return True
            return False
    
    async def get_feedback_summary_for_deck(
        self,
        course_id: str,
        deck_id: str
    ) -> Dict[str, Any]:
        """
        Get aggregated feedback summary for a deck.
        
        Args:
            course_id: Course identifier
            deck_id: Deck identifier
            
        Returns:
            Summary with likes, dislikes, and total count
        """
        query = """
            SELECT 
                COUNT(*) FILTER (WHERE rating = 1) as likes,
                COUNT(*) FILTER (WHERE rating = -1) as dislikes,
                COUNT(*) as total
            FROM flashcard_feedback
            WHERE course_id = $1 AND deck_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, course_id, deck_id)
            
            return {
                "likes": row["likes"] or 0,
                "dislikes": row["dislikes"] or 0,
                "total": row["total"] or 0
            }


