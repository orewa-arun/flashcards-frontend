"""Adaptive quiz engine service for personalized question selection."""

import json
import hashlib
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AdaptiveQuizService:
    """Service for adaptive quiz question selection based on user performance."""
    
    def __init__(self, courses_dir: Optional[str] = None):
        if courses_dir is None:
            # Get the backend directory (parent of app directory)
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
    
    async def load_flashcards(
        self,
        course_id: str,
        lecture_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load all flashcards for a lecture and extract their relevance scores.
        
        Args:
            course_id: Course identifier (e.g., "MS5150")
            lecture_id: Lecture identifier (e.g., "SI_PLC")
            
        Returns:
            Dict mapping flashcard_id to flashcard metadata (relevance_score, etc.)
        """
        flashcard_file = (
            self.courses_dir / course_id / "cognitive_flashcards" / 
            lecture_id / f"{lecture_id}_cognitive_flashcards_only.json"
        )
        
        if not flashcard_file.exists():
            logger.error(f"Flashcard file not found: {flashcard_file}")
            return {}
        
        try:
            with open(flashcard_file, 'r', encoding='utf-8') as f:
                flashcard_data = json.load(f)
            
            flashcards = flashcard_data.get('flashcards', [])
            
            # Create a mapping of flashcard_id -> metadata
            flashcard_map = {}
            for card in flashcards:
                flashcard_id = card.get('flashcard_id')
                if flashcard_id:
                    flashcard_map[flashcard_id] = {
                        'relevance_score': card.get('relevance_score', 0),
                        'question': card.get('question', ''),
                        'tags': card.get('tags', [])
                    }
            
            logger.info(f"Loaded {len(flashcard_map)} flashcards from {flashcard_file.name}")
            return flashcard_map
        
        except Exception as e:
            logger.error(f"Error loading flashcard file {flashcard_file}: {e}")
            return {}
    
    async def load_quiz_questions(
        self,
        course_id: str,
        lecture_id: str,
        level: int
    ) -> List[Dict[str, Any]]:
        """
        Load all questions for a specific quiz level.
        
        Args:
            course_id: Course identifier (e.g., "MS5150")
            lecture_id: Lecture identifier (e.g., "SI_PLC")
            level: Difficulty level (1-4)
            
        Returns:
            List of question objects with added question_hash field
        """
        quiz_file = self.courses_dir / course_id / "quiz" / f"{lecture_id}_level_{level}_quiz.json"
        
        if not quiz_file.exists():
            logger.error(f"Quiz file not found: {quiz_file}")
            return []
        
        try:
            with open(quiz_file, 'r', encoding='utf-8') as f:
                quiz_data = json.load(f)
            
            questions = quiz_data.get('questions', [])
            
            # Add question_hash to each question
            for question in questions:
                question['question_hash'] = self.hash_question(question['question_text'])
            
            logger.info(f"Loaded {len(questions)} questions from {quiz_file.name}")
            return questions
        
        except Exception as e:
            logger.error(f"Error loading quiz file {quiz_file}: {e}")
            return []
    
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
        
        # Determine adaptive session size based on total available questions
        # Rule of thumb: ~33% of available, bounded within [5, 20]
        total_available = len(all_questions)
        dynamic_size = max(5, min(20, int(round(total_available * 0.33))))
        session_size = dynamic_size if size is None else max(5, min(20, size))
        
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

