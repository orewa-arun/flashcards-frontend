"""Service for managing Mix Mode adaptive study sessions."""

import hashlib
import json
import logging
import random
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.mix_session import (
    MixSession,
    MixActivity,
    UserQuestionPerformance,
    MixActivityResponse,
    MixAnswerResponse
)
from app.models.readiness_v2 import UserFlashcardPerformance
from app.models.adaptive_quiz import QuestionResult
from app import readiness_config as config

logger = logging.getLogger(__name__)

# Base path for course data
COURSES_BASE_PATH = Path(__file__).parent.parent.parent / "courses"


class MixSessionService:
    """Service for managing mix mode study sessions."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.sessions_collection = database.mix_sessions
        self.question_perf_collection = database.user_question_performance
        self.flashcard_perf_collection = database.user_flashcard_performance
    
    async def initialize_indexes(self):
        """Create necessary indexes for efficient querying."""
        await self.sessions_collection.create_index([("session_id", 1)], unique=True)
        await self.sessions_collection.create_index([("user_id", 1), ("status", 1)])
        
        await self.question_perf_collection.create_index(
            [("user_id", 1), ("question_content_hash", 1)],
            unique=True
        )
        logger.info("Mix session indexes created")
    
    async def start_session(
        self,
        user_id: str,
        course_id: str,
        deck_ids: List[str]
    ) -> Tuple[str, int]:
        """
        Start a new mix session.
        
        Args:
            user_id: Firebase UID
            course_id: Course identifier
            deck_ids: List of deck/lecture IDs
            
        Returns:
            Tuple of (session_id, total_flashcards)
        """
        # Load flashcards from all decks
        all_flashcards = []
        for deck_id in deck_ids:
            flashcards = await self._load_flashcards_for_deck(course_id, deck_id)
            all_flashcards.extend(flashcards)
        
        if not all_flashcards:
            raise ValueError(f"No flashcards found for decks: {deck_ids}")
        
        # Sort by relevance_score (highest first)
        all_flashcards.sort(
            key=lambda fc: fc.get("relevance_score", {}).get("score", 0),
            reverse=True
        )
        
        # Create master order
        flashcard_master_order = [fc["flashcard_id"] for fc in all_flashcards]
        
        # Generate initial activity queue (Round 1: all medium level)
        activity_queue = []
        for flashcard_id in flashcard_master_order:
            activity = MixActivity(
                type="question",
                flashcard_id=flashcard_id,
                level="medium",
                is_follow_up=False
            )
            activity_queue.append(activity)
        
        # Create session
        session_id = f"mix_{uuid4().hex[:16]}"
        session = MixSession(
            session_id=session_id,
            user_id=user_id,
            course_id=course_id,
            deck_ids=deck_ids,
            flashcard_master_order=flashcard_master_order,
            activity_queue=activity_queue,
            status="in_progress"
        )
        
        # Save to database
        await self.sessions_collection.insert_one(session.model_dump())
        
        logger.info(f"Created mix session {session_id} with {len(flashcard_master_order)} flashcards")
        return session_id, len(flashcard_master_order)
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[MixSession]:
        """
        Retrieve an existing session by ID.
        
        Args:
            session_id: Session identifier
            user_id: Firebase UID (for verification)
            
        Returns:
            MixSession or None if not found
        """
        session_doc = await self.sessions_collection.find_one({"session_id": session_id})
        if not session_doc:
            return None
        
        session = MixSession(**session_doc)
        
        # Verify user owns this session
        if session.user_id != user_id:
            raise PermissionError("Session does not belong to this user")
        
        return session
    
    async def get_next_activity(self, session_id: str, user_id: str) -> Optional[MixActivityResponse]:
        """
        Get the next activity from the session queue.
        
        Args:
            session_id: Session identifier
            user_id: Firebase UID (for verification)
            
        Returns:
            MixActivityResponse or None if session is complete
        """
        # Retrieve session
        session_doc = await self.sessions_collection.find_one({"session_id": session_id})
        if not session_doc:
            raise ValueError(f"Session {session_id} not found")
        
        session = MixSession(**session_doc)
        
        # Verify user owns this session
        if session.user_id != user_id:
            raise PermissionError("Session does not belong to this user")
        
        # Check if queue is empty
        if not session.activity_queue:
            # Check if we need to generate a new round
            if len(session.seen_in_current_round) >= len(session.flashcard_master_order):
                # Round complete, generate next round
                await self._generate_next_round(session)
            else:
                # Queue exhausted before covering all flashcards in the round.
                # Instead of ending the session, generate the next round to keep Mix endless.
                # This can happen if some flashcards had no available questions at the chosen level
                # and were skipped; the next round will re-attempt based on updated next levels.
                await self._generate_next_round(session)
        
        # Pop the next activity
        if not session.activity_queue:
            return None
            
        next_activity = session.activity_queue.pop(0)
        
        # Mark flashcard as seen if this is a question
        if next_activity.type == "question" and not next_activity.is_follow_up:
            if next_activity.flashcard_id not in session.seen_in_current_round:
                session.seen_in_current_round.append(next_activity.flashcard_id)
        
        # Update session in database
        await self.sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "activity_queue": [act.model_dump() for act in session.activity_queue],
                    "seen_in_current_round": session.seen_in_current_round,
                    "last_updated": datetime.now(timezone.utc)
                }
            }
        )
        
        # Build response based on activity type
        if next_activity.type == "flashcard":
            # Load flashcard content
            flashcard_content = await self._load_flashcard_content(
                session.course_id,
                next_activity.flashcard_id
            )
            
            return MixActivityResponse(
                activity_type="flashcard",
                flashcard_id=next_activity.flashcard_id,
                flashcard_content=flashcard_content,
                round_number=session.current_round,
                progress={
                    "seen_in_round": len(session.seen_in_current_round),
                    "total_flashcards": len(session.flashcard_master_order),
                    "current_round": session.current_round
                }
            )
        else:
            # Load and select a question
            question = await self._select_question_for_flashcard(
                session.course_id,
                next_activity.flashcard_id,
                next_activity.level,
                session.asked_question_hashes,
                session.user_id
            )
            
            if question:
                # Add question hash to asked list
                question_hash = self._hash_question(question["question_text"])
                session.asked_question_hashes.append(question_hash)
                await self.sessions_collection.update_one(
                    {"session_id": session_id},
                    {"$push": {"asked_question_hashes": question_hash}}
                )
                
                return MixActivityResponse(
                    activity_type="question",
                    flashcard_id=next_activity.flashcard_id,
                    question=question,
                    level=next_activity.level,
                    is_follow_up=next_activity.is_follow_up,
                    round_number=session.current_round,
                    progress={
                        "seen_in_round": len(session.seen_in_current_round),
                        "total_flashcards": len(session.flashcard_master_order),
                        "current_round": session.current_round
                    }
                )
            else:
                # No question found - skip this activity and try next
                logger.warning(f"No question found for flashcard {next_activity.flashcard_id} at level {next_activity.level}, skipping to next activity")
                
                # Remove this activity and try again
                session.activity_queue.pop(0)
                await self.sessions_collection.update_one(
                    {"session_id": session_id},
                    {"$pop": {"activity_queue": -1}}
                )
                
                # Recursively call to get next activity
                return await self.get_next_activity(session_id, user_id)
    
    async def submit_answer(
        self,
        session_id: str,
        user_id: str,
        flashcard_id: str,
        question_hash: str,
        level: str,
        user_answer: Any,
        correct_answer: Any,
        is_follow_up: bool
    ) -> MixAnswerResponse:
        """
        Submit an answer and update performance.
        
        Args:
            session_id: Session identifier
            user_id: Firebase UID
            flashcard_id: The flashcard ID
            question_hash: Hash of the question
            level: Question difficulty level
            user_answer: User's answer
            correct_answer: Correct answer
            is_follow_up: Whether this was a follow-up question
            
        Returns:
            MixAnswerResponse with grading results
        """
        # Grade the answer
        is_correct, partial_credit = self._grade_answer(user_answer, correct_answer)
        
        # Calculate points earned
        points_earned = self._calculate_points(level, is_correct, partial_credit)
        
        # Update UserFlashcardPerformance (triggers CS recalculation)
        from app.services.flashcard_performance_service import FlashcardPerformanceService
        flashcard_service = FlashcardPerformanceService(self.db)
        
        # Get course_id and lecture_id from flashcard_id
        # Assuming flashcard_id format: "DECK_ID_NUMBER" (e.g., "SI_lec_1_15")
        parts = flashcard_id.rsplit("_", 1)
        lecture_id = parts[0] if len(parts) > 1 else flashcard_id
        
        # Fetch session to get course_id
        session_doc = await self.sessions_collection.find_one({"session_id": session_id})
        if not session_doc:
            raise ValueError(f"Session {session_id} not found")
        
        session = MixSession(**session_doc)
        course_id = session.course_id
        
        # Create a QuestionResult for the service
        question_result = QuestionResult(
            question_id=question_hash,
            source_flashcard_id=flashcard_id,
            question_type="mcq",  # We'll assume MCQ for now
            question=user_answer,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            partial_credit_score=partial_credit
        )
        
        # Update flashcard performance
        await flashcard_service.update_performance_from_quiz(
            user_id=user_id,
            course_id=course_id,
            lecture_id=lecture_id,
            question_results=[question_result],
            difficulty=level
        )
        
        # Update UserQuestionPerformance
        await self.question_perf_collection.update_one(
            {"user_id": user_id, "question_content_hash": question_hash},
            {
                "$set": {
                    "flashcard_id": flashcard_id,
                    "level": level,
                    "is_correct": is_correct,
                    "last_attempted": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        # Inject remediation if user earned 0 points (completely wrong) and not a follow-up
        # Per spec: "even if partially correct, the user moves on" - so only trigger remediation for 0 points
        if points_earned <= 0 and not is_follow_up:
            logger.info(f"🔴 Wrong answer (0 points) - injecting remediation for {flashcard_id}")
            await self._inject_remediation(session_id, flashcard_id, user_id)
        else:
            logger.info(f"✅ Answer earned {points_earned} points - no remediation needed")
        
        return MixAnswerResponse(
            is_correct=is_correct,
            correct_answer=correct_answer,
            explanation=None,  # Can be added later
            points_earned=points_earned
        )
    
    async def _inject_remediation(self, session_id: str, flashcard_id: str, user_id: str):
        """
        Inject remediation activities (flashcard review + follow-up question) to the front of the queue.
        
        Args:
            session_id: Session identifier
            flashcard_id: The flashcard that needs remediation
            user_id: Firebase UID
        """
        logger.info(f"🔄 Starting remediation injection for flashcard {flashcard_id}")
        
        # Get the updated question_next_level from flashcard performance
        flashcard_perf = await self.flashcard_perf_collection.find_one({
            "user_id": user_id,
            "flashcard_id": flashcard_id
        })
        
        next_level = "medium"  # Default
        if flashcard_perf:
            perf = UserFlashcardPerformance(**flashcard_perf)
            next_level = perf.question_next_level
            logger.info(f"📊 Flashcard performance found - CS: {perf.comfortability_score:.2f}, next_level: {next_level}")
        else:
            logger.warning(f"⚠️ No flashcard performance found for {flashcard_id}, using default level: {next_level}")
        
        # Create remediation activities
        flashcard_review = MixActivity(
            type="flashcard",
            flashcard_id=flashcard_id,
            level=next_level,
            is_follow_up=False
        )
        
        follow_up_question = MixActivity(
            type="question",
            flashcard_id=flashcard_id,
            level=next_level,
            is_follow_up=True
        )
        
        logger.info(f"📝 Created remediation activities: flashcard_review + follow_up_question at level {next_level}")
        
        # Prepend to activity queue
        result = await self.sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "activity_queue": {
                        "$each": [
                            flashcard_review.model_dump(),
                            follow_up_question.model_dump()
                        ],
                        "$position": 0
                    }
                },
                "$set": {"last_updated": datetime.now(timezone.utc)}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Successfully injected remediation for flashcard {flashcard_id} at level {next_level}")
        else:
            logger.error(f"❌ Failed to inject remediation - session {session_id} not found or not modified")
    
    async def _generate_next_round(self, session: MixSession):
        """
        Generate the next round of questions based on question_next_level.
        
        Args:
            session: The current session
        """
        new_queue = []
        
        for flashcard_id in session.flashcard_master_order:
            # Get the question_next_level for this flashcard
            flashcard_perf = await self.flashcard_perf_collection.find_one({
                "user_id": session.user_id,
                "flashcard_id": flashcard_id
            })
            
            level = "easy"  # Default for new flashcards
            if flashcard_perf:
                perf = UserFlashcardPerformance(**flashcard_perf)
                level = perf.question_next_level
            
            activity = MixActivity(
                type="question",
                flashcard_id=flashcard_id,
                level=level,
                is_follow_up=False
            )
            new_queue.append(activity)
        
        # Update session
        session.activity_queue = new_queue
        session.seen_in_current_round = []
        session.current_round += 1
        
        await self.sessions_collection.update_one(
            {"session_id": session.session_id},
            {
                "$set": {
                    "activity_queue": [act.model_dump() for act in new_queue],
                    "seen_in_current_round": [],
                    "current_round": session.current_round,
                    "last_updated": datetime.now(timezone.utc)
                }
            }
        )
        
        logger.info(f"Generated round {session.current_round} for session {session.session_id}")
    
    async def _select_question_for_flashcard(
        self,
        course_id: str,
        flashcard_id: str,
        level: str,
        asked_question_hashes: List[str],
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Select a question for a flashcard using the 3-tier fallback logic.
        
        Priority:
        1. Unseen question at target level
        2. Previously incorrectly answered question at target level
        3. Random question at target level
        
        Args:
            course_id: Course identifier
            flashcard_id: Flashcard identifier
            level: Target difficulty level
            asked_question_hashes: List of already asked question hashes
            user_id: Firebase UID
            
        Returns:
            Question dict or None
        """
        # Load questions at the target level
        questions = await self._load_questions_for_level(course_id, flashcard_id, level)
        
        if not questions:
            logger.warning(f"No questions found for {flashcard_id} at level {level}")
            return None
        
        # Filter questions by flashcard_id
        flashcard_questions = [
            q for q in questions
            if q.get("source_flashcard_id") == flashcard_id
        ]
        
        if not flashcard_questions:
            logger.warning(f"No questions for flashcard {flashcard_id} at level {level}")
            return None
        
        # Priority 1: Unseen questions
        unseen_questions = [
            q for q in flashcard_questions
            if self._hash_question(q["question_text"]) not in asked_question_hashes
        ]
        
        if unseen_questions:
            return random.choice(unseen_questions)
        
        # Priority 2: Previously incorrectly answered questions
        incorrect_questions = []
        for q in flashcard_questions:
            q_hash = self._hash_question(q["question_text"])
            perf = await self.question_perf_collection.find_one({
                "user_id": user_id,
                "question_content_hash": q_hash
            })
            if perf and not perf.get("is_correct"):
                incorrect_questions.append(q)
        
        if incorrect_questions:
            return random.choice(incorrect_questions)
        
        # Priority 3: Random question (all have been answered correctly)
        return random.choice(flashcard_questions)
    
    async def _load_flashcards_for_deck(
        self,
        course_id: str,
        deck_id: str
    ) -> List[Dict[str, Any]]:
        """Load flashcards from a deck's JSON file."""
        flashcard_path = COURSES_BASE_PATH / course_id / "cognitive_flashcards" / deck_id / f"{deck_id}_cognitive_flashcards_only.json"
        
        if not flashcard_path.exists():
            logger.error(f"Flashcard file not found: {flashcard_path}")
            return []
        
        try:
            with open(flashcard_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("flashcards", [])
        except Exception as e:
            logger.error(f"Error loading flashcards from {flashcard_path}: {e}")
            return []
    
    async def _load_flashcard_content(
        self,
        course_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load the full content of a specific flashcard."""
        # Extract deck_id from flashcard_id (format: "DECK_ID_NUMBER")
        parts = flashcard_id.rsplit("_", 1)
        deck_id = parts[0] if len(parts) > 1 else flashcard_id
        
        flashcards = await self._load_flashcards_for_deck(course_id, deck_id)
        
        for fc in flashcards:
            if fc.get("flashcard_id") == flashcard_id:
                return fc
        
        return None
    
    async def _load_questions_for_level(
        self,
        course_id: str,
        flashcard_id: str,
        level: str
    ) -> List[Dict[str, Any]]:
        """
        Load questions for a specific level from the appropriate quiz file.
        
        Level mapping: easy=1, medium=2, hard=3, boss=4
        """
        # Map level to file number
        level_map = {"easy": 1, "medium": 2, "hard": 3, "boss": 4}
        level_num = level_map.get(level, 2)
        
        # Extract deck_id from flashcard_id
        parts = flashcard_id.rsplit("_", 1)
        deck_id = parts[0] if len(parts) > 1 else flashcard_id
        
        # Load quiz file
        quiz_path = COURSES_BASE_PATH / course_id / "quiz" / f"{deck_id}_level_{level_num}_quiz.json"
        
        if not quiz_path.exists():
            logger.warning(f"Quiz file not found: {quiz_path}")
            return []
        
        try:
            with open(quiz_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            questions = data.get("questions", [])
            
            # Add content hash and normalize correct_answer to option keys
            for q in questions:
                q["question_hash"] = self._hash_question(q["question_text"])
                # CRITICAL: Normalize correct_answer from text to option keys
                q["correct_answer"] = self._normalize_correct_answer(q)
            
            return questions
        except Exception as e:
            logger.error(f"Error loading questions from {quiz_path}: {e}")
            return []
    
    def _hash_question(self, question_text: str) -> str:
        """Generate a deterministic hash for a question."""
        return hashlib.sha256(question_text.encode('utf-8')).hexdigest()[:16]
    
    def _normalize_correct_answer(self, question: Dict[str, Any]) -> List[str]:
        """
        Normalize correct_answer to always be an array of option KEYS.
        
        Handles legacy data where correct_answer might be:
        - A string option key: "C"
        - An array of option keys: ["A", "D"]
        - A string option text: "Targeting new users or segments."
        - An array of option texts: ["Adding new features...", "Lowering the price..."]
        
        Args:
            question: Question dict with 'correct_answer' and 'options'
            
        Returns:
            List of option keys (e.g., ["C"] or ["A", "D"])
        """
        options = question.get('options', {})
        option_keys = list(options.keys())
        raw = question.get('correct_answer')
        
        if not raw:
            return []
        
        # Ensure raw is a list
        raw_list = raw if isinstance(raw, list) else [raw]
        
        # Normalize text for matching
        import re
        def norm(s):
            text = str(s or '').strip().lower()
            # Remove common punctuation and markdown formatting
            text = text.replace('.', '').replace(',', '').replace('*', '').replace('_', '')
            text = text.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            text = text.replace('"', '').replace("'", '').replace(':', '').replace(';', '')
            # Collapse multiple whitespace into single space
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        keys = []
        for item in raw_list:
            value = str(item or '').strip()
            if not value:
                continue
            
            # Case 1: Already an option key
            if value in option_keys:
                keys.append(value)
                continue
            
            # Case 2: Match by option text
            match_key = next(
                (k for k in option_keys if norm(options[k]) == norm(value)),
                None
            )
            if match_key:
                keys.append(match_key)
                logger.info(f"✅ Normalized answer text to key '{match_key}' for question: {question.get('question_text', '')[:60]}")
            else:
                # Fallback: keep the raw value (will cause issues, but log it)
                logger.warning(f"❌ Could not normalize correct_answer '{value[:100]}' to option key for question: {question.get('question_text', '')[:60]}")
                logger.warning(f"   Available options: {list(options.keys())}")
                logger.warning(f"   Option texts (normalized): {[norm(options[k]) for k in option_keys]}")
                logger.warning(f"   Target text (normalized): {norm(value)}")
                keys.append(value)
        
        return keys
    
    def _grade_answer(self, user_answer: Any, correct_answer: Any) -> Tuple[bool, Optional[float]]:
        """
        Grade an answer and return (is_correct, partial_credit_score).
        
        Returns:
            Tuple of (is_correct, partial_credit) where partial_credit is 0.0-1.0 or None
        """
        # Handle MCA (Multiple Correct Answers)
        if isinstance(correct_answer, list) and len(correct_answer) > 1:
            if not isinstance(user_answer, list):
                return False, 0.0
            
            user_set = set(user_answer) if isinstance(user_answer, list) else {user_answer}
            correct_set = set(correct_answer)
            
            if user_set == correct_set:
                return True, 1.0
            
            # Calculate partial credit
            correct_selections = len(user_set & correct_set)
            incorrect_selections = len(user_set - correct_set)
            
            if correct_selections == 0:
                return False, 0.0
            
            partial = correct_selections / len(correct_set)
            return False, partial
        
        # Handle MCQ (single answer)
        if isinstance(correct_answer, list):
            correct_answer = correct_answer[0]
        
        is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        return is_correct, None
    
    def _calculate_points(self, level: str, is_correct: bool, partial_credit: Optional[float]) -> float:
        """Calculate points earned for an answer."""
        level_points = config.ACCURACY_POINTS.get(level, {})
        
        if partial_credit is not None and not is_correct:
            max_points = level_points.get("correct", 0)
            return max_points * partial_credit
        
        if is_correct:
            return float(level_points.get("correct", 0))
        else:
            return float(level_points.get("incorrect", 0))


def get_mix_session_service(db=None) -> MixSessionService:
    """Dependency injection helper."""
    from app.database import get_database
    if db is None:
        db = get_database()
    return MixSessionService(db)

