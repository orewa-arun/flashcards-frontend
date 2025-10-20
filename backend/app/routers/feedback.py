"""Feedback API endpoints for flashcard like/dislike tracking."""

from typing import List
from fastapi import APIRouter, HTTPException, Header, Depends
from app.database import get_database
from app.models.feedback import FlashcardFeedback, FeedbackRequest, FeedbackResponse, UserFeedbackSummary
from app.models.user import User
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

async def get_user_id_from_header(x_user_id: str = Header(..., alias="X-User-ID")) -> str:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header is required")
    return x_user_id

async def ensure_user_exists(user_id: str, db) -> User:
    """Ensure user exists in database, create if not."""
    users_collection = db[settings.USERS_COLLECTION]
    
    # Check if user exists
    user_doc = await users_collection.find_one({"user_id": user_id})
    
    if not user_doc:
        # Create new user
        from datetime import datetime, timezone
        new_user = User(user_id=user_id)
        result = await users_collection.insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))
        
        # Fetch the created user
        user_doc = await users_collection.find_one({"_id": result.inserted_id})
        logger.info(f"Created new user: {user_id}")
    else:
        # Update last_active
        from datetime import datetime, timezone
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}}
        )
    
    return User(**user_doc)

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_data: FeedbackRequest,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Submit or update feedback for a flashcard."""
    try:
        # Validate rating
        if feedback_data.rating not in [1, -1]:
            raise HTTPException(status_code=400, detail="Rating must be 1 (like) or -1 (dislike)")
        
        # Ensure user exists
        await ensure_user_exists(user_id, db)
        
        feedback_collection = db[settings.FLASHCARD_FEEDBACK_COLLECTION]
        
        # Check if feedback already exists for this user and flashcard
        existing_feedback = await feedback_collection.find_one({
            "user_id": user_id,
            "course_id": feedback_data.course_id,
            "deck_id": feedback_data.deck_id,
            "flashcard_index": feedback_data.flashcard_index
        })
        
        if existing_feedback:
            # Update existing feedback
            await feedback_collection.update_one(
                {
                    "user_id": user_id,
                    "course_id": feedback_data.course_id,
                    "deck_id": feedback_data.deck_id,
                    "flashcard_index": feedback_data.flashcard_index
                },
                {
                    "$set": {
                        "rating": feedback_data.rating,
                        "session_id": feedback_data.session_id,
                        "created_at": feedback_data.created_at if hasattr(feedback_data, 'created_at') else existing_feedback["created_at"]
                    }
                }
            )
            
            # Get updated document
            updated_doc = await feedback_collection.find_one({
                "user_id": user_id,
                "course_id": feedback_data.course_id,
                "deck_id": feedback_data.deck_id,
                "flashcard_index": feedback_data.flashcard_index
            })
            
            logger.info(f"Updated feedback for user {user_id}: {feedback_data.course_id}:{feedback_data.deck_id}:{feedback_data.flashcard_index} = {feedback_data.rating}")
            
        else:
            # Create new feedback
            new_feedback = FlashcardFeedback(
                user_id=user_id,
                session_id=feedback_data.session_id,
                course_id=feedback_data.course_id,
                deck_id=feedback_data.deck_id,
                flashcard_index=feedback_data.flashcard_index,
                rating=feedback_data.rating
            )
            
            # Save to database
            result = await feedback_collection.insert_one(
                new_feedback.model_dump(by_alias=True, exclude={"id"})
            )
            
            # Get created document
            updated_doc = await feedback_collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Created feedback for user {user_id}: {feedback_data.course_id}:{feedback_data.deck_id}:{feedback_data.flashcard_index} = {feedback_data.rating}")
        
        return FeedbackResponse(
            user_id=updated_doc["user_id"],
            course_id=updated_doc["course_id"],
            deck_id=updated_doc["deck_id"],
            flashcard_index=updated_doc["flashcard_index"],
            session_id=updated_doc["session_id"],
            rating=updated_doc["rating"],
            created_at=updated_doc["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/user", response_model=List[UserFeedbackSummary])
async def get_user_feedback(
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Get all feedback for a user."""
    try:
        feedback_collection = db[settings.FLASHCARD_FEEDBACK_COLLECTION]
        
        # Get all feedback for the user
        cursor = feedback_collection.find({"user_id": user_id}).sort("created_at", -1)
        feedback_list = await cursor.to_list(length=None)
        
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
        logger.error(f"Error getting feedback for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")

@router.delete("")
async def clear_feedback(
    feedback_data: FeedbackRequest,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Clear/remove feedback for a specific flashcard."""
    try:
        feedback_collection = db[settings.FLASHCARD_FEEDBACK_COLLECTION]
        
        # Find and delete the feedback
        result = await feedback_collection.delete_one({
            "user_id": user_id,
            "course_id": feedback_data.course_id,
            "deck_id": feedback_data.deck_id,
            "flashcard_index": feedback_data.flashcard_index
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        logger.info(f"Cleared feedback for user {user_id}: {feedback_data.course_id}:{feedback_data.deck_id}:{feedback_data.flashcard_index}")
        
        return {"message": "Feedback cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing feedback for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear feedback: {str(e)}")
