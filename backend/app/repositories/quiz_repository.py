"""
Quiz repository - PostgreSQL queries for quiz sessions, results, exam readiness, and timetables.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
import asyncpg

logger = logging.getLogger(__name__)


class QuizRepository:
    """Repository for quiz-related database operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Quiz Sessions Operations ====================
    
    async def create_quiz_session(
        self,
        firebase_uid: str,
        course_id: str,
        deck_id: str,
        difficulty: str,
        questions: List[Dict[str, Any]]
    ) -> str:
        """
        Create a new quiz session.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Course identifier
            deck_id: Deck identifier
            difficulty: Quiz difficulty level
            questions: List of question objects
            
        Returns:
            quiz_id: UUID string for the new session
        """
        quiz_id = uuid4()
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO quiz_sessions (
                quiz_id, firebase_uid, course_id, deck_id, difficulty,
                questions, completed, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, FALSE, $7)
            RETURNING quiz_id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                quiz_id, firebase_uid, course_id, deck_id, difficulty,
                json.dumps(questions), now
            )
            
            result_id = str(row["quiz_id"])
            logger.info(f"Created quiz session {result_id} for user {firebase_uid}")
            return result_id
    
    async def get_quiz_session(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a quiz session by ID.
        
        Args:
            quiz_id: Quiz UUID string
            
        Returns:
            Quiz session dict or None
        """
        query = """
            SELECT 
                quiz_id, firebase_uid, course_id, deck_id, difficulty,
                questions, completed, created_at, completed_at
            FROM quiz_sessions
            WHERE quiz_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(quiz_id))
            
            if not row:
                return None
            
            result = dict(row)
            result["quiz_id"] = str(result["quiz_id"])
            if isinstance(result.get("questions"), str):
                result["questions"] = json.loads(result["questions"])
            
            return result
    
    async def complete_quiz_session(self, quiz_id: str) -> bool:
        """
        Mark a quiz session as completed.
        
        Args:
            quiz_id: Quiz UUID string
            
        Returns:
            True if updated
        """
        now = datetime.now(timezone.utc)
        
        query = """
            UPDATE quiz_sessions
            SET completed = TRUE, completed_at = $2
            WHERE quiz_id = $1
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, UUID(quiz_id), now)
            return row is not None
    
    async def get_active_sessions_for_user(
        self,
        firebase_uid: str,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active (incomplete) quiz sessions for a user.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Optional course filter
            
        Returns:
            List of active quiz sessions
        """
        if course_id:
            query = """
                SELECT quiz_id, course_id, deck_id, difficulty, created_at
                FROM quiz_sessions
                WHERE firebase_uid = $1 AND course_id = $2 AND completed = FALSE
                ORDER BY created_at DESC
            """
            params = [firebase_uid, course_id]
        else:
            query = """
                SELECT quiz_id, course_id, deck_id, difficulty, created_at
                FROM quiz_sessions
                WHERE firebase_uid = $1 AND completed = FALSE
                ORDER BY created_at DESC
            """
            params = [firebase_uid]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            results = []
            for row in rows:
                result = dict(row)
                result["quiz_id"] = str(result["quiz_id"])
                results.append(result)
            
            return results
    
    # ==================== Quiz Results Operations ====================
    
    async def save_quiz_result(
        self,
        firebase_uid: str,
        course_id: str,
        lecture_id: str,
        deck_id: str,
        difficulty: str,
        score: int,
        total_questions: int,
        percentage: float,
        time_taken: Optional[int],
        question_results: List[Dict[str, Any]],
        quiz_id: Optional[str] = None
    ) -> int:
        """
        Save a completed quiz result.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Course identifier
            lecture_id: Lecture identifier
            deck_id: Deck identifier
            difficulty: Quiz difficulty
            score: Number of correct answers
            total_questions: Total number of questions
            percentage: Score percentage
            time_taken: Time taken in seconds
            question_results: List of question result objects
            quiz_id: Optional quiz session ID
            
        Returns:
            ID of the created result
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO quiz_results (
                firebase_uid, course_id, lecture_id, deck_id, quiz_id,
                difficulty, score, total_questions, percentage,
                time_taken, question_results, completed_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                firebase_uid, course_id, lecture_id, deck_id,
                UUID(quiz_id) if quiz_id else None,
                difficulty, score, total_questions, percentage,
                time_taken, json.dumps(question_results), now
            )
            
            logger.info(f"Saved quiz result for user {firebase_uid}: {score}/{total_questions}")
            return row["id"]
    
    async def get_user_quiz_history(
        self,
        firebase_uid: str,
        course_id: Optional[str] = None,
        lecture_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get quiz history for a user.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Optional course filter
            lecture_id: Optional lecture filter
            limit: Maximum results to return
            
        Returns:
            List of quiz results
        """
        base_query = """
            SELECT 
                id, firebase_uid, course_id, lecture_id, deck_id, quiz_id,
                difficulty, score, total_questions, percentage,
                time_taken, question_results, completed_at
            FROM quiz_results
            WHERE firebase_uid = $1
        """
        
        params = [firebase_uid]
        param_idx = 2
        
        if course_id:
            base_query += f" AND course_id = ${param_idx}"
            params.append(course_id)
            param_idx += 1
        
        if lecture_id:
            base_query += f" AND lecture_id = ${param_idx}"
            params.append(lecture_id)
            param_idx += 1
        
        base_query += f" ORDER BY completed_at DESC LIMIT ${param_idx}"
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(base_query, *params)
            
            results = []
            for row in rows:
                result = dict(row)
                if result.get("quiz_id"):
                    result["quiz_id"] = str(result["quiz_id"])
                if isinstance(result.get("question_results"), str):
                    result["question_results"] = json.loads(result["question_results"])
                results.append(result)
            
            return results
    
    async def get_quiz_stats_for_lecture(
        self,
        firebase_uid: str,
        course_id: str,
        lecture_id: str
    ) -> Dict[str, Any]:
        """
        Get aggregated quiz statistics for a lecture.
        
        Args:
            firebase_uid: Firebase user ID
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            Stats dict with total attempts, average score, etc.
        """
        query = """
            SELECT 
                COUNT(*) as total_attempts,
                AVG(percentage) as avg_percentage,
                MAX(percentage) as best_percentage,
                SUM(score) as total_correct,
                SUM(total_questions) as total_questions,
                MAX(completed_at) as last_attempt
            FROM quiz_results
            WHERE firebase_uid = $1 AND course_id = $2 AND lecture_id = $3
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, firebase_uid, course_id, lecture_id)
            
            return {
                "total_attempts": row["total_attempts"] or 0,
                "avg_percentage": round(row["avg_percentage"] or 0, 2),
                "best_percentage": round(row["best_percentage"] or 0, 2),
                "total_correct": row["total_correct"] or 0,
                "total_questions": row["total_questions"] or 0,
                "last_attempt": row["last_attempt"]
            }
    
    # ==================== Exam Readiness Operations ====================
    
    async def get_exam_readiness(
        self,
        user_id: str,
        exam_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get exam readiness for a user and exam.
        
        Args:
            user_id: Firebase user ID
            exam_id: Exam identifier
            
        Returns:
            Readiness dict or None
        """
        query = """
            SELECT 
                user_id, exam_id, course_id, overall_readiness_score,
                coverage_factor, accuracy_factor, momentum_factor,
                raw_scores, max_possible_scores, weak_flashcards,
                total_flashcards_in_exam, flashcards_attempted, last_calculated
            FROM user_exam_readiness
            WHERE user_id = $1 AND exam_id = $2
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, exam_id)
            
            if not row:
                return None
            
            result = dict(row)
            # Parse JSONB fields
            for field in ["raw_scores", "max_possible_scores", "weak_flashcards"]:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            
            return result
    
    async def save_exam_readiness(
        self,
        user_id: str,
        exam_id: str,
        course_id: str,
        overall_readiness_score: float,
        coverage_factor: float,
        accuracy_factor: float,
        momentum_factor: float,
        raw_scores: Dict[str, Any],
        max_possible_scores: Dict[str, Any],
        weak_flashcards: List[Dict[str, Any]],
        total_flashcards_in_exam: int,
        flashcards_attempted: int
    ) -> Dict[str, Any]:
        """
        Save or update exam readiness.
        
        Returns:
            Saved readiness dict
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO user_exam_readiness (
                user_id, exam_id, course_id, overall_readiness_score,
                coverage_factor, accuracy_factor, momentum_factor,
                raw_scores, max_possible_scores, weak_flashcards,
                total_flashcards_in_exam, flashcards_attempted, last_calculated
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb, $11, $12, $13)
            ON CONFLICT (user_id, exam_id)
            DO UPDATE SET
                overall_readiness_score = $4,
                coverage_factor = $5,
                accuracy_factor = $6,
                momentum_factor = $7,
                raw_scores = $8::jsonb,
                max_possible_scores = $9::jsonb,
                weak_flashcards = $10::jsonb,
                total_flashcards_in_exam = $11,
                flashcards_attempted = $12,
                last_calculated = $13
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                user_id, exam_id, course_id, overall_readiness_score,
                coverage_factor, accuracy_factor, momentum_factor,
                json.dumps(raw_scores), json.dumps(max_possible_scores),
                json.dumps(weak_flashcards),
                total_flashcards_in_exam, flashcards_attempted, now
            )
            
            result = dict(row)
            for field in ["raw_scores", "max_possible_scores", "weak_flashcards"]:
                if isinstance(result.get(field), str):
                    result[field] = json.loads(result[field])
            
            logger.info(f"Saved exam readiness for user {user_id}, exam {exam_id}: {overall_readiness_score:.1f}%")
            return result
    
    async def get_user_exam_readiness_all(
        self,
        user_id: str,
        course_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all exam readiness records for a user.
        
        Args:
            user_id: Firebase user ID
            course_id: Optional course filter
            
        Returns:
            List of readiness records
        """
        if course_id:
            query = """
                SELECT 
                    user_id, exam_id, course_id, overall_readiness_score,
                    coverage_factor, accuracy_factor, momentum_factor,
                    total_flashcards_in_exam, flashcards_attempted, last_calculated
                FROM user_exam_readiness
                WHERE user_id = $1 AND course_id = $2
                ORDER BY last_calculated DESC
            """
            params = [user_id, course_id]
        else:
            query = """
                SELECT 
                    user_id, exam_id, course_id, overall_readiness_score,
                    coverage_factor, accuracy_factor, momentum_factor,
                    total_flashcards_in_exam, flashcards_attempted, last_calculated
                FROM user_exam_readiness
                WHERE user_id = $1
                ORDER BY last_calculated DESC
            """
            params = [user_id]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # ==================== Timetables Operations ====================
    
    async def get_timetable(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Get timetable for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Timetable dict or None
        """
        query = """
            SELECT id, course_id, exams, created_at, updated_at
            FROM course_timetables
            WHERE course_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, course_id)
            
            if not row:
                return None
            
            result = dict(row)
            if isinstance(result.get("exams"), str):
                result["exams"] = json.loads(result["exams"])
            
            return result
    
    async def save_timetable(
        self,
        course_id: str,
        exams: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Save or update a course timetable.
        
        Args:
            course_id: Course identifier
            exams: List of exam objects with exam_id, subject, lectures, etc.
            
        Returns:
            Saved timetable dict
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO course_timetables (course_id, exams, created_at, updated_at)
            VALUES ($1, $2::jsonb, $3, $3)
            ON CONFLICT (course_id)
            DO UPDATE SET
                exams = $2::jsonb,
                updated_at = $3
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, course_id, json.dumps(exams), now)
            
            result = dict(row)
            if isinstance(result.get("exams"), str):
                result["exams"] = json.loads(result["exams"])
            
            logger.info(f"Saved timetable for course {course_id} with {len(exams)} exams")
            return result
    
    async def get_exam_lectures(
        self,
        course_id: str,
        exam_id: str
    ) -> List[str]:
        """
        Get list of lecture IDs for an exam.
        
        Args:
            course_id: Course identifier
            exam_id: Exam identifier
            
        Returns:
            List of lecture IDs
        """
        timetable = await self.get_timetable(course_id)
        
        if not timetable:
            return []
        
        for exam in timetable.get("exams", []):
            if exam.get("exam_id") == exam_id:
                return exam.get("lectures", [])
        
        return []
    
    async def get_exams_containing_lecture(
        self,
        course_id: str,
        lecture_id: str
    ) -> List[Dict[str, str]]:
        """
        Find all exams that include a specific lecture.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            
        Returns:
            List of dicts with exam_id and exam_name
        """
        timetable = await self.get_timetable(course_id)
        
        if not timetable:
            return []
        
        matching_exams = []
        for exam in timetable.get("exams", []):
            lectures = exam.get("lectures", [])
            
            if lecture_id in lectures:
                matching_exams.append({
                    "exam_id": exam.get("exam_id"),
                    "exam_name": exam.get("subject", exam.get("exam_id"))
                })
        
        return matching_exams
    
    async def delete_timetable(self, course_id: str) -> bool:
        """
        Delete a course timetable.
        
        Args:
            course_id: Course identifier
            
        Returns:
            True if deleted
        """
        query = """
            DELETE FROM course_timetables
            WHERE course_id = $1
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, course_id)
            return row is not None


