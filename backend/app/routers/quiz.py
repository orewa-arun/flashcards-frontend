"""Adaptive quiz generation and submission endpoints."""

import json
import os
import random
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Header, Depends
from app.database import get_database
from app.firebase_auth import get_current_user
from app.services.user_service import get_user_service, UserService
from app.models.adaptive_quiz import (
    QuizGenerationRequest, QuizGenerationResponse, QuizQuestion,
    QuizSubmissionRequest, QuizSubmissionResponse, QuestionResult,
    UserDeckPerformance, FlashcardPerformance, FlashcardWeakness
)
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])

# Collection name for user deck performance
USER_DECK_PERFORMANCE_COLLECTION = "user_deck_performance"
QUIZ_SESSIONS_COLLECTION = "quiz_sessions"

# Base path for cognitive flashcards
# Construct path relative to this file's location to ensure portability
_ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
FLASHCARDS_BASE_PATH = os.path.abspath(os.path.join(_ROUTER_DIR, "..", "..", "courses"))


async def get_user_id_from_header(x_user_id: str = Header(..., alias="X-User-ID")) -> str:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-ID header is required")
    return x_user_id


async def ensure_user_exists(user_id: str, db) -> User:
    """Ensure user exists in database, create if not."""
    users_collection = db[settings.USERS_COLLECTION]
    
    user_doc = await users_collection.find_one({"user_id": user_id})
    
    if not user_doc:
        # Create minimal user document with required firebase_uid; keep legacy user_id for compatibility
        new_user = User(firebase_uid=user_id, email=None, name=None, picture=None, user_id=user_id)
        result = await users_collection.insert_one(new_user.model_dump(by_alias=True, exclude={"id"}))
        user_doc = await users_collection.find_one({"_id": result.inserted_id})
        logger.info(f"Created new user: {user_id}")
    else:
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}}
        )
    
    return User(**user_doc)


