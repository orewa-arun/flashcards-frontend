"""Service for managing Mix Mode adaptive study sessions using PostgreSQL."""

import hashlib
import json
import logging
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

import asyncpg

from app.models.mix_session import (
    MixSession,
    MixActivity,
    MixActivityResponse,
    MixAnswerResponse,
    MixRevealResponse
)
from app.models.adaptive_quiz import QuestionResult
from app import readiness_config as config
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.adaptive_quiz_service import AdaptiveQuizService

logger = logging.getLogger(__name__)


class MixSessionService:
    """Service for managing mix mode study sessions using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """Initialize service with PostgreSQL connection pool."""
        self.pool = pool
        self.analytics_repo = AnalyticsRepository(pool)
        self.quiz_service = AdaptiveQuizService(pool)
    
    async def get_session_data(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from PostgreSQL."""
        query = """
            SELECT 
                session_id, user_id, course_id, deck_ids, status, current_round,
                flashcard_master_order, activity_queue, seen_in_current_round,
                asked_question_hashes, created_at, last_updated
            FROM mix_sessions
            WHERE session_id = $1
        """
        
        async with self.pool.acquire() as conn:
            # Pass session_id as string directly
            row = await conn.fetchrow(query, session_id)
            
            if not row:
                return None
            
            result = dict(row)
            
            # Verify ownership
            if result["user_id"] != user_id:
                raise PermissionError("Session does not belong to this user")
            
            # Parse JSONB fields
            for field in ["deck_ids", "flashcard_master_order", "activity_queue", 
                         "seen_in_current_round", "asked_question_hashes"]:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            
            return result
    
    async def _update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update session in PostgreSQL."""
        now = datetime.now(timezone.utc)
        
        # Build dynamic update query
        set_clauses = ["last_updated = $2"]
        # Pass session_id as string directly
        params = [session_id, now]
        param_idx = 3
        
        for key, value in updates.items():
            if key in ["activity_queue", "seen_in_current_round", "asked_question_hashes", 
                      "flashcard_master_order", "deck_ids"]:
                set_clauses.append(f"{key} = ${param_idx}::jsonb")
                params.append(json.dumps(value))
            elif key in ["status", "current_round"]:
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
            param_idx += 1
        
        query = f"""
            UPDATE mix_sessions
            SET {', '.join(set_clauses)}
            WHERE session_id = $1
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, *params)
    
    async def _get_flashcard_performance(self, user_id: str, flashcard_id: str) -> Optional[Dict[str, Any]]:
        """Get flashcard performance from PostgreSQL."""
        return await self.analytics_repo.get_flashcard_performance(user_id, flashcard_id)
    
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
        # Load flashcards from all decks using DB
        all_flashcards = []
        for deck_id in deck_ids:
            flashcards = await self._load_flashcards_for_deck(course_id, deck_id)
            # Add deck_id to each flashcard for reference
            for fc in flashcards:
                fc["deck_id"] = deck_id
                # Ensure flashcard_id exists
                if "flashcard_id" not in fc:
                    # Fallback if ID missing in DB content (unlikely with new schema)
                    fc_idx = flashcards.index(fc) + 1
                    fc["flashcard_id"] = f"{course_id}_L{deck_id}_FC{fc_idx:03d}"
            
            all_flashcards.extend(flashcards)
        
        if not all_flashcards:
            raise ValueError(f"No flashcards found for decks: {deck_ids}")
        
        # Sort by relevance_score (highest first), then by flashcard_id (ascending) for consistent ordering
        all_flashcards.sort(
            key=lambda fc: (
                -fc.get("relevance_score", 0) if isinstance(fc.get("relevance_score"), (int, float)) else 0,
                fc.get("flashcard_id", "")  # Secondary sort by ID (ascending)
            )
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
        session_uuid = uuid4()
        session_id = f"mix_{session_uuid.hex[:16]}"
        now = datetime.now(timezone.utc)
        
        # Save to PostgreSQL
        query = """
            INSERT INTO mix_sessions (
                session_id, user_id, course_id, deck_ids, status, current_round,
                flashcard_master_order, activity_queue, seen_in_current_round,
                asked_question_hashes, created_at, last_updated
            )
            VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7::jsonb, $8::jsonb, $9::jsonb, $10::jsonb, $11, $11)
            RETURNING session_id
        """
        
        activity_queue_json = [a.model_dump() for a in activity_queue]
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                session_id, # Pass string directly
                user_id,
                course_id,
                json.dumps(deck_ids),
                "in_progress",
                1,
                json.dumps(flashcard_master_order),
                json.dumps(activity_queue_json),
                json.dumps([]),
                json.dumps([]),
                now
            )
        
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
        session_data = await self.get_session_data(session_id, user_id)
        if not session_data:
            return None
        
        # Convert activity_queue back to MixActivity objects
        activity_queue = []
        for a in session_data.get("activity_queue", []):
            activity_queue.append(MixActivity(**a))
        
        session = MixSession(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            course_id=session_data["course_id"],
            deck_ids=session_data["deck_ids"],
            status=session_data["status"],
            current_round=session_data["current_round"],
            flashcard_master_order=session_data["flashcard_master_order"],
            activity_queue=activity_queue,
            seen_in_current_round=session_data["seen_in_current_round"],
            asked_question_hashes=session_data["asked_question_hashes"],
            created_at=session_data["created_at"],
            last_updated=session_data["last_updated"]
        )
        
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
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
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
        await self._update_session(session_id, {
            "activity_queue": [act.model_dump() for act in session.activity_queue],
            "seen_in_current_round": session.seen_in_current_round
        })
        
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
                await self._update_session(session_id, {
                    "asked_question_hashes": session.asked_question_hashes
                })
                
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
                
                # Remove this activity and try again (already popped above)
                await self._update_session(session_id, {
                    "activity_queue": [a.model_dump() for a in session.activity_queue]
                })
                
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
        flashcard_service = FlashcardPerformanceService(self.pool)
        
        # Fetch session to get course_id
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        course_id = session.course_id
        
        # Extract lecture_id from flashcard_id
        # Format: {course_code}_L{lecture_id}_FC{index} -> L{lecture_id} -> {lecture_id}
        # Or fallback to simpler parsing if ID format varies
        lecture_id = "unknown"
        if "_L" in flashcard_id:
            try:
                # Example: MS5150_L2_FC001 -> 2
                lecture_part = flashcard_id.split("_L")[1] # 2_FC001
                lecture_id = lecture_part.split("_")[0] # 2
            except Exception:
                # Fallback logic
                parts = flashcard_id.rsplit("_", 1)
                lecture_id = parts[0] if len(parts) > 1 else flashcard_id
        else:
             # Legacy fallback
             parts = flashcard_id.rsplit("_", 1)
             lecture_id = parts[0] if len(parts) > 1 else flashcard_id
        
        # Create a QuestionResult for the service
        question_result = QuestionResult(
            question_id=question_hash,
            source_flashcard_id=flashcard_id,
            question_type="mcq",  # We'll assume MCQ for now
            question=str(user_answer),
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
        
        # Inject remediation if user earned 0 points (completely wrong) and not a follow-up
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
    
    async def get_flashcard_for_reference(
        self,
        course_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get flashcard content for reference/display purposes.
        Public method that can be called from API endpoints.
        
        Args:
            course_id: Course identifier
            flashcard_id: Flashcard identifier
            
        Returns:
            Full flashcard content or None if not found
        """
        return await self._load_flashcard_content(course_id, flashcard_id)
    
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
        flashcard_perf = await self._get_flashcard_performance(user_id, flashcard_id)
        
        next_level = "medium"  # Default
        if flashcard_perf:
            next_level = flashcard_perf.get("next_level", "medium")
            cs = flashcard_perf.get("comfortability_score", 0.0)
            logger.info(f"Flashcard performance found - CS: {cs:.2f}, next_level: {next_level}")
        else:
            logger.warning(f"No flashcard performance found for {flashcard_id}, using default level: {next_level}")
        
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
        
        logger.info(f"Created remediation activities: flashcard_review + follow_up_question at level {next_level}")
        
        # Get current session and prepend to activity queue
        session = await self.get_session(session_id, user_id)
        if session:
            new_queue = [flashcard_review, follow_up_question] + session.activity_queue
            await self._update_session(session_id, {
                "activity_queue": [a.model_dump() for a in new_queue]
            })
            logger.info(f"Successfully injected remediation for flashcard {flashcard_id} at level {next_level}")
        else:
            logger.error(f"Failed to inject remediation - session {session_id} not found")
    
    async def _generate_next_round(self, session: MixSession):
        """
        Generate the next round of questions based on question_next_level.
        
        Args:
            session: The current session
        """
        new_queue = []
        
        for flashcard_id in session.flashcard_master_order:
            # Get the question_next_level for this flashcard
            flashcard_perf = await self._get_flashcard_performance(session.user_id, flashcard_id)
            
            level = "easy"  # Default for new flashcards
            if flashcard_perf:
                level = flashcard_perf.get("next_level", "easy")
            
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
        
        await self._update_session(session.session_id, {
            "activity_queue": [act.model_dump() for act in new_queue],
            "seen_in_current_round": [],
            "current_round": session.current_round
        })
        
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
        # Note: We now track this via user_quiz_attempts in PostgreSQL
        # For simplicity, if all questions have been seen, just return a random one
        # The flashcard performance tracking already handles the adaptive difficulty
        
        # Priority 3: Random question (all have been seen)
        return random.choice(flashcard_questions)
    
    async def _load_flashcards_for_deck(
        self,
        course_id: str,
        deck_id: str
    ) -> List[Dict[str, Any]]:
        """Load flashcards from DB via AdaptiveQuizService."""
        # Map dictionary returned by AdaptiveQuizService to list of dicts
        flashcard_map = await self.quiz_service.load_flashcards(course_id, deck_id)
        
        flashcards_list = []
        for fc_id, metadata in flashcard_map.items():
            # Reconstruct a flashcard object from metadata
            fc_obj = {
                "flashcard_id": fc_id,
                "relevance_score": metadata.get("relevance_score"),
                "question": metadata.get("question"),
                "tags": metadata.get("tags")
            }
            flashcards_list.append(fc_obj)
            
        return flashcards_list
    
    async def _load_flashcard_content(
        self,
        course_id: str,
        flashcard_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load the full content of a specific flashcard."""
        # Extract deck_id from flashcard_id
        if "_L" in flashcard_id:
            try:
                lecture_part = flashcard_id.split("_L")[1]
                deck_id = lecture_part.split("_")[0]
            except IndexError:
                parts = flashcard_id.rsplit("_", 1)
                deck_id = parts[0] if len(parts) > 1 else flashcard_id
        else:
            parts = flashcard_id.rsplit("_", 1)
            deck_id = parts[0] if len(parts) > 1 else flashcard_id
            
        repo = self.quiz_service.repository
        if not repo:
            return None
            
        try:
            # Try to parse deck_id as int
            lecture_id_int = int(deck_id)
            lecture = await repo.get_lecture_by_id(lecture_id_int)
            if not lecture:
                return None
                
            flashcards_data = lecture.get('flashcards')
            if isinstance(flashcards_data, str):
                flashcards_data = json.loads(flashcards_data)
                
            if isinstance(flashcards_data, dict):
                flashcards = flashcards_data.get('flashcards', [])
            elif isinstance(flashcards_data, list):
                flashcards = flashcards_data
            else:
                flashcards = []
                
            for fc in flashcards:
                if fc.get('id') == flashcard_id or fc.get('flashcard_id') == flashcard_id:
                    return fc
            
            return None
            
        except (ValueError, Exception) as e:
            logger.error(f"Error loading flashcard content for {flashcard_id}: {e}")
            return None
    
    async def _load_questions_for_level(
        self,
        course_id: str,
        flashcard_id: str,
        level: str
    ) -> List[Dict[str, Any]]:
        """Load questions for a specific level from DB via AdaptiveQuizService."""
        # Map level string to int (1-4)
        level_map = {"easy": 1, "medium": 2, "hard": 3, "boss": 4}
        level_int = level_map.get(level, 2)
        
        # Extract deck_id
        if "_L" in flashcard_id:
            try:
                lecture_part = flashcard_id.split("_L")[1]
                deck_id = lecture_part.split("_")[0]
            except IndexError:
                parts = flashcard_id.rsplit("_", 1)
                deck_id = parts[0] if len(parts) > 1 else flashcard_id
        else:
            parts = flashcard_id.rsplit("_", 1)
            deck_id = parts[0] if len(parts) > 1 else flashcard_id
            
        return await self.quiz_service.load_quiz_questions(course_id, deck_id, level_int)
    
    def _hash_question(self, question_text: str) -> str:
        """Generate a deterministic hash for a question."""
        return self.quiz_service.hash_question(question_text)
    
    def _normalize_correct_answer(self, question: Dict[str, Any]) -> List[str]:
        """Normalize correct_answer using AdaptiveQuizService logic."""
        # AdaptiveQuizService already does this normalization when loading questions
        if hasattr(self.quiz_service, '_normalize_correct_answer'):
             return self.quiz_service._normalize_correct_answer(question)
        return []
    
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
    
    async def reveal_answer(
        self,
        session_id: str,
        user_id: str,
        flashcard_id: str,
        question_hash: str,
        level: str,
        is_follow_up: bool
    ) -> MixRevealResponse:
        """
        Reveal answer without recording performance.
        Still triggers remediation if not a follow-up question.
        
        Args:
            session_id: Session identifier
            user_id: Firebase UID
            flashcard_id: The flashcard ID
            question_hash: Hash of the question
            level: Question difficulty level
            is_follow_up: Whether this was a follow-up question
            
        Returns:
            MixRevealResponse with correct answer and remediation status
        """
        # Retrieve session
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Load question to get correct answer and explanation
        question = await self._load_question_by_hash(
            session.course_id,
            flashcard_id,
            level,
            question_hash
        )
        
        if not question:
            raise ValueError(f"Question not found for hash {question_hash}")
        
        correct_answer = question.get("correct_answer")
        explanation = question.get("explanation")
        
        # Remove question_hash from asked_question_hashes (allows reappearance)
        if question_hash in session.asked_question_hashes:
            session.asked_question_hashes.remove(question_hash)
            await self._update_session(session_id, {
                "asked_question_hashes": session.asked_question_hashes
            })
        logger.info(f"Removed question_hash {question_hash} from asked_question_hashes")
        
        # Inject remediation if not a follow-up question
        remediation_injected = False
        if not is_follow_up:
            logger.info(f"🔄 Injecting remediation for revealed answer on flashcard {flashcard_id}")
            await self._inject_remediation(session_id, flashcard_id, user_id)
            remediation_injected = True
        else:
            logger.info(f"⏭️ Skipping remediation - this was a follow-up question")
        
        return MixRevealResponse(
            correct_answer=correct_answer,
            explanation=explanation,
            remediation_injected=remediation_injected
        )
    
    async def _load_question_by_hash(
        self,
        course_id: str,
        flashcard_id: str,
        level: str,
        question_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load a specific question by its hash.
        
        Args:
            course_id: Course identifier
            flashcard_id: Flashcard identifier
            level: Question difficulty level
            question_hash: Hash of the question text
            
        Returns:
            Question dict or None if not found
        """
        # Load all questions for this level
        questions = await self._load_questions_for_level(course_id, flashcard_id, level)
        
        if not questions:
            return None
        
        # Filter questions by flashcard_id
        flashcard_questions = [
            q for q in questions
            if q.get("source_flashcard_id") == flashcard_id
        ]
        
        # Find question by hash
        for q in flashcard_questions:
            if self._hash_question(q["question_text"]) == question_hash:
                return q
        
        return None
    
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


async def get_mix_session_service() -> MixSessionService:
    """Dependency injection helper with PostgreSQL pool."""
    from app.db.postgres import get_postgres_pool
    pool = await get_postgres_pool()
    return MixSessionService(pool)

