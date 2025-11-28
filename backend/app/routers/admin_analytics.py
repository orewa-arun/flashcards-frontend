"""Admin analytics API endpoints using PostgreSQL - no authentication, security through obscurity."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException

from app.db.postgres import get_postgres_pool
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin-analytics", tags=["admin-analytics"])


@router.get("/overview", response_model=Dict[str, Any])
async def get_analytics_overview():
    """Get high-level analytics overview."""
    try:
        pool = await get_postgres_pool()
        
        async with pool.acquire() as conn:
            # Count totals from PostgreSQL tables
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            total_quiz_attempts = await conn.fetchval("SELECT COUNT(*) FROM quiz_results")
            total_feedback = await conn.fetchval("SELECT COUNT(*) FROM flashcard_feedback")
            total_bookmarks = await conn.fetchval("SELECT COUNT(*) FROM bookmarks")
            
            # Get feedback breakdown
            likes = await conn.fetchval("SELECT COUNT(*) FROM flashcard_feedback WHERE rating = 1")
            dislikes = await conn.fetchval("SELECT COUNT(*) FROM flashcard_feedback WHERE rating = -1")
        
        overview = {
            "total_users": total_users or 0,
            "total_sessions": 0,  # Sessions moved to quiz_sessions
            "completed_sessions": 0,
            "total_quiz_attempts": total_quiz_attempts or 0,
            "total_feedback": total_feedback or 0,
            "feedback_likes": likes or 0,
            "feedback_dislikes": dislikes or 0,
            "total_bookmarks": total_bookmarks or 0
        }
        
        logger.info("Retrieved admin analytics overview")
        return overview
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.get("/quiz-results", response_model=List[Dict[str, Any]])
async def get_quiz_performance_summary():
    """Get aggregated quiz performance by deck."""
    try:
        pool = await get_postgres_pool()
        
        query = """
            SELECT 
                course_id,
                deck_id,
                COUNT(*) as total_attempts,
                AVG(percentage) as average_score,
                MAX(percentage) as highest_score,
                MIN(percentage) as lowest_score,
                AVG(time_taken) as average_time,
                AVG(total_questions) as total_questions_avg
            FROM quiz_results
            GROUP BY course_id, deck_id
            ORDER BY total_attempts DESC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        formatted_stats = []
        for row in rows:
            formatted_stats.append({
                "course_id": row["course_id"],
                "deck_id": row["deck_id"],
                "total_attempts": row["total_attempts"],
                "average_score_percentage": round(row["average_score"] or 0, 2),
                "highest_score_percentage": round(row["highest_score"] or 0, 2),
                "lowest_score_percentage": round(row["lowest_score"] or 0, 2),
                "average_time_seconds": round(row["average_time"] or 0, 2),
                "average_total_questions": round(row["total_questions_avg"] or 0, 1)
            })
        
        logger.info(f"Retrieved quiz performance summary for {len(formatted_stats)} decks")
        return formatted_stats
        
    except Exception as e:
        logger.error(f"Error getting quiz performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz performance: {str(e)}")


@router.get("/flashcard-feedback/summary", response_model=List[Dict[str, Any]])
async def get_flashcard_feedback_summary():
    """Get like/dislike counts per flashcard."""
    try:
        pool = await get_postgres_pool()
        
        query = """
            SELECT 
                course_id,
                deck_id,
                flashcard_index,
                COUNT(*) as total_feedback,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as likes,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as dislikes
            FROM flashcard_feedback
            GROUP BY course_id, deck_id, flashcard_index
            ORDER BY total_feedback DESC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        formatted_stats = []
        for row in rows:
            net_score = (row["likes"] or 0) - (row["dislikes"] or 0)
            
            formatted_stats.append({
                "course_id": row["course_id"],
                "deck_id": row["deck_id"],
                "flashcard_index": row["flashcard_index"],
                "flashcard_identifier": f"{row['course_id']}:{row['deck_id']}:{row['flashcard_index']}",
                "total_feedback": row["total_feedback"],
                "likes": row["likes"] or 0,
                "dislikes": row["dislikes"] or 0,
                "net_score": net_score
            })
        
        logger.info(f"Retrieved flashcard feedback summary for {len(formatted_stats)} flashcards")
        return formatted_stats
        
    except Exception as e:
        logger.error(f"Error getting flashcard feedback summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback summary: {str(e)}")


@router.get("/flashcard-feedback/details", response_model=List[Dict[str, Any]])
async def get_flashcard_feedback_details():
    """Get raw feedback log with user/session info."""
    try:
        pool = await get_postgres_pool()
        
        query = """
            SELECT 
                id, user_id, session_id, course_id, deck_id,
                flashcard_index, rating, created_at
            FROM flashcard_feedback
            ORDER BY created_at DESC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        formatted_feedback = []
        for row in rows:
            formatted_feedback.append({
                "feedback_id": str(row["id"]),
                "user_id": row["user_id"],
                "session_id": row["session_id"],
                "course_id": row["course_id"],
                "deck_id": row["deck_id"],
                "flashcard_index": row["flashcard_index"],
                "flashcard_identifier": f"{row['course_id']}:{row['deck_id']}:{row['flashcard_index']}",
                "rating": row["rating"],
                "rating_text": "like" if row["rating"] == 1 else "dislike",
                "created_at": row["created_at"]
            })
        
        logger.info(f"Retrieved {len(formatted_feedback)} feedback details")
        return formatted_feedback
        
    except Exception as e:
        logger.error(f"Error getting flashcard feedback details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback details: {str(e)}")


@router.get("/users", response_model=List[Dict[str, Any]])
async def get_all_users_summary():
    """Get all user summaries with activity stats."""
    try:
        pool = await get_postgres_pool()
        
        query = """
            SELECT 
                firebase_uid, created_at, last_active,
                total_decks_studied, total_quiz_attempts
            FROM users
            ORDER BY last_active DESC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        formatted_users = []
        for row in rows:
            formatted_users.append({
                "user_id": row["firebase_uid"],
                "created_at": row["created_at"],
                "last_active": row["last_active"],
                "total_decks_studied": row["total_decks_studied"] or 0,
                "total_quiz_attempts": row["total_quiz_attempts"] or 0
            })
        
        logger.info(f"Retrieved {len(formatted_users)} users summary")
        return formatted_users
        
    except Exception as e:
        logger.error(f"Error getting users summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users summary: {str(e)}")
