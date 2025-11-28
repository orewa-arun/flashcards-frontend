"""Feedback API endpoints for flashcard like/dislike tracking using PostgreSQL."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from app.db.postgres import get_postgres_pool
from app.models.feedback import FeedbackRequest, FeedbackResponse, UserFeedbackSummary
from app.firebase_auth import get_current_user
from app.repositories.bookmark_feedback_repository import BookmarkFeedbackRepository
from app.repositories.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


async def ensure_user_exists(firebase_uid: str, pool) -> dict:
    """Ensure user exists in database, create if not. For Firebase authenticated users."""
    repository = UserRepository(pool)
    return await repository.get_or_create_user(firebase_uid=firebase_uid)


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit or update feedback for a flashcard."""
    try:
        user_id = current_user['uid']
        logger.info(f"Received feedback submission: {feedback_data.model_dump()}")
        
        # Validate rating
        if feedback_data.rating not in [1, -1]:
            raise HTTPException(status_code=400, detail="Rating must be 1 (like) or -1 for dislike)")
        
        pool = await get_postgres_pool()
        
        # Ensure user exists
        await ensure_user_exists(user_id, pool)
        
        # Submit feedback
        repository = BookmarkFeedbackRepository(pool)
        feedback_doc = await repository.submit_feedback(
            user_id=user_id,
            course_id=feedback_data.course_id,
            deck_id=feedback_data.deck_id,
            flashcard_index=feedback_data.flashcard_index,
            rating=feedback_data.rating,
            session_id=feedback_data.session_id
        )
        
        logger.info(f"Submitted feedback for user {user_id}: {feedback_data.course_id}:{feedback_data.deck_id}:{feedback_data.flashcard_index} = {feedback_data.rating}")
        
        return FeedbackResponse(
            user_id=feedback_doc["user_id"],
            course_id=feedback_doc["course_id"],
            deck_id=feedback_doc["deck_id"],
            flashcard_index=feedback_doc["flashcard_index"],
            session_id=feedback_doc["session_id"],
            rating=feedback_doc["rating"],
            created_at=feedback_doc["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.get("/user", response_model=List[UserFeedbackSummary])
async def get_user_feedback(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all feedback for a user."""
    user_id: str | None = None
    try:
        user_id = current_user['uid']
        
        pool = await get_postgres_pool()
        repository = BookmarkFeedbackRepository(pool)
        
        # Get all feedback for the user
        feedback_list = await repository.get_user_feedback(user_id)
        
        # Convert to response format
        feedback_summaries = []
        for feedback in feedback_list:
            feedback_summaries.append(UserFeedbackSummary(
                course_id=feedback["course_id"],
                deck_id=feedback["deck_id"],
                flashcard_index=feedback["flashcard_index"],
                rating=feedback["rating"]
            ))
        
        logger.info(f"Retrieved {len(feedback_summaries)} feedback items for user {user_id}")
        
        return feedback_summaries
        
    except Exception as e:
        logger.error(f"Error getting feedback for user {user_id or 'unknown'}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


@router.delete("")
async def clear_feedback(
    feedback_data: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear/remove feedback for a specific flashcard."""
    try:
        user_id = current_user['uid']
        
        pool = await get_postgres_pool()
        repository = BookmarkFeedbackRepository(pool)
        
        # Find and delete the feedback
        success = await repository.clear_feedback(
            user_id=user_id,
            course_id=feedback_data.course_id,
            deck_id=feedback_data.deck_id,
            flashcard_index=feedback_data.flashcard_index
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        logger.info(f"Cleared feedback for user {user_id}: {feedback_data.course_id}:{feedback_data.deck_id}:{feedback_data.flashcard_index}")
        
        return {"message": "Feedback cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing feedback for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear feedback: {str(e)}")
