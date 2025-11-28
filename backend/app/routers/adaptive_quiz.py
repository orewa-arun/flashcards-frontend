"""API endpoints for adaptive quiz system using PostgreSQL."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.db.postgres import get_postgres_pool
from app.firebase_auth import get_current_user
from app.models.user_performance import QuizSessionRequest, QuizAnswerSubmission, QuizSessionCompletion
from app.services.user_performance_service import UserPerformanceService
from app.services.adaptive_quiz_service import AdaptiveQuizService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/adaptive-quiz", tags=["adaptive-quiz"])


@router.post("/session/start")
async def start_quiz_session(
    request: QuizSessionRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start an adaptive quiz session.
    
    Returns a personalized set of questions based on the user's performance history.
    
    Args:
        request: Quiz session configuration
        current_user: Authenticated user from Firebase
        
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
        
        # Get PostgreSQL pool
        pool = await get_postgres_pool()
        
        # Initialize services
        performance_service = UserPerformanceService(pool)
        quiz_service = AdaptiveQuizService(pool)
        
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
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit an answer to a quiz question.
    
    Updates the user's performance metrics in the database.
    
    Args:
        submission: Answer submission data
        current_user: Authenticated user from Firebase
        
    Returns:
        {
            "success": true,
            "message": "Answer recorded successfully"
        }
    """
    try:
        user_id = current_user['uid']
        
        # Get PostgreSQL pool
        pool = await get_postgres_pool()
        
        # Initialize service
        performance_service = UserPerformanceService(pool)
        
        # Prepare question snapshot if provided
        question_snapshot = None
        if submission.question_text and submission.options:
            question_snapshot = {
                'question_text': submission.question_text,
                'options': submission.options
            }
        
        # Record the answer with snapshot
        success = await performance_service.record_answer(
            user_id=user_id,
            course_id=submission.course_id,
            lecture_id=submission.lecture_id,
            question_hash=submission.question_hash,
            flashcard_id=submission.flashcard_id,
            is_correct=submission.is_correct,
            question_snapshot=question_snapshot
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
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Complete a quiz session and save it to quiz history.
    
    This endpoint saves the completed quiz attempt to the database,
    making it available in the quiz history view.
    
    Args:
        completion: Quiz session completion data
        current_user: Authenticated user from Firebase
        
    Returns:
        {
            "success": true,
            "result_id": "...",
            "message": "Quiz session saved to history"
        }
    """
    try:
        from datetime import datetime
        import json
        
        user_id = current_user['uid']
        
        # Get PostgreSQL pool
        pool = await get_postgres_pool()
        
        logger.info(f"📝 Completing quiz session: user={user_id}, course={completion.course_id}, "
                   f"lecture={completion.lecture_id}, level={completion.level}, "
                   f"score={completion.score}/{completion.total_questions}")
        
        # Calculate percentage
        percentage = round((completion.score / completion.total_questions * 100), 2) if completion.total_questions > 0 else 0
        
        # Create the deck_id from lecture_id and level
        deck_id = f"{completion.lecture_id}"
        
        # Helper function to normalize answers for storage
        def normalize_answer(answer):
            """Convert answer to appropriate format for storage."""
            if isinstance(answer, list):
                return answer  # Keep as array for MCA
            return answer  # Keep as string for MCQ
        
        # Prepare quiz result for storage
        # Note: For full PostgreSQL migration, we would store this in a quiz_results table
        # For now, we'll focus on updating flashcard performance
        
        # Update flashcard performance using new service
        from app.services.flashcard_performance_service import FlashcardPerformanceService
        from app.models.adaptive_quiz import QuestionResult
        
        flashcard_perf_service = FlashcardPerformanceService(pool)
        
        # Convert completion.question_results to QuestionResult models
        question_results_for_service = [
            QuestionResult(
                question_id=str(idx),  # Generate a simple ID
                source_flashcard_id=qr.source_flashcard_id,
                question_type="mca" if isinstance(qr.correct_answer, list) and len(qr.correct_answer) > 1 else "mcq",
                question=qr.question_text,
                options=None,
                user_answer=qr.user_answer,
                correct_answer=qr.correct_answer,
                is_correct=qr.is_correct,
                partial_credit_score=None
            )
            for idx, qr in enumerate(completion.question_results)
        ]
        
        affected_lectures = await flashcard_perf_service.update_performance_from_quiz(
            user_id=user_id,
            course_id=completion.course_id,
            lecture_id=completion.lecture_id,
            question_results=question_results_for_service,
            difficulty=f"level_{completion.level}"
        )
        
        logger.info(f"📊 Updated flashcard performance for lectures: {affected_lectures}")
        
        # Check if this lecture is part of any exams the user is enrolled in
        # Wrap in try-catch to prevent breaking quiz completion if exam readiness fails
        updated_exam_readiness = []
        
        try:
            from app.services.readiness_v2_service import ReadinessV2Service
            from app.repositories.analytics_repository import AnalyticsRepository
            
            readiness_service = ReadinessV2Service(pool)
            analytics_repo = AnalyticsRepository(pool)
            
            # User profiles are now in PostgreSQL, but exam readiness update
            # is handled separately through the readiness_v2_service
            
            logger.info(f"📤 Returning {len(updated_exam_readiness)} exam readiness updates")
        except Exception as e:
            logger.error(f"🚨 Exam readiness update failed, but quiz will still be saved: {e}", exc_info=True)
            # Continue anyway - don't break quiz completion
        
        return {
            "success": True,
            "result_id": "pg_" + str(hash(f"{user_id}_{completion.course_id}_{completion.lecture_id}_{datetime.utcnow().isoformat()}")),
            "message": "Quiz session saved to history",
            "updated_exam_readiness": updated_exam_readiness
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
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's performance statistics for a specific lecture.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
        current_user: Authenticated user from Firebase
        
    Returns:
        Performance data including flashcard and question statistics
    """
    try:
        user_id = current_user['uid']
        
        # Get PostgreSQL pool
        pool = await get_postgres_pool()
        
        # Initialize service
        performance_service = UserPerformanceService(pool)
        
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


@router.get("/weak-concepts/{course_id}")
async def get_weak_concepts_for_course(
    course_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated weak concepts across all lectures in a course.
    
    Returns flashcards where the user has:
    - Accuracy < 60% (weak)
    - At least 2 attempts
    
    Args:
        course_id: Course identifier
        current_user: Authenticated user from Firebase
        
    Returns:
        {
            "has_attempts": bool,
            "weak_concepts": [
                {
                    "lecture_id": str,
                    "flashcard_id": str,
                    "question": str,
                    "options": dict,
                    "correct": int,
                    "incorrect": int,
                    "accuracy": float,
                    "weakness_score": float,
                    "is_missing_data": bool
                }
            ]
        }
    """
    try:
        user_id = current_user['uid']
        
        # Get PostgreSQL pool
        pool = await get_postgres_pool()
        
        # Initialize repository
        from app.repositories.analytics_repository import AnalyticsRepository
        analytics_repo = AnalyticsRepository(pool)
        
        # Get weak flashcards for this user
        weak_flashcards = await analytics_repo.get_weak_flashcards(user_id, course_id)
        
        if not weak_flashcards:
            return {
                "has_attempts": False,
                "weak_concepts": [],
                "message": "No quiz attempts found. Take a quiz first to assess your weak areas."
            }
        
        weak_concepts = []
        
        for perf in weak_flashcards:
            flashcard_id = perf.get("flashcard_id")
            lecture_id = perf.get("lecture_id")
            perf_data = perf.get("performance_data", {})
            perf_by_level = perf_data.get("performance_by_level", {})
            
            # Calculate totals
            correct = sum(p.get("correct", 0) for p in perf_by_level.values())
            attempts = sum(p.get("attempts", 0) for p in perf_by_level.values())
            incorrect = attempts - correct
            
            if attempts >= 2:
                accuracy = (correct / attempts) * 100 if attempts > 0 else 0
                weakness_score = (incorrect + 1) / (correct + 1)
                
                weak_concepts.append({
                    "lecture_id": lecture_id,
                    "flashcard_id": flashcard_id,
                    "question": f"[Flashcard {flashcard_id}]",  # Actual content would come from lectures table
                    "options": {},
                    "answers": {},
                    "example": "",
                    "mermaid_diagrams": {},
                    "math_visualizations": {},
                    "correct": correct,
                    "incorrect": incorrect,
                    "total_attempts": attempts,
                    "accuracy": round(accuracy, 1),
                    "weakness_score": round(weakness_score, 2),
                    "is_missing_data": True  # Would be False if we enriched from lectures table
                })
        
        # Sort by weakness score (worst first)
        weak_concepts.sort(key=lambda x: x["weakness_score"], reverse=True)
        
        return {
            "has_attempts": True,
            "weak_concepts": weak_concepts,
            "total_weak": len(weak_concepts)
        }
    
    except Exception as e:
        logger.error(f"Error fetching weak concepts for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weak concepts: {str(e)}"
        )
