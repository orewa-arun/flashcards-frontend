"""Bookmarks API endpoints for flashcard bookmarking using PostgreSQL."""

import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from app.db.postgres import get_postgres_pool
from app.models.bookmark import BookmarkRequest, BookmarkResponse
from app.firebase_auth import get_current_user
from app.services.user_service import UserService
from app.repositories.bookmark_feedback_repository import BookmarkFeedbackRepository
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])


async def load_flashcard_data(course_id: str, deck_id: str, flashcard_index: int) -> Optional[dict]:
    """Load flashcard data from JSON file."""
    try:
        import os
        # Construct path to flashcard JSON file - try _only variant first
        json_path = f"courses/{course_id}/cognitive_flashcards/{deck_id}/{deck_id}_cognitive_flashcards_only.json"
        
        # Fallback to full file if _only doesn't exist
        if not os.path.exists(json_path):
            json_path = f"courses/{course_id}/cognitive_flashcards/{deck_id}/{deck_id}_cognitive_flashcards.json"
        
        if not os.path.exists(json_path):
            logger.warning(f"Flashcard JSON file not found: {json_path}")
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        flashcards = data.get('flashcards', [])
        if 0 <= flashcard_index < len(flashcards):
            return flashcards[flashcard_index]
        else:
            logger.warning(f"Flashcard index {flashcard_index} out of range for deck {deck_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error loading flashcard data: {e}")
        return None


@router.post("", response_model=BookmarkResponse)
async def add_bookmark(
    bookmark_data: BookmarkRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a flashcard to user's bookmarks."""
    firebase_uid = current_user['uid']
    logger.info(f"Attempting to add bookmark for firebase_uid: {firebase_uid}")
    
    try:
        pool = await get_postgres_pool()
        
        # Ensure user exists in database
        user_service = UserService(pool)
        await user_service.get_or_create_user(
            firebase_uid=firebase_uid,
            email=current_user.get("email"),
            name=current_user.get("name"),
            picture=current_user.get("picture"),
            email_verified=current_user.get("email_verified", False)
        )
        
        # Check if bookmark already exists
        repository = BookmarkFeedbackRepository(pool)
        exists = await repository.bookmark_exists(
            firebase_uid=firebase_uid,
            course_id=bookmark_data.course_id,
            deck_id=bookmark_data.deck_id,
            flashcard_index=bookmark_data.flashcard_index
        )
        
        if exists:
            raise HTTPException(status_code=409, detail="Flashcard already bookmarked")
        
        # Create new bookmark
        created_bookmark = await repository.add_bookmark(
            firebase_uid=firebase_uid,
            course_id=bookmark_data.course_id,
            deck_id=bookmark_data.deck_id,
            flashcard_index=bookmark_data.flashcard_index
        )
        
        if not created_bookmark:
            raise HTTPException(status_code=409, detail="Flashcard already bookmarked")
        
        # Load flashcard data
        flashcard_data = await load_flashcard_data(
            bookmark_data.course_id,
            bookmark_data.deck_id,
            bookmark_data.flashcard_index
        )
        
        logger.info(f"Added bookmark for user {firebase_uid}: {bookmark_data.course_id}:{bookmark_data.deck_id}:{bookmark_data.flashcard_index}")
        
        return BookmarkResponse(
            firebase_uid=created_bookmark["firebase_uid"],
            course_id=created_bookmark["course_id"],
            deck_id=created_bookmark["deck_id"],
            flashcard_index=created_bookmark["flashcard_index"],
            created_at=created_bookmark["created_at"],
            flashcard_data=flashcard_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding bookmark for user {firebase_uid}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add bookmark: {str(e)}")


@router.delete("")
async def remove_bookmark(
    bookmark_data: BookmarkRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove a flashcard from user's bookmarks."""
    firebase_uid = current_user['uid']
    
    try:
        pool = await get_postgres_pool()
        repository = BookmarkFeedbackRepository(pool)
        
        # Find and delete the bookmark
        success = await repository.remove_bookmark(
            firebase_uid=firebase_uid,
            course_id=bookmark_data.course_id,
            deck_id=bookmark_data.deck_id,
            flashcard_index=bookmark_data.flashcard_index
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
        logger.info(f"Removed bookmark for user {firebase_uid}: {bookmark_data.course_id}:{bookmark_data.deck_id}:{bookmark_data.flashcard_index}")
        
        return {"message": "Bookmark removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing bookmark for user {firebase_uid}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove bookmark: {str(e)}")


@router.get("", response_model=List[BookmarkResponse])
async def get_user_bookmarks(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all bookmarks for a user."""
    firebase_uid = current_user['uid']
    logger.info(f"Fetching bookmarks for firebase_uid: {firebase_uid}")
    
    try:
        pool = await get_postgres_pool()
        repository = BookmarkFeedbackRepository(pool)
        
        # Get all bookmarks for the user
        bookmarks = await repository.get_user_bookmarks(firebase_uid)
        
        # Load flashcard data for each bookmark
        bookmark_responses = []
        for bookmark in bookmarks:
            flashcard_data = await load_flashcard_data(
                bookmark["course_id"],
                bookmark["deck_id"],
                bookmark["flashcard_index"]
            )
            
            bookmark_responses.append(BookmarkResponse(
                firebase_uid=bookmark["firebase_uid"],
                course_id=bookmark["course_id"],
                deck_id=bookmark["deck_id"],
                flashcard_index=bookmark["flashcard_index"],
                created_at=bookmark["created_at"],
                flashcard_data=flashcard_data
            ))
        
        logger.info(f"Retrieved {len(bookmark_responses)} bookmarks for user {firebase_uid}")
        
        return bookmark_responses
        
    except Exception as e:
        logger.error(f"Error getting bookmarks for user {firebase_uid}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bookmarks: {str(e)}")
