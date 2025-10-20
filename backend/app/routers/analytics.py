"""Analytics API endpoints for user tracking."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from app.database import get_database
from app.models.user import User, UserSummary
from app.models.progress import DeckProgress, ProgressUpdate, ProgressResponse
from app.models.quiz import QuizResult, QuizSubmission, QuizResultResponse
from app.models.session import (
    StudySession, SessionStartRequest, SessionStartResponse,
    SessionUpdateRequest, SessionUpdateResponse, SessionSummaryResponse
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

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
        new_user = User(user_id=user_id)
        result = await users_collection.insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))
        
        # Fetch the created user
        user_doc = await users_collection.find_one({"_id": result.inserted_id})
        logger.info(f"Created new user: {user_id}")
    else:
        # Update last_active
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}}
        )
    
    return User(**user_doc)

@router.post("/progress", response_model=ProgressResponse)
async def update_deck_progress(
    progress_data: ProgressUpdate,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Update user's deck study progress."""
    try:
        # Ensure user exists
        await ensure_user_exists(user_id, db)
        
        # Update progress
        progress_collection = db[settings.DECK_PROGRESS_COLLECTION]
        
        # Check if progress already exists for this deck
        existing_progress = await progress_collection.find_one({
            "user_id": user_id,
            "deck_id": progress_data.deck_id
        })
        
        if existing_progress:
            # Update existing progress
            update_data = {
                "progress": progress_data.progress,
                "cards_studied": progress_data.cards_studied,
                "total_cards": progress_data.total_cards,
                "last_studied": datetime.now(timezone.utc)
            }
            
            # Update study streak if studied today
            last_studied = existing_progress.get("last_studied")
            now = datetime.now(timezone.utc)
            
            # Handle timezone awareness for study streak calculation
            if last_studied:
                # Ensure last_studied is timezone-aware to avoid comparison errors
                if last_studied.tzinfo is None:
                    last_studied = last_studied.replace(tzinfo=timezone.utc)
                
                days_diff = (now - last_studied).days
                if days_diff == 1:
                    update_data["study_streak"] = existing_progress.get("study_streak", 0) + 1
                elif days_diff > 1:
                    update_data["study_streak"] = 1
                # If days_diff == 0, same day, keep current streak
            else:
                update_data["study_streak"] = 1
            
            await progress_collection.update_one(
                {"user_id": user_id, "deck_id": progress_data.deck_id},
                {"$set": update_data}
            )
            
            # Get updated document
            updated_doc = await progress_collection.find_one({
                "user_id": user_id,
                "deck_id": progress_data.deck_id
            })
            
        else:
            # Create new progress entry
            new_progress = DeckProgress(
                user_id=user_id,
                deck_id=progress_data.deck_id,
                course_id=progress_data.course_id,
                progress=progress_data.progress,
                cards_studied=progress_data.cards_studied,
                total_cards=progress_data.total_cards,
                study_streak=1
            )
            
            result = await progress_collection.insert_one(
                new_progress.model_dump(by_alias=True, exclude={"id"})
            )
            
            # Get created document
            updated_doc = await progress_collection.find_one({"_id": result.inserted_id})
            
            # Update user's total decks studied
            users_collection = db[settings.USERS_COLLECTION]
            await users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"total_decks_studied": 1}}
            )
        
        # Return response
        return ProgressResponse(
            user_id=updated_doc["user_id"],
            deck_id=updated_doc["deck_id"],
            course_id=updated_doc["course_id"],
            progress=updated_doc["progress"],
            cards_studied=updated_doc["cards_studied"],
            total_cards=updated_doc["total_cards"],
            last_studied=updated_doc["last_studied"],
            study_streak=updated_doc["study_streak"]
        )
        
    except Exception as e:
        logger.error(f"Error updating progress for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

@router.post("/quiz-result", response_model=QuizResultResponse)
async def submit_quiz_result(
    quiz_data: QuizSubmission,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Submit quiz result for a user."""
    try:
        # Ensure user exists
        await ensure_user_exists(user_id, db)
        
        # Calculate percentage
        percentage = (quiz_data.score / quiz_data.total_questions) * 100
        
        # Create quiz result
        quiz_result = QuizResult(
            user_id=user_id,
            deck_id=quiz_data.deck_id,
            course_id=quiz_data.course_id,
            score=quiz_data.score,
            total_questions=quiz_data.total_questions,
            percentage=percentage,
            time_taken=quiz_data.time_taken,
            question_results=quiz_data.question_results or []
        )
        
        # Save to database
        quiz_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        result = await quiz_collection.insert_one(
            quiz_result.model_dump(by_alias=True, exclude={"id"})
        )
        
        # Update user's total quiz attempts
        users_collection = db[settings.USERS_COLLECTION]
        await users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"total_quiz_attempts": 1}}
        )
        
        # Get created document
        created_doc = await quiz_collection.find_one({"_id": result.inserted_id})
        
        logger.info(f"Quiz result saved for user {user_id}, deck {quiz_data.deck_id}: {quiz_data.score}/{quiz_data.total_questions}")
        
        return QuizResultResponse(
            user_id=created_doc["user_id"],
            deck_id=created_doc["deck_id"],
            course_id=created_doc["course_id"],
            score=created_doc["score"],
            total_questions=created_doc["total_questions"],
            percentage=created_doc["percentage"],
            time_taken=created_doc["time_taken"],
            completed_at=created_doc["completed_at"]
        )
        
    except Exception as e:
        logger.error(f"Error submitting quiz result for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz result: {str(e)}")

@router.get("/user/{user_id}", response_model=UserSummary)
async def get_user_summary(user_id: str, db = Depends(get_database)):
    """Get user summary statistics."""
    try:
        users_collection = db[settings.USERS_COLLECTION]
        user_doc = await users_collection.find_one({"user_id": user_id})
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserSummary(
            user_id=user_doc["user_id"],
            total_decks_studied=user_doc.get("total_decks_studied", 0),
            total_quiz_attempts=user_doc.get("total_quiz_attempts", 0),
            created_at=user_doc["created_at"],
            last_active=user_doc["last_active"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user summary for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user summary: {str(e)}")

# =============================================================================
# SESSION TRACKING ENDPOINTS
# =============================================================================

@router.post("/session/start", response_model=SessionStartResponse)
async def start_study_session(
    session_request: SessionStartRequest,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Start a new study session."""
    try:
        # Ensure user exists
        await ensure_user_exists(user_id, db)
        
        # Create new session
        new_session = StudySession(
            user_id=user_id,
            course_id=session_request.course_id,
            deck_id=session_request.deck_id
        )
        
        # Save to database
        sessions_collection = db[settings.STUDY_SESSIONS_COLLECTION]
        result = await sessions_collection.insert_one(
            new_session.model_dump(by_alias=True, exclude={"id"})
        )
        
        logger.info(f"Started new study session: {new_session.session_id} for user {user_id}, deck {session_request.deck_id}")
        
        return SessionStartResponse(
            session_id=new_session.session_id,
            message="Study session started successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting session for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@router.post("/session/update", response_model=SessionUpdateResponse)
async def update_study_session(
    update_request: SessionUpdateRequest,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Update an existing study session with study duration or quiz results."""
    try:
        sessions_collection = db[settings.STUDY_SESSIONS_COLLECTION]
        
        # Find the session
        session_doc = await sessions_collection.find_one({
            "session_id": update_request.session_id,
            "user_id": user_id
        })
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Prepare update data
        update_data = {}
        
        # Update study duration if provided
        if update_request.study_duration_seconds is not None:
            update_data["study_duration_seconds"] = update_request.study_duration_seconds
            logger.info(f"Updated study duration for session {update_request.session_id}: {update_request.study_duration_seconds}s")
        
        # Update quiz data if provided
        if update_request.quiz_data is not None:
            quiz_data_dict = update_request.quiz_data.model_dump(exclude_none=True)
            
            # Calculate percentage if score and total_questions are provided
            if quiz_data_dict.get("score") is not None and quiz_data_dict.get("total_questions") is not None:
                quiz_data_dict["percentage"] = (quiz_data_dict["score"] / quiz_data_dict["total_questions"]) * 100
            
            update_data["quiz_data"] = quiz_data_dict
            logger.info(f"Updated quiz data for session {update_request.session_id}: {quiz_data_dict.get('score', 0)}/{quiz_data_dict.get('total_questions', 0)}")
        
        # Update completion status if provided
        if update_request.is_completed is not None:
            update_data["is_completed"] = update_request.is_completed
            if update_request.is_completed:
                update_data["completed_at"] = datetime.now(timezone.utc)
        
        # Perform the update
        await sessions_collection.update_one(
            {"session_id": update_request.session_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        # Get updated document
        updated_doc = await sessions_collection.find_one({
            "session_id": update_request.session_id,
            "user_id": user_id
        })
        
        # Calculate total session time if both study and quiz durations are available
        total_session_time = None
        study_duration = updated_doc.get("study_duration_seconds")
        quiz_duration = updated_doc.get("quiz_data", {}).get("quiz_duration_seconds")
        
        if study_duration is not None and quiz_duration is not None:
            total_session_time = study_duration + quiz_duration
        
        return SessionUpdateResponse(
            session_id=updated_doc["session_id"],
            user_id=updated_doc["user_id"],
            course_id=updated_doc["course_id"],
            deck_id=updated_doc["deck_id"],
            study_duration_seconds=updated_doc.get("study_duration_seconds"),
            quiz_data=updated_doc.get("quiz_data", {}),
            is_completed=updated_doc.get("is_completed", False),
            total_session_time_seconds=total_session_time,
            message="Session updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {update_request.session_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@router.get("/session/{session_id}", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: str,
    user_id: str = Depends(get_user_id_from_header),
    db = Depends(get_database)
):
    """Get complete summary of a study session."""
    try:
        sessions_collection = db[settings.STUDY_SESSIONS_COLLECTION]
        
        session_doc = await sessions_collection.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")
        
        quiz_data = session_doc.get("quiz_data", {})
        study_duration = session_doc.get("study_duration_seconds")
        quiz_duration = quiz_data.get("quiz_duration_seconds")
        
        # Calculate total session time
        total_session_time = None
        if study_duration is not None and quiz_duration is not None:
            total_session_time = study_duration + quiz_duration
        
        return SessionSummaryResponse(
            session_id=session_doc["session_id"],
            user_id=session_doc["user_id"],
            course_id=session_doc["course_id"],
            deck_id=session_doc["deck_id"],
            session_start_time=session_doc["session_start_time"],
            study_duration_seconds=study_duration,
            quiz_duration_seconds=quiz_duration,
            total_session_time_seconds=total_session_time,
            quiz_score=quiz_data.get("score"),
            quiz_total_questions=quiz_data.get("total_questions"),
            quiz_percentage=quiz_data.get("percentage"),
            is_completed=session_doc.get("is_completed", False),
            completed_at=session_doc.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session summary {session_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session summary: {str(e)}")
