"""Quiz history API endpoints for viewing past quiz attempts using PostgreSQL."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from app.db.postgres import get_postgres_pool
from app.repositories.quiz_repository import QuizRepository
from app.firebase_auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/quiz-history", tags=["quiz-history"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_quiz_history_summary(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get quiz history summary grouped by deck with highest scores."""
    firebase_uid = current_user['uid']
    logger.info(f"Fetching quiz history summary for firebase_uid: {firebase_uid}")
    
    try:
        pool = await get_postgres_pool()
        
        # Query to get aggregated quiz history
        query = """
            SELECT 
                deck_id,
                course_id,
                COUNT(*) as attempt_count,
                MAX(score) as highest_score,
                MAX(percentage) as highest_percentage,
                MAX(completed_at) as latest_attempt_date
            FROM quiz_results
            WHERE firebase_uid = $1
            GROUP BY deck_id, course_id
            ORDER BY MAX(completed_at) DESC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, firebase_uid)
        
        quiz_history = []
        for row in rows:
            quiz_history.append({
                "deck_id": row["deck_id"],
                "course_id": row["course_id"],
                "attempt_count": row["attempt_count"],
                "highest_score": row["highest_score"],
                "highest_percentage": row["highest_percentage"],
                "latest_attempt_date": row["latest_attempt_date"]
            })
        
        logger.info(f"Retrieved quiz history summary for user {firebase_uid}: {len(quiz_history)} decks")
        
        return quiz_history
        
    except Exception as e:
        logger.error(f"Error getting quiz history summary for user {firebase_uid}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz history: {str(e)}")


@router.get("/{deck_id}", response_model=List[Dict[str, Any]])
async def get_deck_quiz_attempts(
    deck_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all quiz attempts for a specific deck."""
    firebase_uid = current_user['uid']
    
    try:
        pool = await get_postgres_pool()
        
        query = """
            SELECT 
                id, score, total_questions, percentage, 
                time_taken, completed_at, difficulty
            FROM quiz_results
            WHERE firebase_uid = $1 AND deck_id = $2
            ORDER BY completed_at DESC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, firebase_uid, deck_id)
        
        attempt_summaries = []
        for row in rows:
            attempt_summaries.append({
                "result_id": str(row["id"]),
                "score": row["score"],
                "total_questions": row["total_questions"],
                "percentage": row["percentage"],
                "time_taken": row["time_taken"],
                "completed_at": row["completed_at"],
                "difficulty": row.get("difficulty", "medium")
            })
        
        logger.info(f"Retrieved {len(attempt_summaries)} quiz attempts for user {firebase_uid}, deck {deck_id}")
        
        return attempt_summaries
        
    except Exception as e:
        logger.error(f"Error getting quiz attempts for user {firebase_uid}, deck {deck_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz attempts: {str(e)}")


@router.get("/attempt/{result_id}", response_model=Dict[str, Any])
async def get_quiz_attempt_details(
    result_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed results for a specific quiz attempt."""
    firebase_uid = current_user['uid']
    
    try:
        pool = await get_postgres_pool()
        
        # Validate result_id is an integer
        try:
            result_id_int = int(result_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid result ID format")
        
        query = """
            SELECT 
                id, firebase_uid, deck_id, course_id, lecture_id,
                score, total_questions, percentage, time_taken,
                completed_at, question_results, difficulty
            FROM quiz_results
            WHERE id = $1 AND firebase_uid = $2
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, result_id_int, firebase_uid)
        
        if not row:
            raise HTTPException(status_code=404, detail="Quiz attempt not found")
        
        import json
        question_results = row["question_results"]
        if isinstance(question_results, str):
            question_results = json.loads(question_results)
        
        detailed_result = {
            "result_id": str(row["id"]),
            "firebase_uid": row["firebase_uid"],
            "deck_id": row["deck_id"],
            "course_id": row["course_id"],
            "score": row["score"],
            "total_questions": row["total_questions"],
            "percentage": row["percentage"],
            "time_taken": row["time_taken"],
            "completed_at": row["completed_at"],
            "question_results": question_results
        }
        
        logger.info(f"Retrieved detailed quiz results for user {firebase_uid}, attempt {result_id}")
        
        return detailed_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz attempt details for user {firebase_uid}, attempt {result_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz attempt details: {str(e)}")
