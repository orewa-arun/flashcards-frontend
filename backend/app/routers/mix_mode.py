"""API endpoints for Mix Mode adaptive study sessions."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_database
from app.firebase_auth import get_current_user
from app.models.mix_session import (
    MixSessionStartRequest,
    MixSessionStartResponse,
    MixActivityResponse,
    MixAnswerSubmission,
    MixAnswerResponse,
    DeckReadinessRequest
)
from app.models.readiness_v2 import UserExamReadiness
from app.services.mix_session_service import MixSessionService
from app.services.readiness_v2_service import ReadinessV2Service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mix", tags=["Mix Mode"])


@router.post("/start", response_model=MixSessionStartResponse)
async def start_mix_session(
    request: MixSessionStartRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Start a new mix mode study session.
    
    Mix mode provides an adaptive study experience that:
    - Prioritizes important concepts (high relevance_score)
    - Starts with medium-level questions
    - Provides immediate remediation for incorrect answers
    - Adapts question difficulty based on user performance
    - Can span multiple decks for exam preparation
    
    Args:
        request: Contains course_id and deck_ids
        user_id: Firebase UID from JWT token
        db: Database connection
        
    Returns:
        Session ID and total flashcard count
        
    Raises:
        HTTPException: If decks are not found or invalid
    """
    try:
        user_id = current_user['uid']
        service = MixSessionService(db)
        session_id, total_flashcards = await service.start_session(
            user_id=user_id,
            course_id=request.course_id,
            deck_ids=request.deck_ids
        )
        
        logger.info(f"User {user_id} started mix session {session_id}")
        
        return MixSessionStartResponse(
            session_id=session_id,
            total_flashcards=total_flashcards
        )
    except ValueError as e:
        logger.error(f"Error starting mix session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error starting mix session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start mix session"
        )


@router.get("/session/{session_id}/next", response_model=Optional[MixActivityResponse])
async def get_next_activity(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Get the next activity in the mix session.
    
    Activities can be:
    - A question to answer (with difficulty level)
    - A flashcard to review (for remediation)
    
    The session automatically progresses through rounds, with each round
    covering all flashcards. Question difficulty adapts based on the user's
    Comfortability Score (CS).
    
    Args:
        session_id: The session identifier
        user_id: Firebase UID from JWT token
        db: Database connection
        
    Returns:
        Next activity details or None if session is complete
        
    Raises:
        HTTPException: If session not found or permission denied
    """
    try:
        user_id = current_user['uid']
        service = MixSessionService(db)
        activity = await service.get_next_activity(
            session_id=session_id,
            user_id=user_id
        )
        
        return activity
    except ValueError as e:
        logger.error(f"Error getting next activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting next activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get next activity"
        )


@router.post("/session/{session_id}/answer", response_model=MixAnswerResponse)
async def submit_answer(
    session_id: str,
    answer: MixAnswerSubmission,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Submit an answer for grading and update performance.
    
    The system will:
    - Grade the answer (supporting partial credit for MCA)
    - Update flashcard performance and Comfortability Score
    - Track question-level performance
    - Inject remediation (flashcard review + follow-up question) if incorrect
    
    Follow-up questions (from remediation) do not trigger additional remediation
    to avoid infinite loops.
    
    Args:
        session_id: The session identifier
        answer: Answer submission details
        user_id: Firebase UID from JWT token
        db: Database connection
        
    Returns:
        Grading results including correctness and points earned
        
    Raises:
        HTTPException: If session not found or submission invalid
    """
    try:
        user_id = current_user['uid']
        service = MixSessionService(db)
        
        # For now, we need to fetch the correct answer
        # In a real implementation, this would come from loading the question
        # Let's load the question to get the correct answer
        session_doc = await db.mix_sessions.find_one({"session_id": session_id})
        if not session_doc:
            raise ValueError(f"Session {session_id} not found")
        
        # Load the question to get correct answer
        from app.services.adaptive_quiz_service import AdaptiveQuizService
        quiz_service = AdaptiveQuizService()
        
        # Map level to file number
        level_map = {"easy": 1, "medium": 2, "hard": 3, "boss": 4}
        level_num = level_map.get(answer.level, 2)
        
        # Extract deck_id from flashcard_id
        parts = answer.flashcard_id.rsplit("_", 1)
        deck_id = parts[0] if len(parts) > 1 else answer.flashcard_id
        
        # Load questions
        questions = await quiz_service.load_quiz_questions(
            session_doc["course_id"],
            deck_id,
            level_num
        )
        
        # Find the question by hash
        correct_answer = None
        question_text = None
        explanation = None
        for q in questions:
            if service._hash_question(q["question_text"]) == answer.question_hash:
                correct_answer = q["correct_answer"]
                question_text = q["question_text"]
                explanation = q.get("explanation", "")
                break
        
        if correct_answer is None:
            raise ValueError("Question not found")
        
        # Submit answer
        result = await service.submit_answer(
            session_id=session_id,
            user_id=user_id,
            flashcard_id=answer.flashcard_id,
            question_hash=answer.question_hash,
            level=answer.level,
            user_answer=answer.user_answer,
            correct_answer=correct_answer,
            is_follow_up=answer.is_follow_up
        )
        
        # Add explanation to the result
        result.explanation = explanation
        
        logger.info(
            f"User {user_id} answered question in session {session_id}: "
            f"{'correct' if result.is_correct else 'incorrect'}, "
            f"points: {result.points_earned}"
        )
        
        return result
    except ValueError as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error submitting answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answer"
        )


