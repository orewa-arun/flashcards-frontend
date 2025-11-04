"""API endpoints for adaptive quiz system."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.database import get_database
from app.firebase_auth import get_current_user
from app.models.user_performance import QuizSessionRequest, QuizAnswerSubmission, QuizSessionCompletion
from app.services.user_performance_service import UserPerformanceService
from app.services.adaptive_quiz_service import AdaptiveQuizService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quiz", tags=["adaptive-quiz"])


@router.post("/session/start")
async def start_quiz_session(
    request: QuizSessionRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Start an adaptive quiz session.
    
    Returns a personalized set of questions based on the user's performance history.
    
    Args:
        request: Quiz session configuration
        current_user: Authenticated user from Firebase
        db: MongoDB database connection
        
    Returns:
        {
            "questions": [...],  # List of question objects
            "metadata": {
                "total_questions": 20,
                "level": 1,
                "course_id": "MS5150",
                "lecture_id": "SI_PLC"
            }
        }
    """
    try:
        user_id = current_user['uid']
        
        # Initialize services
        performance_service = UserPerformanceService(db)
        quiz_service = AdaptiveQuizService()
        
        # Get user's weakness scores for this lecture
        weakness_scores = await performance_service.calculate_weakness_scores(
            user_id,
            request.course_id,
            request.lecture_id
        )
        
        # Get already attempted questions
        attempted_questions = await performance_service.get_attempted_questions(
            user_id,
            request.course_id,
            request.lecture_id
        )
        
        # Get seen flashcard IDs for coverage-first algorithm
        seen_flashcard_ids = await performance_service.get_seen_flashcard_ids(
            user_id,
            request.course_id,
            request.lecture_id
        )
        
        logger.info(f"User {user_id}: {len(weakness_scores)} tracked flashcards, "
                   f"{len(attempted_questions)} attempted questions, "
                   f"{len(seen_flashcard_ids)} seen concepts")
        
        # Generate adaptive quiz session with coverage-first approach
        selected_questions = await quiz_service.generate_quiz_session(
            course_id=request.course_id,
            lecture_id=request.lecture_id,
            level=request.level,
            weakness_scores=weakness_scores,
            attempted_questions=attempted_questions,
            seen_flashcard_ids=seen_flashcard_ids,
            size=None  # Let service compute adaptive session size based on total
        )
        
        if not selected_questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No questions found for {request.course_id}/{request.lecture_id}/level_{request.level}"
            )
        
        return {
            "questions": selected_questions,
            "metadata": {
                "total_questions": len(selected_questions),
                "level": request.level,
                "course_id": request.course_id,
                "lecture_id": request.lecture_id,
                "user_id": user_id
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting quiz session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start quiz session: {str(e)}"
        )


@router.post("/session/submit")
async def submit_quiz_answer(
    submission: QuizAnswerSubmission,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Submit an answer to a quiz question.
    
    Updates the user's performance metrics in the database.
    
    Args:
        submission: Answer submission data
        current_user: Authenticated user from Firebase
        db: MongoDB database connection
        
    Returns:
        {
            "success": true,
            "message": "Answer recorded successfully"
        }
    """
    try:
        user_id = current_user['uid']
        
        # Initialize service
        performance_service = UserPerformanceService(db)
        
        # Record the answer
        success = await performance_service.record_answer(
            user_id=user_id,
            course_id=submission.course_id,
            lecture_id=submission.lecture_id,
            question_hash=submission.question_hash,
            flashcard_id=submission.flashcard_id,
            is_correct=submission.is_correct
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record answer"
            )
        
        logger.info(f"User {user_id} answered question {submission.question_hash}: "
                   f"{'correct' if submission.is_correct else 'incorrect'}")
        
        return {
            "success": True,
            "message": "Answer recorded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit answer: {str(e)}"
        )


@router.post("/session/complete")
async def complete_quiz_session(
    completion: QuizSessionCompletion,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Complete a quiz session and save it to quiz history.
    
    This endpoint saves the completed quiz attempt to the quiz_results collection,
    making it available in the quiz history view.
    
    Args:
        completion: Quiz session completion data
        current_user: Authenticated user from Firebase
        db: MongoDB database connection
        
    Returns:
        {
            "success": true,
            "result_id": "...",
            "message": "Quiz session saved to history"
        }
    """
    try:
        from datetime import datetime
        from app.config import settings
        
        user_id = current_user['uid']
        
        # Calculate percentage
        percentage = round((completion.score / completion.total_questions * 100), 2) if completion.total_questions > 0 else 0
        
        # Create the deck_id from lecture_id and level
        deck_id = f"{completion.lecture_id}"
        
        # Prepare quiz result document matching the old quiz system format
        quiz_result_document = {
            "firebase_uid": user_id,
            "course_id": completion.course_id,
            "deck_id": deck_id,
            "difficulty": f"level_{completion.level}",
            "score": completion.score,
            "total_questions": completion.total_questions,
            "percentage": percentage,
            "time_taken": completion.time_taken_seconds,
            "completed_at": datetime.utcnow().isoformat(),
            "question_results": [
                {
                    "question": result.question_text,
                    "user_answer": result.user_answer,
                    "correct_answer": result.correct_answer,
                    "is_correct": result.is_correct,
                    "explanation": result.explanation,
                    "source_flashcard_id": result.source_flashcard_id,
                    "question_type": "multiple_choice"
                }
                for result in completion.question_results
            ]
        }
        
        # Save to quiz_results collection
        quiz_results_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        result = await quiz_results_collection.insert_one(quiz_result_document)
        
        logger.info(f"✅ Saved adaptive quiz session to history: user={user_id}, "
                   f"course={completion.course_id}, lecture={completion.lecture_id}, "
                   f"level={completion.level}, score={completion.score}/{completion.total_questions}")
        
        return {
            "success": True,
            "result_id": str(result.inserted_id),
            "message": "Quiz session saved to history"
        }
    
    except Exception as e:
        logger.error(f"Error completing quiz session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save quiz session: {str(e)}"
        )


@router.get("/performance/{course_id}/{lecture_id}")
async def get_user_performance(
    course_id: str,
    lecture_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Get user's performance statistics for a specific lecture.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
        current_user: Authenticated user from Firebase
        db: MongoDB database connection
        
    Returns:
        Performance data including flashcard and question statistics
    """
    try:
        user_id = current_user['uid']
        
        # Initialize service
        performance_service = UserPerformanceService(db)
        
        # Get performance data
        performance = await performance_service.get_user_performance(
            user_id,
            course_id,
            lecture_id
        )
        
        if not performance:
            return {
                "found": False,
                "message": "No performance data found for this lecture"
            }
        
        # Calculate weakness scores
        weakness_scores = await performance_service.calculate_weakness_scores(
            user_id,
            course_id,
            lecture_id
        )
        
        return {
            "found": True,
            "performance": {
                "flashcards": performance.get('flashcards', {}),
                "questions": performance.get('questions', {}),
                "weakness_scores": weakness_scores
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching user performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance data: {str(e)}"
        )

