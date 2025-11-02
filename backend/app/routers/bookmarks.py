"""Bookmarks API endpoints for flashcard bookmarking."""

import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.database import get_database
from app.models.bookmark import Bookmark, BookmarkRequest, BookmarkResponse
from app.config import settings
from app.firebase_auth import get_current_user
from app.services import user_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])

async def load_flashcard_data(course_id: str, deck_id: str, flashcard_index: int) -> Optional[dict]:
    """Load flashcard data from JSON file."""
    try:
        import os
        # Construct path to flashcard JSON file
        json_path = f"courses/{course_id}/cognitive_flashcards/{deck_id}/{deck_id}_cognitive_flashcards.json"
        # json_path = "../"
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Add a flashcard to user's bookmarks."""
    firebase_uid = current_user['uid']
    logger.info(f"Attempting to add bookmark for firebase_uid: {firebase_uid}")
    try:
        # Ensure user exists in database
        await user_service.get_or_create_user(current_user, db)
        
        # Check if bookmark already exists
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        existing_bookmark = await bookmarks_collection.find_one({
            "firebase_uid": firebase_uid,
            "course_id": bookmark_data.course_id,
            "deck_id": bookmark_data.deck_id,
            "flashcard_index": bookmark_data.flashcard_index
        })
        
        if existing_bookmark:
            raise HTTPException(status_code=409, detail="Flashcard already bookmarked")
        
        # Create new bookmark
        new_bookmark = Bookmark(
            firebase_uid=firebase_uid,
            course_id=bookmark_data.course_id,
            deck_id=bookmark_data.deck_id,
            flashcard_index=bookmark_data.flashcard_index
        )
        
        # Save to database
        result = await bookmarks_collection.insert_one(
            new_bookmark.model_dump(by_alias=True, exclude={"id"})
        )
        
        # Get created document
        created_doc = await bookmarks_collection.find_one({"_id": result.inserted_id})
        
        # Load flashcard data
        flashcard_data = await load_flashcard_data(
            bookmark_data.course_id,
            bookmark_data.deck_id,
            bookmark_data.flashcard_index
        )
        
        logger.info(f"Added bookmark for user {firebase_uid}: {bookmark_data.course_id}:{bookmark_data.deck_id}:{bookmark_data.flashcard_index}")
        
        return BookmarkResponse(
            firebase_uid=created_doc["firebase_uid"],
            course_id=created_doc["course_id"],
            deck_id=created_doc["deck_id"],
            flashcard_index=created_doc["flashcard_index"],
            created_at=created_doc["created_at"],
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Remove a flashcard from user's bookmarks."""
    firebase_uid = current_user['uid']
    try:
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        
        # Find and delete the bookmark
        result = await bookmarks_collection.delete_one({
            "firebase_uid": firebase_uid,
            "course_id": bookmark_data.course_id,
            "deck_id": bookmark_data.deck_id,
            "flashcard_index": bookmark_data.flashcard_index
        })
        
        if result.deleted_count == 0:
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
    current_user: Dict[str, Any] = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all bookmarks for a user."""
    firebase_uid = current_user['uid']
    logger.info(f"Fetching bookmarks for firebase_uid: {firebase_uid}")
    try:
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        
        # Get all bookmarks for the user
        cursor = bookmarks_collection.find({"firebase_uid": firebase_uid}).sort("created_at", -1)
        bookmarks = await cursor.to_list(length=None)
        
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