@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Get the current status of a mix session.
    
    Returns progress information including:
    - Current round number
    - Questions answered in current round
    - Total flashcards
    - Session status
    
    Args:
        session_id: The session identifier
        user_id: Firebase UID from JWT token
        db: Database connection
        
    Returns:
        Session status and progress information
    """
    try:
        user_id = current_user['uid']
        session_doc = await db.mix_sessions.find_one({"session_id": session_id})
        if not session_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify ownership
        if session_doc["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to this user"
            )
        
        return {
            "session_id": session_id,
            "status": session_doc["status"],
            "current_round": session_doc.get("current_round", 1),
            "total_flashcards": len(session_doc["flashcard_master_order"]),
            "seen_in_current_round": len(session_doc.get("seen_in_current_round", [])),
            "activities_remaining": len(session_doc.get("activity_queue", [])),
            "created_at": session_doc["created_at"],
            "last_updated": session_doc["last_updated"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session status"
        )


@router.post("/deck-readiness", response_model=UserExamReadiness)
async def get_deck_exam_readiness(
    request: DeckReadinessRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    """
    Get exam readiness score for one or more decks.
    
    This endpoint calculates the user's exam readiness based on their
    performance across the specified decks. The score aggregates:
    - Coverage: How many flashcards have been attempted
    - Accuracy: How well questions have been answered (weighted by difficulty)
    - Momentum: Recent performance trend
    
    The calculation is cached for 30 seconds to optimize real-time updates
    during Mix Mode sessions.
    
    Args:
        request: Contains course_id, deck_ids, and optional force_refresh flag
        current_user: Firebase user from JWT token
        db: Database connection
        
    Returns:
        UserExamReadiness with overall score and Trinity breakdown
        
    Raises:
        HTTPException: If decks are not found or calculation fails
    """
    try:
        user_id = current_user['uid']
        readiness_service = ReadinessV2Service(db)
        
        # Get or calculate deck readiness
        readiness = await readiness_service.get_or_calculate_deck_readiness(
            user_id=user_id,
            course_id=request.course_id,
            deck_ids=request.deck_ids,
            force_refresh=request.force_refresh
        )
        
        logger.info(
            f"Deck readiness for user {user_id}, decks {request.deck_ids}: "
            f"{readiness.overall_readiness_score:.1f}%"
        )
        
        return readiness
    except ValueError as e:
        logger.error(f"Error calculating deck readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error calculating deck readiness: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate deck readiness"
        )

