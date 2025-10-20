"""Bookmarks API endpoints for flashcard bookmarking."""

import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from app.database import get_database
from app.models.bookmark import Bookmark, BookmarkRequest, BookmarkResponse
from app.models.user import User
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])

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
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Add a flashcard to user's bookmarks."""
    logger.info(f"Attempting to add bookmark for user_id: {user_id}")
    try:
        # Ensure user exists
        await ensure_user_exists(user_id, db)
        
        # Check if bookmark already exists
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        existing_bookmark = await bookmarks_collection.find_one({
            "user_id": user_id,
            "course_id": bookmark_data.course_id,
            "deck_id": bookmark_data.deck_id,
            "flashcard_index": bookmark_data.flashcard_index
        })
        
        if existing_bookmark:
            raise HTTPException(status_code=409, detail="Flashcard already bookmarked")
        
        # Create new bookmark
        new_bookmark = Bookmark(
            user_id=user_id,
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
        
        logger.info(f"Added bookmark for user {user_id}: {bookmark_data.course_id}:{bookmark_data.deck_id}:{bookmark_data.flashcard_index}")
        
        return BookmarkResponse(
            user_id=created_doc["user_id"],
            course_id=created_doc["course_id"],
            deck_id=created_doc["deck_id"],
            flashcard_index=created_doc["flashcard_index"],
            created_at=created_doc["created_at"],
            flashcard_data=flashcard_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding bookmark for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add bookmark: {str(e)}")

@router.delete("")
async def remove_bookmark(
    bookmark_data: BookmarkRequest,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Remove a flashcard from user's bookmarks."""
    try:
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        
        # Find and delete the bookmark
        result = await bookmarks_collection.delete_one({
            "user_id": user_id,
            "course_id": bookmark_data.course_id,
            "deck_id": bookmark_data.deck_id,
            "flashcard_index": bookmark_data.flashcard_index
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
        logger.info(f"Removed bookmark for user {user_id}: {bookmark_data.course_id}:{bookmark_data.deck_id}:{bookmark_data.flashcard_index}")
        
        return {"message": "Bookmark removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing bookmark for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove bookmark: {str(e)}")

@router.get("", response_model=List[BookmarkResponse])
async def get_user_bookmarks(
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Get all bookmarks for a user."""
    logger.info(f"Fetching bookmarks for user_id: {user_id}")
    try:
        bookmarks_collection = db[settings.BOOKMARKS_COLLECTION]
        
        # Get all bookmarks for the user
        cursor = bookmarks_collection.find({"user_id": user_id}).sort("created_at", -1)
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
                user_id=bookmark["user_id"],
                course_id=bookmark["course_id"],
                deck_id=bookmark["deck_id"],
                flashcard_index=bookmark["flashcard_index"],
                created_at=bookmark["created_at"],
                flashcard_data=flashcard_data
            ))
        
        logger.info(f"Retrieved {len(bookmark_responses)} bookmarks for user {user_id}")
        
        return bookmark_responses
        
    except Exception as e:
        logger.error(f"Error getting bookmarks for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bookmarks: {str(e)}")
