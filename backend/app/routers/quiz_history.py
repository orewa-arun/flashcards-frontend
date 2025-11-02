"""Quiz history API endpoints for viewing past quiz attempts."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_database
from app.models.quiz import QuizResult
from app.config import settings
from app.firebase_auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/quiz-history", tags=["quiz-history"])

class QuizHistorySummary:
    """Quiz history summary for deck view."""
    def __init__(self, deck_id: str, course_id: str, attempt_count: int, highest_score: int, 
                 highest_percentage: float, latest_attempt: Any):
        self.deck_id = deck_id
        self.course_id = course_id
        self.attempt_count = attempt_count
        self.highest_score = highest_score
        self.highest_percentage = highest_percentage
        self.latest_attempt = latest_attempt

class QuizAttemptSummary:
    """Individual quiz attempt summary."""
    def __init__(self, result_id: str, score: int, total_questions: int, percentage: float, 
                 time_taken: int, completed_at: Any):
        self.result_id = result_id
        self.score = score
        self.total_questions = total_questions
        self.percentage = percentage
        self.time_taken = time_taken
        self.completed_at = completed_at

@router.get("", response_model=List[Dict[str, Any]])
async def get_quiz_history_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get quiz history summary grouped by deck with highest scores."""
    firebase_uid = current_user['uid']
    logger.info(f"Fetching quiz history summary for firebase_uid: {firebase_uid}")
    try:
        quiz_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        
        # Aggregate quiz results by deck
        pipeline = [
            {"$match": {"firebase_uid": firebase_uid}},
            {"$sort": {"completed_at": -1}},
            {
                "$group": {
                    "_id": {
                        "deck_id": "$deck_id",
                        "course_id": "$course_id"
                    },
                    "attempt_count": {"$sum": 1},
                    "highest_score": {"$max": "$score"},
                    "highest_percentage": {"$max": "$percentage"},
                    "latest_attempt": {"$first": "$$ROOT"},
                    "attempts": {"$push": "$$ROOT"}
                }
            },
            {"$sort": {"latest_attempt.completed_at": -1}}
        ]
        
        cursor = quiz_collection.aggregate(pipeline)
        aggregated_results = await cursor.to_list(length=None)
        
        # Format results
        quiz_history = []
        for result in aggregated_results:
            deck_info = result["_id"]
            quiz_history.append({
                "deck_id": deck_info["deck_id"],
                "course_id": deck_info["course_id"],
                "attempt_count": result["attempt_count"],
                "highest_score": result["highest_score"],
                "highest_percentage": result["highest_percentage"],
                "latest_attempt_date": result["latest_attempt"]["completed_at"]
            })
        
        logger.info(f"Retrieved quiz history summary for user {firebase_uid}: {len(quiz_history)} decks")
        
        return quiz_history
        
    except Exception as e:
        logger.error(f"Error getting quiz history summary for user {firebase_uid}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz history: {str(e)}")

@router.get("/{deck_id}", response_model=List[Dict[str, Any]])
async def get_deck_quiz_attempts(
    deck_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all quiz attempts for a specific deck."""
    firebase_uid = current_user['uid']
    try:
        quiz_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        
        # Get all attempts for this deck, sorted by completion date (newest first)
        cursor = quiz_collection.find({
            "firebase_uid": firebase_uid,
            "deck_id": deck_id
        }).sort("completed_at", -1)
        
        attempts = await cursor.to_list(length=None)
        
        # Format results
        attempt_summaries = []
        for attempt in attempts:
            attempt_summaries.append({
                "result_id": str(attempt["_id"]),
                "score": attempt["score"],
                "total_questions": attempt["total_questions"],
                "percentage": attempt["percentage"],
                "time_taken": attempt["time_taken"],
                "completed_at": attempt["completed_at"]
            })
        
        logger.info(f"Retrieved {len(attempt_summaries)} quiz attempts for user {firebase_uid}, deck {deck_id}")
        
        return attempt_summaries
        
    except Exception as e:
        logger.error(f"Error getting quiz attempts for user {firebase_uid}, deck {deck_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz attempts: {str(e)}")

@router.get("/attempt/{result_id}", response_model=Dict[str, Any])
async def get_quiz_attempt_details(
    result_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get detailed results for a specific quiz attempt."""
    firebase_uid = current_user['uid']
    try:
        from bson import ObjectId
        quiz_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        
        # Validate ObjectId format
        if not ObjectId.is_valid(result_id):
            raise HTTPException(status_code=400, detail="Invalid result ID format")
        
        # Get the specific quiz attempt
        quiz_result = await quiz_collection.find_one({
            "_id": ObjectId(result_id),
            "firebase_uid": firebase_uid
        })
        
        if not quiz_result:
            raise HTTPException(status_code=404, detail="Quiz attempt not found")
        
        # Format detailed results
        detailed_result = {
            "result_id": str(quiz_result["_id"]),
            "firebase_uid": quiz_result["firebase_uid"],
            "deck_id": quiz_result["deck_id"],
            "course_id": quiz_result["course_id"],
            "score": quiz_result["score"],
            "total_questions": quiz_result["total_questions"],
            "percentage": quiz_result["percentage"],
            "time_taken": quiz_result["time_taken"],
            "completed_at": quiz_result["completed_at"],
            "question_results": quiz_result.get("question_results", [])
        }
        
        logger.info(f"Retrieved detailed quiz results for user {firebase_uid}, attempt {result_id}")
        
        return detailed_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quiz attempt details for user {firebase_uid}, attempt {result_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz attempt details: {str(e)}")
