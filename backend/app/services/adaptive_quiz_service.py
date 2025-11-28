"""Adaptive quiz engine service for personalized question selection."""

import json
import hashlib
import random
import logging
import asyncpg
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.repositories.content_repository import ContentRepository

logger = logging.getLogger(__name__)


class AdaptiveQuizService:
    """Service for adaptive quiz question selection based on user performance."""
    
    def __init__(self, pool: Optional[asyncpg.Pool] = None, courses_dir: Optional[str] = None):
        self.pool = pool
        if pool:
            self.repository = ContentRepository(pool)
        else:
            self.repository = None
            logger.warning("AdaptiveQuizService initialized without PostgreSQL pool. DB operations will fail.")
        
        # Keep courses_dir for backward compatibility if needed, but prefer DB
        if courses_dir is None:
            backend_dir = Path(__file__).parent.parent.parent
            courses_dir = str(backend_dir / "courses")
        self.courses_dir = Path(courses_dir)
    
    @staticmethod
    def hash_question(question_text: str) -> str:
        """
        Generate a unique hash for a question based on its text.
        
        Args:
            question_text: The question text
            
        Returns:
            MD5 hash of the question text
        """
        return hashlib.md5(question_text.encode()).hexdigest()[:16]
    
    async def _get_lecture_id_int(self, lecture_id: str) -> Optional[int]:
        """Helper to convert lecture_id string to int."""
        try:
            return int(lecture_id)
        except ValueError:
            logger.warning(f"Invalid lecture ID format: {lecture_id} (expected integer)")
            return None

    async def load_flashcards(
        self,
        course_id: str,
        lecture_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load all flashcards for a lecture from the database and extract metadata.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier (database ID)
            
        Returns:
            Dict mapping flashcard_id to flashcard metadata (relevance_score, etc.)
        """
        if not self.repository:
            logger.error("Repository not initialized")
            return {}

        lec_id_int = await self._get_lecture_id_int(lecture_id)
        if lec_id_int is None:
            return {}

        lecture = await self.repository.get_lecture_by_id(lec_id_int)
        if not lecture:
            logger.error(f"Lecture {lecture_id} not found in database")
            return {}

        try:
            # flashcards column is JSONB, asyncpg returns it as a python object (dict/list) or string
            flashcards_data = lecture.get('flashcards')
            
            if not flashcards_data:
                return {}
                
            if isinstance(flashcards_data, str):
                flashcards_data = json.loads(flashcards_data)
            
            # Handle structure: {"flashcards": [...]} or just [...]
            if isinstance(flashcards_data, dict):
                flashcards = flashcards_data.get('flashcards', [])
            elif isinstance(flashcards_data, list):
                flashcards = flashcards_data
            else:
                flashcards = []
            
            # Create a mapping of flashcard_id -> metadata
            flashcard_map = {}
            for card in flashcards:
                # Handle both 'id' and 'flashcard_id' keys
                flashcard_id = card.get('id') or card.get('flashcard_id')
                if flashcard_id:
                    # relevance_score might be object or int
                    numeric_relevance = 0
                    try:
                        rs = card.get('relevance_score')
                        if isinstance(rs, dict):
                            numeric_relevance = rs.get('score', 0)
                        elif isinstance(rs, (int, float)):
                            numeric_relevance = rs
                    except Exception:
                        numeric_relevance = 0

                    flashcard_map[flashcard_id] = {
                        'relevance_score': numeric_relevance,
                        'question': card.get('front', '') or card.get('question', ''),
                        'tags': card.get('tags', [])
                    }
            
            logger.info(f"Loaded {len(flashcard_map)} flashcards for lecture {lecture_id}")
            return flashcard_map
        
        except Exception as e:
            logger.error(f"Error parsing flashcards for lecture {lecture_id}: {e}")
            return {}
    
    async def load_quiz_questions(
        self,
        course_id: str,
        lecture_id: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Load all questions for a specific quiz level from the database.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier (database ID)
            level: Difficulty level (1-4)
            
        Returns:
            List of question objects
        """
        if not self.repository:
            logger.error("Repository not initialized")
            return []

        lec_id_int = await self._get_lecture_id_int(lecture_id)
        if lec_id_int is None:
            return []

        lecture = await self.repository.get_lecture_by_id(lec_id_int)
        if not lecture:
            logger.error(f"Lecture {lecture_id} not found in database")
            return []

        try:
            quizzes_data = lecture.get('quizzes')
            if not quizzes_data:
                logger.warning(f"No quizzes found for lecture {lecture_id}")
                return []
                
            if isinstance(quizzes_data, str):
                quizzes_data = json.loads(quizzes_data)
            
            # Handle structure: {"levels": [{"level": 1, "questions": [...]}, ...]}
            questions = []
            
            # Check for "levels" list structure (new format)
            if isinstance(quizzes_data, dict) and "levels" in quizzes_data:
                levels = quizzes_data.get("levels", [])
                for lvl_data in levels:
                    if lvl_data.get("level") == level:
                        questions = lvl_data.get("questions", [])
                        break
            
            # Fallback to flat dict structure (old format: {"level_1": [...]})
            elif isinstance(quizzes_data, dict):
                level_key = f"level_{level}"
                questions = quizzes_data.get(level_key, [])
            
            if not questions:
                logger.warning(f"No questions found for {lecture_id} level {level} in quiz data")
                return []
            
            # Add question_hash and normalize correct_answer
            for question in questions:
                question['question_hash'] = self.hash_question(question['question_text'])
                question['correct_answer'] = self._normalize_correct_answer(question)
            
            logger.info(f"Loaded {len(questions)} questions for {lecture_id} level {level}")
            return questions
        
        except Exception as e:
            logger.error(f"Error loading quiz questions for lecture {lecture_id}: {e}")
            return []
    
    @staticmethod
    def _normalize_correct_answer(question: Dict[str, Any]) -> List[str]:
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
            # Strip leading option label like "a.", "b)", "c:", or just "d "
            text = re.sub(r'^[a-d]\s*[\.\):\-]?\s*', '', text, flags=re.IGNORECASE)
            # Remove common punctuation and markdown formatting
            text = text.replace('.', '').replace(',', '').replace('*', '').replace('_', '')
            text = text.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            text = text.replace('"', '').replace("'", '').replace(':', '').replace(';', '')
            text = text.replace('`', '')  # Remove backticks for code formatting
            # Collapse multiple whitespace into single space
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        def extract_letter_heuristic(value_str):
            """Try to extract option letter from explanatory text."""
            # Heuristic 1: "Option C" or "Approach D" pattern
            label_match = re.search(r'\b(?:option|approach)\s+([a-d])\b', value_str, re.IGNORECASE)
            if label_match:
                return label_match.group(1).upper()
            
            # Heuristic 2: First letter followed by space/punctuation
            first_match = re.match(r'^\s*([a-d])[\s:.\)\-\]]+', value_str, re.IGNORECASE)
            if first_match:
                return first_match.group(1).upper()
            
            return None
        
        # Special-case: some legacy questions split a single long answer across
        # multiple strings in the correct_answer array (e.g., ["B: ...", "such as ...", "shifting ..."]).
        # First, try to join them and match once against full option texts.
        if len(raw_list) > 1:
            joined_value = " ".join(str(item or '') for item in raw_list).strip()
            if joined_value:
                match_key = next(
                    (k for k in option_keys if norm(options[k]) == norm(joined_value)),
                    None
                )
                if match_key:
                    logger.info(
                        "✅ Normalized multi-part correct_answer to key '%s' for question: %s",
                        match_key,
                        question.get('question_text', '')[:60],
                    )
                    return [match_key]

            # If the joined text doesn't exactly match any option, try a softer
            # heuristic: find an option whose normalized text contains ALL of the
            # normalized fragments (useful when the correct_answer is a set of
            # key phrases taken from the full option text).
            fragment_texts = [norm(item) for item in raw_list if norm(item)]
            if fragment_texts:
                candidate_keys = []
                for k in option_keys:
                    opt_text = norm(options[k])
                    if all(fragment in opt_text for fragment in fragment_texts):
                        candidate_keys.append(k)
                if len(candidate_keys) == 1:
                    logger.info(
                        "✅ Heuristically mapped multi-part correct_answer to key '%s' for question: %s",
                        candidate_keys[0],
                        question.get('question_text', '')[:60],
                    )
                    return [candidate_keys[0]]
        
        keys = []
        for item in raw_list:
            value = str(item or '').strip()
            if not value:
                continue
            
            # Case 1: Already an option key
            if value in option_keys:
                keys.append(value)
                continue
            
            # Case 2: Try letter extraction heuristics first
            extracted_letter = extract_letter_heuristic(value)
            if extracted_letter and extracted_letter in option_keys:
                keys.append(extracted_letter)
                logger.debug(
                    "✅ Extracted option key '%s' from explanatory text for question: %s",
                    extracted_letter,
                    question.get('question_text', '')[:60],
                )
                continue
            
            # Case 3: Match by option text
            match_key = next(
                (k for k in option_keys if norm(options[k]) == norm(value)),
                None
            )
            if match_key:
                keys.append(match_key)
                logger.debug(
                    "✅ Normalized answer text to key '%s' for question: %s",
                    match_key,
                    question.get('question_text', '')[:60],
                )
            else:
                # Fallback: keep the raw value (will cause issues, but only log at debug level)
                logger.debug(
                    "⚠️ Could not normalize correct_answer '%s' to option key for question: %s",
                    value[:100],
                    question.get('question_text', '')[:60],
                )
                keys.append(value)
        
        return keys
    
    async def select_coverage_first_questions(
        self,
        all_questions: List[Dict[str, Any]],
        flashcard_metadata: Dict[str, Dict[str, Any]],
        seen_flashcard_ids: set,
        size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Select questions prioritizing concept coverage based on relevance scores.
        
        Discovery Phase Algorithm:
        1. Identify all flashcard_ids that have never been tested
        2. Sort unseen flashcards by relevance_score (descending)
        3. Select one question from each unseen flashcard (most relevant first)
        4. If we still need more questions, fill with reinforcement questions
        
        Args:
            all_questions: All available questions for this level
            flashcard_metadata: Dict mapping flashcard_id to metadata (relevance_score, etc.)
            seen_flashcard_ids: Set of flashcard_ids the user has been tested on
            size: Number of questions to select
            
        Returns:
            List of selected question objects
        """
        if not all_questions:
            return []
        
        # Get all available flashcard_ids from questions
        available_flashcard_ids = set()
        flashcard_to_questions = {}  # Map flashcard_id to list of questions
        
        for question in all_questions:
            flashcard_id = question.get('source_flashcard_id', '')
            if flashcard_id:
                available_flashcard_ids.add(flashcard_id)
                if flashcard_id not in flashcard_to_questions:
                    flashcard_to_questions[flashcard_id] = []
                flashcard_to_questions[flashcard_id].append(question)
        
        # Identify unseen flashcards
        unseen_flashcard_ids = available_flashcard_ids - seen_flashcard_ids
        
        logger.info(f"Coverage analysis: {len(available_flashcard_ids)} total concepts, "
                   f"{len(seen_flashcard_ids)} seen, {len(unseen_flashcard_ids)} unseen")
        
        selected_questions = []
        
        # DISCOVERY PHASE: Prioritize unseen concepts
        if unseen_flashcard_ids:
            # Sort unseen flashcards by relevance_score (descending)
            unseen_sorted = sorted(
                unseen_flashcard_ids,
                key=lambda fid: flashcard_metadata.get(fid, {}).get('relevance_score', 0),
                reverse=True
            )
            
            # Select one question from each unseen flashcard (in relevance order)
            for flashcard_id in unseen_sorted:
                if len(selected_questions) >= size:
                    break
                
                questions_for_flashcard = flashcard_to_questions.get(flashcard_id, [])
                if questions_for_flashcard:
                    # Pick a random question from this flashcard
                    selected_questions.append(random.choice(questions_for_flashcard))
            
            logger.info(f"Discovery phase: Selected {len(selected_questions)} questions from unseen concepts")
        
        # If we still need more questions, fill with questions from seen concepts
        if len(selected_questions) < size and seen_flashcard_ids:
            remaining_size = size - len(selected_questions)
            
            # Get questions from seen flashcards
            seen_questions = [
                q for q in all_questions 
                if q.get('source_flashcard_id', '') in seen_flashcard_ids
            ]
            
            # Randomly select from seen questions to fill the gap
            if seen_questions:
                fill_questions = random.sample(
                    seen_questions,
                    min(remaining_size, len(seen_questions))
                )
                selected_questions.extend(fill_questions)
                logger.info(f"Reinforcement fill: Added {len(fill_questions)} questions from seen concepts")
        
        # Shuffle to randomize order
        random.shuffle(selected_questions)
        
        return selected_questions
    
    async def select_adaptive_questions(
        self,
        all_questions: List[Dict[str, Any]],
        weakness_scores: Dict[str, float],
        attempted_questions: set,
        size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Select questions adaptively based on user's weakness scores.
        
        Reinforcement Phase Algorithm:
        1. Calculate weight for each question based on its source flashcard's weakness score
        2. Boost weight for new (unattempted) questions
        3. Use weighted random sampling to select questions
        
        Args:
            all_questions: All available questions for this level
            weakness_scores: Dict mapping flashcard_id to weakness score
            attempted_questions: Set of question hashes user has already seen
            size: Number of questions to select
            
        Returns:
            List of selected question objects
        """
        if not all_questions:
            return []
        
        # If we have fewer questions than requested, return all
        if len(all_questions) <= size:
            return all_questions
        
        # Calculate weights for each question
        weighted_questions = []
        
        for question in all_questions:
            flashcard_id = question.get('source_flashcard_id', '')
            question_hash = question.get('question_hash', '')
            
            # Base weight from weakness score (higher score = more weight)
            base_weight = weakness_scores.get(flashcard_id, 1.5)  # Default 1.5 for new flashcards
            
            # Boost weight for unattempted questions (encourage exploration)
            if question_hash not in attempted_questions:
                base_weight *= 1.3  # 30% boost for new questions
            
            weighted_questions.append((question, base_weight))
        
        # Perform weighted random sampling
        questions_list, weights_list = zip(*weighted_questions)
        
        selected = random.choices(
            questions_list,
            weights=weights_list,
            k=min(size, len(questions_list))
        )
        
        # Shuffle to randomize order
        random.shuffle(selected)
        
        logger.info(f"Reinforcement phase: Selected {len(selected)} adaptive questions")
        return selected
    
    async def generate_quiz_session(
        self,
        course_id: str,
        lecture_id: str,
        level: int,
        weakness_scores: Dict[str, float],
        attempted_questions: set,
        seen_flashcard_ids: set,
        size: int | None = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a complete adaptive quiz session with coverage-first approach.
        
        This is the main entry point for creating a personalized quiz.
        
        Two-Phase System:
        1. Discovery Phase: If user hasn't seen all concepts, prioritize unseen flashcards
                           sorted by relevance_score
        2. Reinforcement Phase: Once all concepts are covered, focus on weak areas
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            level: Difficulty level (1-4)
            weakness_scores: User's flashcard weakness scores
            attempted_questions: Set of already attempted question hashes
            seen_flashcard_ids: Set of flashcard_ids the user has been tested on
            size: Number of questions in the session
            
        Returns:
            List of selected questions for the quiz session
        """
        # Load flashcards to get relevance scores and total concept count
        flashcard_metadata = await self.load_flashcards(course_id, lecture_id)
        
        # Load all questions for this level
        all_questions = await self.load_quiz_questions(course_id, lecture_id, level)
        
        if not all_questions:
            logger.warning(f"No questions found for {course_id}/{lecture_id}/level_{level}")
            return []
        
        # Determine adaptive session size based on level
        # Level-based allocation: Level 1=5, Level 2=10, Level 3=15, Level 4=15
        level_based_sizes = {
            1: 5,
            2: 10,
            3: 15,
            4: 15
        }
        default_size = level_based_sizes.get(level, 10)  # Default to 10 if level not found
        
        # Cap at 15 questions maximum for any level
        total_available = len(all_questions)
        session_size = min(15, default_size, total_available) if size is None else min(15, size, total_available)
        
        # Get all available flashcard IDs from the flashcard deck
        all_flashcard_ids = set(flashcard_metadata.keys())
        
        # Calculate how many concepts have been covered
        unseen_count = len(all_flashcard_ids - seen_flashcard_ids)
        coverage_percentage = (len(seen_flashcard_ids) / len(all_flashcard_ids) * 100) if all_flashcard_ids else 0
        
        logger.info(f"Quiz session for {lecture_id}: {len(all_flashcard_ids)} total concepts, "
                   f"{len(seen_flashcard_ids)} seen ({coverage_percentage:.1f}% coverage), "
                   f"{unseen_count} unseen")
        
        # Decide which selection strategy to use
        if unseen_count > 0:
            # DISCOVERY PHASE: User hasn't seen all concepts yet
            logger.info(f"🔍 DISCOVERY PHASE: Prioritizing {unseen_count} unseen concepts by relevance")
            selected_questions = await self.select_coverage_first_questions(
                all_questions,
                flashcard_metadata,
                seen_flashcard_ids,
                min(session_size, total_available)
            )
        else:
            # REINFORCEMENT PHASE: All concepts covered, focus on weak areas
            logger.info(f"💪 REINFORCEMENT PHASE: All concepts covered, focusing on weaknesses")
            selected_questions = await self.select_adaptive_questions(
                all_questions,
                weakness_scores,
                attempted_questions,
                min(session_size, total_available)
            )
        
        return selected_questions

