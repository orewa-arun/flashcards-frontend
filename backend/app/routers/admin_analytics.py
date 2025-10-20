"""Admin analytics API endpoints - no authentication, security through obscurity."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_database
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin-analytics", tags=["admin-analytics"])

@router.get("/overview", response_model=Dict[str, Any])
async def get_analytics_overview(db = Depends(get_database)):
    """Get high-level analytics overview."""
    try:
        users_collection = db[settings.USERS_COLLECTION]
        sessions_collection = db[settings.STUDY_SESSIONS_COLLECTION]
        quiz_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        feedback_collection = db[settings.FLASHCARD_FEEDBACK_COLLECTION]
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        
        # Count totals
        total_users = await users_collection.count_documents({})
        total_sessions = await sessions_collection.count_documents({})
        total_quiz_attempts = await quiz_collection.count_documents({})
        total_feedback = await feedback_collection.count_documents({})
        total_bookmarks = await bookmarks_collection.count_documents({})
        
        # Get completed sessions
        completed_sessions = await sessions_collection.count_documents({"is_completed": True})
        
        # Get feedback breakdown
        likes = await feedback_collection.count_documents({"rating": 1})
        dislikes = await feedback_collection.count_documents({"rating": -1})
        
        overview = {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_quiz_attempts": total_quiz_attempts,
            "total_feedback": total_feedback,
            "feedback_likes": likes,
            "feedback_dislikes": dislikes,
            "total_bookmarks": total_bookmarks
        }
        
        logger.info("Retrieved admin analytics overview")
        return overview
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_all_sessions(db = Depends(get_database)):
    """Get all study sessions with details."""
    try:
        sessions_collection = db[settings.STUDY_SESSIONS_COLLECTION]
        
        # Get all sessions, sorted by most recent first
        cursor = sessions_collection.find({}).sort("session_start_time", -1)
        sessions = await cursor.to_list(length=None)
        
        # Format sessions data
        formatted_sessions = []
        for session in sessions:
            quiz_data = session.get("quiz_data", {})
            
            formatted_session = {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "course_id": session["course_id"],
                "deck_id": session["deck_id"],
                "session_start_time": session["session_start_time"],
                "study_duration_seconds": session.get("study_duration_seconds"),
                "quiz_duration_seconds": quiz_data.get("quiz_duration_seconds"),
                "quiz_score": quiz_data.get("score"),
                "quiz_total_questions": quiz_data.get("total_questions"),
                "quiz_percentage": quiz_data.get("percentage"),
                "is_completed": session.get("is_completed", False),
                "completed_at": session.get("completed_at"),
                "quiz_question_results": quiz_data.get("question_results", [])
            }
            formatted_sessions.append(formatted_session)
        
        logger.info(f"Retrieved {len(formatted_sessions)} sessions for admin analytics")
        return formatted_sessions
        
    except Exception as e:
        logger.error(f"Error getting all sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/quiz-results", response_model=List[Dict[str, Any]])
async def get_quiz_performance_summary(db = Depends(get_database)):
    """Get aggregated quiz performance by deck."""
    try:
        quiz_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        
        # Aggregate quiz results by deck
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "course_id": "$course_id",
                        "deck_id": "$deck_id"
                    },
                    "total_attempts": {"$sum": 1},
                    "average_score": {"$avg": "$percentage"},
                    "highest_score": {"$max": "$percentage"},
                    "lowest_score": {"$min": "$percentage"},
                    "average_time": {"$avg": "$time_taken"},
                    "total_questions_avg": {"$avg": "$total_questions"}
                }
            },
            {"$sort": {"total_attempts": -1}}
        ]
        
        cursor = quiz_collection.aggregate(pipeline)
        quiz_stats = await cursor.to_list(length=None)
        
        # Format results
        formatted_stats = []
        for stat in quiz_stats:
            deck_info = stat["_id"]
            formatted_stats.append({
                "course_id": deck_info["course_id"],
                "deck_id": deck_info["deck_id"],
                "total_attempts": stat["total_attempts"],
                "average_score_percentage": round(stat["average_score"], 2),
                "highest_score_percentage": round(stat["highest_score"], 2),
                "lowest_score_percentage": round(stat["lowest_score"], 2),
                "average_time_seconds": round(stat["average_time"], 2),
                "average_total_questions": round(stat["total_questions_avg"], 1)
            })
        
        logger.info(f"Retrieved quiz performance summary for {len(formatted_stats)} decks")
        return formatted_stats
        
    except Exception as e:
        logger.error(f"Error getting quiz performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get quiz performance: {str(e)}")

@router.get("/flashcard-feedback/summary", response_model=List[Dict[str, Any]])
async def get_flashcard_feedback_summary(db = Depends(get_database)):
    """Get like/dislike counts per flashcard."""
    try:
        feedback_collection = db[settings.FLASHCARD_FEEDBACK_COLLECTION]
        
        # Aggregate feedback by flashcard
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "course_id": "$course_id",
                        "deck_id": "$deck_id",
                        "flashcard_index": "$flashcard_index"
                    },
                    "total_feedback": {"$sum": 1},
                    "likes": {
                        "$sum": {"$cond": [{"$eq": ["$rating", 1]}, 1, 0]}
                    },
                    "dislikes": {
                        "$sum": {"$cond": [{"$eq": ["$rating", -1]}, 1, 0]}
                    }
                }
            },
            {"$sort": {"total_feedback": -1}}
        ]
        
        cursor = feedback_collection.aggregate(pipeline)
        feedback_stats = await cursor.to_list(length=None)
        
        # Format results
        formatted_stats = []
        for stat in feedback_stats:
            flashcard_info = stat["_id"]
            net_score = stat["likes"] - stat["dislikes"]
            
            formatted_stats.append({
                "course_id": flashcard_info["course_id"],
                "deck_id": flashcard_info["deck_id"],
                "flashcard_index": flashcard_info["flashcard_index"],
                "flashcard_identifier": f"{flashcard_info['course_id']}:{flashcard_info['deck_id']}:{flashcard_info['flashcard_index']}",
                "total_feedback": stat["total_feedback"],
                "likes": stat["likes"],
                "dislikes": stat["dislikes"],
                "net_score": net_score
            })
        
        logger.info(f"Retrieved flashcard feedback summary for {len(formatted_stats)} flashcards")
        return formatted_stats
        
    except Exception as e:
        logger.error(f"Error getting flashcard feedback summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback summary: {str(e)}")

@router.get("/flashcard-feedback/details", response_model=List[Dict[str, Any]])
async def get_flashcard_feedback_details(db = Depends(get_database)):
    """Get raw feedback log with user/session info."""
    try:
        feedback_collection = db[settings.FLASHCARD_FEEDBACK_COLLECTION]
        
        # Get all feedback, sorted by most recent first
        cursor = feedback_collection.find({}).sort("created_at", -1)
        feedback_log = await cursor.to_list(length=None)
        
        # Format results
        formatted_feedback = []
        for feedback in feedback_log:
            formatted_feedback.append({
                "feedback_id": str(feedback["_id"]),
                "user_id": feedback["user_id"],
                "session_id": feedback["session_id"],
                "course_id": feedback["course_id"],
                "deck_id": feedback["deck_id"],
                "flashcard_index": feedback["flashcard_index"],
                "flashcard_identifier": f"{feedback['course_id']}:{feedback['deck_id']}:{feedback['flashcard_index']}",
                "rating": feedback["rating"],
                "rating_text": "like" if feedback["rating"] == 1 else "dislike",
                "created_at": feedback["created_at"]
            })
        
        logger.info(f"Retrieved {len(formatted_feedback)} feedback details")
        return formatted_feedback
        
    except Exception as e:
        logger.error(f"Error getting flashcard feedback details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback details: {str(e)}")

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_all_users_summary(db = Depends(get_database)):
    """Get all user summaries with activity stats."""
    try:
        users_collection = db[settings.USERS_COLLECTION]
        
        # Get all users, sorted by most recent activity
        cursor = users_collection.find({}).sort("last_active", -1)
        users = await cursor.to_list(length=None)
        
        # Format results
        formatted_users = []
        for user in users:
            formatted_users.append({
                "user_id": user["user_id"],
                "created_at": user["created_at"],
                "last_active": user["last_active"],
                "total_decks_studied": user.get("total_decks_studied", 0),
                "total_quiz_attempts": user.get("total_quiz_attempts", 0)
            })
        
        logger.info(f"Retrieved {len(formatted_users)} users summary")
        return formatted_users
        
    except Exception as e:
        logger.error(f"Error getting users summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users summary: {str(e)}")
