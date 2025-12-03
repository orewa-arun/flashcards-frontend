"""API endpoints for exam readiness calculations."""

import logging
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.db.postgres import get_postgres_pool
from app.firebase_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/readiness", tags=["readiness"])


@router.get("/lectures")
async def get_lecture_readiness(
    course_id: str = Query(..., description="Course identifier"),
    lecture_ids: str = Query(..., description="Comma-separated list of lecture IDs"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, float]:
    """
    Get readiness scores for specific lectures.
    
    Calculates the average accuracy_score from user_flashcard_performance 
    for each lecture the user has attempted.
    
    Args:
        course_id: Course identifier
        lecture_ids: Comma-separated list of lecture IDs
        current_user: Authenticated user from Firebase
        
    Returns:
        Dictionary mapping lecture_id to readiness score (0-100)
    """
    try:
        user_id = current_user['uid']
        
        # Parse lecture IDs
        lecture_id_list = [lid.strip() for lid in lecture_ids.split(",") if lid.strip()]
        
        if not lecture_id_list:
            return {}
        
        pool = await get_postgres_pool()
        
        # Query for average accuracy per lecture
        # Using a parameterized query with ANY for the list
        query = """
            SELECT 
                lecture_id,
                AVG(accuracy_score) * 100 as readiness_score,
                COUNT(*) as flashcards_attempted
            FROM user_flashcard_performance
            WHERE user_id = $1 
              AND course_id = $2
              AND lecture_id = ANY($3::text[])
            GROUP BY lecture_id
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, course_id, lecture_id_list)
        
        # Build result dictionary
        result = {}
        for row in rows:
            lecture_id = row['lecture_id']
            score = float(row['readiness_score']) if row['readiness_score'] else 0.0
            result[lecture_id] = round(score, 1)
        
        # For lectures with no data, return 0
        for lid in lecture_id_list:
            if lid not in result:
                result[lid] = 0.0
        
        logger.info(f"Readiness for user {user_id}, course {course_id}: {len(result)} lectures")
        
        return result
    
    except Exception as e:
        logger.error(f"Error calculating lecture readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate readiness: {str(e)}"
        )


@router.get("/exam/{exam_id}")
async def get_exam_readiness_breakdown(
    exam_id: str,
    course_id: str = Query(..., description="Course identifier"),
    lecture_ids: str = Query(..., description="Comma-separated list of lecture IDs covered by exam"),
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """
    Get detailed readiness breakdown for an exam.
    
    Returns both per-lecture scores and an overall average.
    
    Args:
        exam_id: Exam identifier
        course_id: Course identifier
        lecture_ids: Comma-separated list of lecture IDs covered by the exam
        current_user: Authenticated user from Firebase
        
    Returns:
        Dictionary with lecture_scores and overall_score
    """
    try:
        user_id = current_user['uid']
        
        # Parse lecture IDs
        lecture_id_list = [lid.strip() for lid in lecture_ids.split(",") if lid.strip()]
        
        if not lecture_id_list:
            return {
                "exam_id": exam_id,
                "course_id": course_id,
                "lecture_scores": {},
                "overall_score": 0.0
            }
        
        pool = await get_postgres_pool()
        
        # Query for average accuracy per lecture
        query = """
            SELECT 
                lecture_id,
                AVG(accuracy_score) * 100 as readiness_score,
                COUNT(*) as flashcards_attempted
            FROM user_flashcard_performance
            WHERE user_id = $1 
              AND course_id = $2
              AND lecture_id = ANY($3::text[])
            GROUP BY lecture_id
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, course_id, lecture_id_list)
        
        # Build lecture scores
        lecture_scores = {}
        total_score = 0.0
        scored_count = 0
        
        for row in rows:
            lecture_id = row['lecture_id']
            score = float(row['readiness_score']) if row['readiness_score'] else 0.0
            lecture_scores[lecture_id] = {
                "score": round(score, 1),
                "flashcards_attempted": row['flashcards_attempted']
            }
            total_score += score
            scored_count += 1
        
        # For lectures with no data, return 0
        for lid in lecture_id_list:
            if lid not in lecture_scores:
                lecture_scores[lid] = {
                    "score": 0.0,
                    "flashcards_attempted": 0
                }
        
        # Calculate overall average (only from lectures with data)
        overall_score = round(total_score / scored_count, 1) if scored_count > 0 else 0.0
        
        logger.info(f"Exam {exam_id} readiness for user {user_id}: {overall_score}%")
        
        return {
            "exam_id": exam_id,
            "course_id": course_id,
            "lecture_scores": lecture_scores,
            "overall_score": overall_score,
            "lectures_with_data": scored_count,
            "total_lectures": len(lecture_id_list)
        }
    
    except Exception as e:
        logger.error(f"Error calculating exam readiness breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate readiness: {str(e)}"
        )