def load_flashcards(course_id: str, deck_id: str) -> Dict[str, Any]:
    """Load cognitive flashcards JSON file for a given course and deck."""
    flashcard_path = os.path.join(
        FLASHCARDS_BASE_PATH,
        course_id,
        "cognitive_flashcards",
        deck_id,
        f"{deck_id}_cognitive_flashcards.json"
    )
    
    if not os.path.exists(flashcard_path):
        raise HTTPException(
            status_code=404,
            detail=f"Flashcard file not found for course {course_id}, deck {deck_id}"
        )
    
    try:
        with open(flashcard_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading flashcards: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading flashcards: {str(e)}")


def load_hard_questions(course_id: str, deck_id: str) -> Dict[str, Any]:
    """Load hard questions JSON file for a given course and deck."""
    hard_questions_path = os.path.join(
        FLASHCARDS_BASE_PATH,
        course_id,
        "cognitive_flashcards",
        deck_id,
        f"{deck_id}_hard_questions.json"
    )
    
    if not os.path.exists(hard_questions_path):
        raise HTTPException(
            status_code=404,
            detail=f"Hard questions not available for course {course_id}, deck {deck_id}. Please generate them first using: python generate_hard_questions.py {course_id} {deck_id}"
        )
    
    try:
        with open(hard_questions_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading hard questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading hard questions: {str(e)}")


async def get_or_create_deck_performance(
    firebase_uid: str,
    course_id: str,
    deck_id: str,
    flashcards_data: Dict[str, Any],
    db
) -> UserDeckPerformance:
    """Get existing deck performance or create new one."""
    performance_collection = db[USER_DECK_PERFORMANCE_COLLECTION]
    
    perf_doc = await performance_collection.find_one({
        "firebase_uid": firebase_uid,
        "course_id": course_id,
        "deck_id": deck_id
    })
    
    if perf_doc:
        return UserDeckPerformance(**perf_doc)
    
    # Create new performance tracking document
    flashcards = flashcards_data.get("flashcards", [])
    total_flashcards = len(flashcards)
    
    flashcards_performance = []
    for card in flashcards:
        flashcard_id = card.get("flashcard_id")
        if not flashcard_id:
            continue
        
        flashcard_perf = FlashcardPerformance(
            flashcard_id=flashcard_id,
            last_attempted=None
        )
        flashcards_performance.append(flashcard_perf)
    
    new_performance = UserDeckPerformance(
        firebase_uid=firebase_uid,
        course_id=course_id,
        deck_id=deck_id,
        total_flashcards=total_flashcards,
        flashcards_performance=flashcards_performance,
        last_quiz_date=None
    )
    
    await performance_collection.insert_one(
        new_performance.model_dump(by_alias=True, exclude={"id"})
    )
    
    logger.info(f"Created new deck performance for user {firebase_uid}, deck {deck_id}")
    return new_performance


def select_questions_phase1(
    flashcards_data: Dict[str, Any],
    num_questions: int
) -> List[Dict[str, Any]]:
    """
    Phase 1: Initial quiz - select questions from top relevance flashcards.
    
    Returns list of selected questions with metadata.
    """
    flashcards = flashcards_data.get("flashcards", [])
    
    # Sort flashcards by relevance score (highest first)
    sorted_flashcards = sorted(
        flashcards,
        key=lambda x: x.get("relevance_score", {}).get("score", 0),
        reverse=True
    )
    
    # Take top N flashcards based on quiz size
    top_flashcards = sorted_flashcards[:num_questions]
    
    selected_questions = []
    for flashcard in top_flashcards:
        recall_questions = flashcard.get("recall_questions", [])
        if not recall_questions:
            continue
        
        flashcard_id = flashcard.get("flashcard_id")
        if not flashcard_id:
            logger.warning(f"Flashcard missing flashcard_id, skipping")
            continue
        
        # Randomly pick one question from this flashcard
        question = random.choice(recall_questions)
        selected_questions.append({
            "source_flashcard_id": flashcard_id,
            "question_data": question
        })
    
    return selected_questions


def select_questions_phase3(
    flashcards_data: Dict[str, Any],
    performance: UserDeckPerformance,
    num_questions: int
) -> List[Dict[str, Any]]:
    """
    Phase 3: Adaptive quiz based on user performance.
    
    Priority:
    1. Flashcards answered incorrectly (remediation)
    2. Flashcards never attempted (exploration)
    3. Flashcards answered correctly, prioritized by relevance and low attempts (reinforcement)
    """
    flashcards = flashcards_data.get("flashcards", [])
    flashcards_perf_dict = {fp.flashcard_id: fp for fp in performance.flashcards_performance}
    
    # Group flashcards by priority
    remediation_flashcards = []  # Flashcards with incorrect answers
    exploration_flashcards = []  # Flashcards never attempted
    reinforcement_flashcards = []  # Flashcards answered correctly
    
    for flashcard in flashcards:
        flashcard_id = flashcard.get("flashcard_id")
        if not flashcard_id:
            continue
        
        perf = flashcards_perf_dict.get(flashcard_id)
        if not perf:
            # Never attempted - add to exploration
            exploration_flashcards.append((flashcard, None))
            continue
        
        if perf.times_incorrect > 0:
            remediation_flashcards.append((flashcard, perf))
        elif perf.times_attempted == 0:
            exploration_flashcards.append((flashcard, perf))
        else:
            reinforcement_flashcards.append((flashcard, perf))
    
    # Sort exploration flashcards by relevance score
    exploration_flashcards.sort(
        key=lambda x: x[0].get("relevance_score", {}).get("score", 0),
        reverse=True
    )
    
    # Sort reinforcement flashcards by relevance (desc) and attempts (asc)
    reinforcement_flashcards.sort(
        key=lambda x: (
            -x[0].get("relevance_score", {}).get("score", 0),
            x[1].times_attempted if x[1] else 0
        )
    )
    
    # Build priority queue
    priority_queue = []
    
    # Priority 1: Remediation
    priority_queue.extend(remediation_flashcards)
    
    # Priority 2: Exploration
    priority_queue.extend(exploration_flashcards)
    
    # Priority 3: Reinforcement
    priority_queue.extend(reinforcement_flashcards)
    
    # Select questions up to num_questions
    selected_questions = []
    for flashcard, perf in priority_queue[:num_questions]:
        recall_questions = flashcard.get("recall_questions", [])
        if not recall_questions:
            continue
        
        flashcard_id = flashcard.get("flashcard_id")
        if not flashcard_id:
            continue
        
        # Randomly pick one question from this flashcard
        question = random.choice(recall_questions)
        selected_questions.append({
            "source_flashcard_id": flashcard_id,
            "question_data": question
        })
    
    return selected_questions


def build_quiz_questions(selected_questions: List[Dict[str, Any]]) -> List[QuizQuestion]:
    """Convert selected questions into QuizQuestion models."""
    quiz_questions = []
    
    for sq in selected_questions:
        q_data = sq["question_data"]
        
        # FIX: Add validation to skip questions with missing answers
        if q_data.get("answer") is None:
            logger.warning(f"Skipping malformed medium question (missing 'answer' key): flashcard_id={sq.get('source_flashcard_id')}, question={q_data.get('question', 'N/A')}")
            continue

        question_id = str(uuid4())
        
        quiz_question = QuizQuestion(
            question_id=question_id,
            source_flashcard_id=sq["source_flashcard_id"],
            question_type=q_data.get("type", "mcq"),
            question=q_data.get("question", ""),
            options=q_data.get("options"),
            items=q_data.get("items"),
            categories=q_data.get("categories"),
            scenario=q_data.get("scenario"),
            premises=q_data.get("premises"),
            responses=q_data.get("responses"),
            correct_answer=q_data.get("answer")
        )
        quiz_questions.append(quiz_question)
    
    # Shuffle questions to avoid predictable ordering
    random.shuffle(quiz_questions)
    
    return quiz_questions


def select_hard_questions(hard_questions_data: Dict[str, Any], num_questions: int) -> List[Dict[str, Any]]:
    """
    Select random hard questions from the hard questions file.
    
    Args:
        hard_questions_data: Loaded hard questions JSON
        num_questions: Number of questions to select
        
    Returns:
        List of selected questions with metadata
    """
    questions = hard_questions_data.get("questions", [])
    
    if not questions:
        raise HTTPException(status_code=404, detail="No hard questions available")
    
    # Randomly select questions
    num_to_select = min(num_questions, len(questions))
    selected = random.sample(questions, num_to_select)
    
    # Convert to format expected by build_quiz_questions_hard
    formatted_questions = []
    for q in selected:
        formatted_questions.append({
            "question_data": q,
            "slide_number": q.get("slide_number", 0)
        })
    
    return formatted_questions


def build_quiz_questions_hard(selected_questions: List[Dict[str, Any]]) -> List[QuizQuestion]:
    """
    Convert hard questions into QuizQuestion models.
    Hard questions use source_flashcard_id from the question data.
    """
    quiz_questions = []
    
    for sq in selected_questions:
        q_data = sq["question_data"]

        # FIX: Add validation to skip questions with missing answers
        if q_data.get("correct_answer") is None:
            logger.warning(f"Skipping malformed hard question (missing 'correct_answer' key): question={q_data.get('question', 'N/A')}")
            continue

        # Get source_flashcard_id from question data
        source_flashcard_id = q_data.get("source_flashcard_id")
        if not source_flashcard_id:
            logger.warning(f"Hard question missing source_flashcard_id, skipping: question={q_data.get('question', 'N/A')}")
            continue

        question_id = str(uuid4())
        
        quiz_question = QuizQuestion(
            question_id=question_id,
            source_flashcard_id=source_flashcard_id,
            question_type=q_data.get("type", "mcq"),
            question=q_data.get("question", ""),
            options=q_data.get("options"),
            items=q_data.get("items"),
            categories=q_data.get("categories"),
            scenario=q_data.get("scenario"),
            premises=q_data.get("premises"),
            responses=q_data.get("responses"),
            correct_answer=q_data.get("correct_answer")
        )
        quiz_questions.append(quiz_question)
    
    # Shuffle questions
    random.shuffle(quiz_questions)
    
    return quiz_questions


@router.post("/generate", response_model=QuizGenerationResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    db = Depends(get_database)
):
    """
    Generate an adaptive quiz based on user's performance history and difficulty level.
    
    Difficulty levels:
    - medium: Questions from flashcards (adaptive based on performance)
    - hard: Challenging questions from hard_questions.json (random selection)
    """
    try:
        firebase_uid = current_user["uid"]
        difficulty = request.difficulty or "medium"
        
        # Ensure user exists in database
        await user_service.get_or_create_user(
            firebase_uid=firebase_uid,
            email=current_user.get("email"),
            name=current_user.get("name"),
            picture=current_user.get("picture"),
            email_verified=current_user.get("email_verified", False)
        )
        
        # Handle hard difficulty
        if difficulty == "hard":
            logger.info(f"Generating HARD quiz for user {firebase_uid}")
            
            # Load hard questions
            hard_questions_data = load_hard_questions(request.course_id, request.deck_id)
            quiz_size = request.num_questions or 20
            
            # Select and build hard questions
            selected_questions = select_hard_questions(hard_questions_data, quiz_size)
            quiz_questions = build_quiz_questions_hard(selected_questions)
            
            # Create quiz session
            quiz_id = str(uuid4())
            quiz_session = {
                "quiz_id": quiz_id,
                "firebase_uid": firebase_uid,
                "course_id": request.course_id,
                "deck_id": request.deck_id,
                "difficulty": difficulty,
                "questions": [q.model_dump() for q in quiz_questions],
                "created_at": datetime.now(timezone.utc),
                "completed": False
            }
            
            quiz_sessions_collection = db[QUIZ_SESSIONS_COLLECTION]
            await quiz_sessions_collection.insert_one(quiz_session)
            
            return QuizGenerationResponse(
                quiz_id=quiz_id,
                course_id=request.course_id,
                deck_id=request.deck_id,
                difficulty=difficulty,
                questions=quiz_questions,
                total_questions=len(quiz_questions),
                quiz_attempt_number=1  # Hard quizzes don't track attempts
            )
        
        # Handle medium difficulty (existing adaptive logic)
        logger.info(f"Generating MEDIUM quiz for user {firebase_uid}")
        
        # Load flashcards
        flashcards_data = load_flashcards(request.course_id, request.deck_id)
        total_cards = flashcards_data.get("metadata", {}).get("total_cards", 0)
        
        # Determine quiz size based on total cards
        if total_cards < 15:
            quiz_size = min(10, request.num_questions or 10)
        else:
            quiz_size = min(20, request.num_questions or 20)
        
        quiz_size = min(quiz_size, total_cards)  # Can't have more questions than concepts
        
        # Get or create performance tracking
        performance = await get_or_create_deck_performance(
            firebase_uid, request.course_id, request.deck_id, flashcards_data, db
        )
        
        # Select questions based on phase
        if performance.total_quiz_attempts == 0:
            # Phase 1: First quiz - baseline assessment
            logger.info(f"Generating Phase 1 (baseline) quiz for user {firebase_uid}")
            selected_questions = select_questions_phase1(flashcards_data, quiz_size)
        else:
            # Phase 3: Adaptive quiz based on performance
            logger.info(f"Generating Phase 3 (adaptive) quiz for user {firebase_uid}")
            selected_questions = select_questions_phase3(flashcards_data, performance, quiz_size)
        
        # Build quiz questions
        quiz_questions = build_quiz_questions(selected_questions)
        
        # Create quiz session
        quiz_id = str(uuid4())
        quiz_session = {
            "quiz_id": quiz_id,
            "firebase_uid": firebase_uid,
            "course_id": request.course_id,
            "deck_id": request.deck_id,
            "difficulty": difficulty,
            "questions": [q.model_dump() for q in quiz_questions],
            "created_at": datetime.now(timezone.utc),
            "completed": False
        }
        
        quiz_sessions_collection = db[QUIZ_SESSIONS_COLLECTION]
        await quiz_sessions_collection.insert_one(quiz_session)
        
        return QuizGenerationResponse(
            quiz_id=quiz_id,
            course_id=request.course_id,
            deck_id=request.deck_id,
            difficulty=difficulty,
            questions=quiz_questions,
            total_questions=len(quiz_questions),
            quiz_attempt_number=performance.total_quiz_attempts + 1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@router.post("/submit", response_model=QuizSubmissionResponse)
async def submit_quiz(
    submission: QuizSubmissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    db = Depends(get_database)
):
    """
    Submit quiz answers and update user's flashcard-level performance.
    
    Returns detailed results including weak flashcards for review.
    """
    try:
        firebase_uid = current_user["uid"]
        
        # Increment quiz attempts counter
        await user_service.increment_quiz_attempts(firebase_uid)
        
        # Retrieve quiz session
        quiz_sessions_collection = db[QUIZ_SESSIONS_COLLECTION]
        quiz_session = await quiz_sessions_collection.find_one({"quiz_id": submission.quiz_id})
        
        if not quiz_session:
            raise HTTPException(status_code=404, detail="Quiz session not found")
        
        if quiz_session.get("completed"):
            raise HTTPException(status_code=400, detail="Quiz already submitted")
        
        # Get questions from session
        questions = [QuizQuestion(**q) for q in quiz_session["questions"]]
        answers_dict = {ans.question_id: ans.user_answer for ans in submission.answers}
        
        # Grade the quiz
        question_results = []
        score = 0.0  # Changed to float to support partial credit
        
        for question in questions:
            user_answer = answers_dict.get(question.question_id)
            is_correct, partial_credit = compare_answers(user_answer, question.correct_answer, question.question_type)
            
            # Calculate score contribution
            if question.question_type == "mca":
                # For MCA, use partial credit score
                score += partial_credit if partial_credit is not None else 0.0
            elif is_correct:
                # For other types, binary scoring
                score += 1.0
            
            question_results.append(QuestionResult(
                question_id=question.question_id,
                source_flashcard_id=question.source_flashcard_id,
                question_type=question.question_type,
                question=question.question,
                options=question.options,
                user_answer=user_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                partial_credit_score=partial_credit
            ))
            
        now = datetime.now(timezone.utc)
        
        # Calculate percentage
        total_questions = len(questions)
        percentage = (score / total_questions * 100) if total_questions > 0 else 0
        
        # Round score for display (but keep float for accurate percentage calculation)
        display_score = round(score)
        
        # Get difficulty from quiz session or submission
        difficulty = quiz_session.get("difficulty", submission.difficulty or "medium")
        
        # Extract lecture_id from deck_id (e.g., "MIS_lec_1" -> "MIS_lec_1")
        lecture_id = submission.deck_id
        
        # Update flashcard performance using new service
        from app.services.flashcard_performance_service import FlashcardPerformanceService
        flashcard_perf_service = FlashcardPerformanceService(db)
        
        affected_lectures = await flashcard_perf_service.update_performance_from_quiz(
            user_id=firebase_uid,
            course_id=submission.course_id,
            lecture_id=lecture_id,
            question_results=question_results,
            difficulty=difficulty
        )
        
        # Get weak flashcards for this user
        weak_flashcard_perfs = await flashcard_perf_service.get_weak_flashcards_for_user(
            user_id=firebase_uid,
            course_id=submission.course_id
        )
        
        # Convert to FlashcardWeakness models
        weak_flashcards = []
        for perf in weak_flashcard_perfs:
            weak_flashcards.append(FlashcardWeakness(
                flashcard_id=perf.flashcard_id,
                times_attempted=sum(
                    level_perf.attempts 
                    for level_perf in perf.performance_by_level.values()
                ),
                times_correct=sum(
                    level_perf.correct 
                    for level_perf in perf.performance_by_level.values()
                ),
                times_incorrect=sum(
                    level_perf.attempts - level_perf.correct 
                    for level_perf in perf.performance_by_level.values()
                ),
                accuracy=perf.accuracy_score  # Using accuracy_score as proxy
            ))
        
        # Sort weak flashcards by accuracy (worst first)
        weak_flashcards.sort(key=lambda x: x.accuracy)
        
        # Mark quiz session as completed
        await quiz_sessions_collection.update_one(
            {"quiz_id": submission.quiz_id},
            {"$set": {"completed": True, "completed_at": now}}
        )
        
        # Save quiz result to quiz_results collection for history tracking
        quiz_results_collection = db[settings.QUIZ_RESULTS_COLLECTION]
        quiz_result_document = {
            "firebase_uid": firebase_uid,
            "course_id": submission.course_id,
            "deck_id": submission.deck_id,
            "lecture_id": lecture_id,  # Add lecture_id for exam readiness
            "quiz_id": submission.quiz_id,
            "difficulty": difficulty,
            "score": display_score,
            "total_questions": total_questions,
            "percentage": round(percentage, 2),
            "time_taken": submission.time_taken_seconds,
            "completed_at": now,
            "question_results": [qr.model_dump() for qr in question_results]
        }
        
        logger.info(f"Attempting to save quiz result: user={firebase_uid}, course={submission.course_id}, deck={submission.deck_id}, difficulty={difficulty}, score={display_score}/{total_questions}")
        result = await quiz_results_collection.insert_one(quiz_result_document)
        logger.info(f"✅ Successfully saved quiz result to history! Document ID: {result.inserted_id}")
        
        # Dispatch background task to recalculate exam readiness
        from fastapi import BackgroundTasks
        from app.services.readiness_v2_service import ReadinessV2Service
        
        # Note: We'll add background task support in the next step
        # For now, we'll log that this should trigger exam readiness recalculation
        logger.info(f"📊 Quiz submitted. Should trigger exam readiness recalculation for lectures: {affected_lectures}")
        
        return QuizSubmissionResponse(
            quiz_id=submission.quiz_id,
            firebase_uid=firebase_uid,
            course_id=submission.course_id,
            deck_id=submission.deck_id,
            difficulty=difficulty,
            score=display_score,
            total_questions=total_questions,
            percentage=round(percentage, 2),
            time_taken_seconds=submission.time_taken_seconds,
            question_results=question_results,
            weak_flashcards=weak_flashcards,
            completed_at=now,
            quiz_attempt_number=1  # Simplified for now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting quiz: {str(e)}")


def compare_answers(user_answer: Any, correct_answer: Any, question_type: str) -> tuple[bool, Optional[float]]:
    """
    Compare user answer with correct answer based on question type.
    
    Note: For MCQ and MCA questions, correct_answer is always a list.
    - MCQ: list with 1 element (e.g., ["A"])
    - MCA: list with 2+ elements (e.g., ["A", "C"])
    
    Returns:
        tuple: (is_correct: bool, partial_credit_score: Optional[float])
        - For MCQ: (True/False, None)
        - For MCA: (True/False, score between 0.0 and 1.0)
    """
    if user_answer is None:
        return False, None
    
    if question_type in ["mcq", "scenario_mcq"]:
        # correct_answer is a list with 1 element
        if not isinstance(correct_answer, list) or len(correct_answer) == 0:
            return False, None
        
        # Compare user's single answer with the first (and only) element in correct_answer array
        is_correct = str(user_answer).strip() == str(correct_answer[0]).strip()
        return is_correct, None
    
    elif question_type == "mca":
        # correct_answer is a list with 2+ elements
        if not isinstance(correct_answer, list):
            return False, 0.0
        
        # Ensure user_answer is a list
        if not isinstance(user_answer, list):
            user_answer = [user_answer] if user_answer else []
        
        # Normalize answers (strip whitespace)
        correct_set = set(str(ans).strip() for ans in correct_answer)
        user_set = set(str(ans).strip() for ans in user_answer)
        
        # Calculate selections
        correct_selections = len(user_set & correct_set)  # Intersection
        incorrect_selections = len(user_set - correct_set)  # User selected but wrong
        total_correct = len(correct_set)
        
        # STRICT SCORING: If user selected ANY wrong option, they get ZERO credit
        if incorrect_selections > 0:
            partial_score = 0.0
            is_correct = False
        else:
            # No wrong selections - give partial credit based on how many correct ones they got
            partial_score = correct_selections / total_correct if total_correct > 0 else 0.0
            # Question is fully correct only if all correct answers selected
            is_correct = (correct_selections == total_correct)
        
        return is_correct, partial_score
    
    elif question_type == "sequencing":
        # Order matters - compare as lists
        if not isinstance(user_answer, list) or not isinstance(correct_answer, list):
            return False, None
        is_correct = user_answer == correct_answer
        return is_correct, None
    
    elif question_type == "categorization":
        # Compare dictionaries
        if not isinstance(user_answer, dict) or not isinstance(correct_answer, dict):
            return False, None
        
        # Check if the set of categories is the same
        if set(user_answer.keys()) != set(correct_answer.keys()):
            return False, None

        # Normalize and compare items within each category
        for category, items in correct_answer.items():
            user_items = set(user_answer.get(category, []))
            correct_items = set(items)
            if user_items != correct_items:
                return False, None
        
        return True, None
    
    elif question_type == "matching":
        # Compare matching pairs (e.g., ["1-A", "2-B", "3-C"])
        if not isinstance(user_answer, list) or not isinstance(correct_answer, list):
            return False, None
        
        # Normalize and compare as sets (order doesn't matter)
        user_pairs = set(str(pair).strip() for pair in user_answer)
        correct_pairs = set(str(pair).strip() for pair in correct_answer)
        is_correct = user_pairs == correct_pairs
        return is_correct, None
    
    else:
        # Default: direct comparison
        is_correct = user_answer == correct_answer
        return is_correct, None

