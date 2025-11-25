"""Multi-level quiz generation module."""

import logging
import json
from typing import Dict, Any, List

from app.content_generation.llm.client import LLMClient
from app.content_generation.prompts import get_quiz_prompt

logger = logging.getLogger(__name__)


class QuizGenerator:
    """Generate quiz questions at multiple difficulty levels."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        course_name: str,
        reference_textbooks: List[str]
    ):
        """
        Initialize quiz generator.
        
        Args:
            llm_client: LLM client for generation
            course_name: Name of the course
            reference_textbooks: List of reference textbooks
        """
        self.llm_client = llm_client
        self.course_name = course_name
        self.textbook_reference = ", ".join(reference_textbooks) if reference_textbooks else "Course Materials"
    
    def generate(
        self,
        flashcards: List[Dict[str, Any]],
        level: int,
        questions_per_flashcard: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions for a specific difficulty level.
        
        Args:
            flashcards: List of flashcard dicts
            level: Difficulty level (1-4)
            questions_per_flashcard: Number of questions per flashcard
            
        Returns:
            List of question dicts
        """
        if not 1 <= level <= 4:
            raise ValueError(f"Invalid level: {level}. Must be 1-4.")
        
        logger.info(f"Generating Level {level} quiz from {len(flashcards)} flashcards")
        
        # Build prompt
        prompt = self._build_prompt(flashcards, level, questions_per_flashcard)
        
        # Generate questions
        try:
            response = self.llm_client.generate(prompt)
            questions = self._parse_questions(response)
            
            logger.info(f"Generated {len(questions)} Level {level} questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating Level {level} quiz: {str(e)}")
            raise
    
    def generate_all_levels(
        self,
        flashcards: List[Dict[str, Any]],
        questions_per_flashcard: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate quizzes for all 4 difficulty levels.
        
        Args:
            flashcards: List of flashcard dicts
            questions_per_flashcard: Number of questions per flashcard per level
            
        Returns:
            List of level dicts: [{"level": 1, "questions": [...]}, ...]
        """
        all_quizzes = []
        
        for level in range(1, 5):
            try:
                questions = self.generate(
                    flashcards=flashcards,
                    level=level,
                    questions_per_flashcard=questions_per_flashcard
                )
                
                all_quizzes.append({
                    "level": level,
                    "total_questions": len(questions),
                    "questions": questions
                })
                
            except Exception as e:
                logger.error(f"Failed to generate Level {level}: {str(e)}")
                all_quizzes.append({
                    "level": level,
                    "error": str(e),
                    "questions": []
                })
        
        return all_quizzes
    
    def _build_prompt(
        self,
        flashcards: List[Dict[str, Any]],
        level: int,
        questions_per_flashcard: int
    ) -> str:
        """Build quiz generation prompt."""
        template = get_quiz_prompt(level)
        
        # Replace placeholders
        prompt = template.replace("{{COURSE_NAME}}", self.course_name)
        prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
        
        # Add flashcards as JSON
        flashcards_json = json.dumps(flashcards, indent=2, ensure_ascii=False)
        prompt += f"\n\nFlashcards (JSON):\n{flashcards_json}\n\n"
        
        # Add instructions
        prompt += f"""
Generate {questions_per_flashcard} questions for EACH flashcard.
Total expected questions: {len(flashcards) * questions_per_flashcard}

Return a JSON array of questions. Each question must have:
- id: unique identifier
- question: the question text
- options: array of 4 options (A, B, C, D)
- correct_answer: the correct option letter(s)
- explanation: detailed explanation
- difficulty: {level}
- type: "MCQ" or "MCA"

Return ONLY valid JSON, no additional text.
"""
        
        return prompt
    
    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to question list."""
        try:
            # Remove code fences
            if response.startswith("```"):
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1]
                    if response.startswith("json"):
                        response = response[4:].strip()
            
            # Parse JSON
            questions = json.loads(response)
            
            # Validate it's a list
            if not isinstance(questions, list):
                logger.warning("Response is not a list, wrapping it")
                questions = [questions]
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse questions JSON: {str(e)}")
            logger.debug(f"Response was: {response[:500]}")
            return []

