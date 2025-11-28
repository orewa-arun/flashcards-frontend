"""
Multi-level quiz generation module with batching and parallel execution.

This module generates quiz questions at 4 difficulty levels:
- Level 1 (Easy): Foundation questions, single concept, direct application
- Level 2 (Medium): Application questions, 2-3 concepts, moderate complexity
- Level 3 (Hard): Analysis questions, multi-concept integration
- Level 4 (Boss): Synthesis questions, expert-level complexity

Key features:
- Smart chunking: Dynamically adjusts chunk size based on questions per level
- Parallel execution: Generates all 4 levels concurrently using asyncio
- Robust error handling: Retry logic with progressive chunk reduction
- Configurable: Uses settings for questions per flashcard per level
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.content_generation.llm.client import LLMClient
from app.content_generation.prompts import get_quiz_prompt

logger = logging.getLogger(__name__)

# Level name mapping for config
LEVEL_NAMES = {1: "easy", 2: "medium", 3: "hard", 4: "boss"}


class QuizGenerator:
    """
    Generate quiz questions at multiple difficulty levels with batching and parallel execution.
    
    This generator:
    1. Chunks flashcards into optimal batches for API calls
    2. Generates questions for all 4 levels in parallel
    3. Uses retry logic with chunk reduction on failures
    4. Validates and normalizes all generated questions
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        course_name: str,
        reference_textbooks: List[str],
        questions_per_flashcard: Optional[Dict[str, int]] = None,
        base_chunk_size: int = 4,
        chunk_size_by_level: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize quiz generator.
        
        Args:
            llm_client: LLM client for generation
            course_name: Name of the course
            reference_textbooks: List of reference textbooks
            questions_per_flashcard: Dict mapping level names to question counts
                                     e.g., {"easy": 2, "medium": 2, "hard": 2, "boss": 2}
            base_chunk_size: Fallback base number of flashcards per API call
                             (adjusted per level and per questions_per_flashcard)
            chunk_size_by_level: Optional dict mapping level names to starting
                                 chunk sizes, e.g.,
                                 {"easy": 6, "medium": 4, "hard": 3, "boss": 2}
        """
        self.llm_client = llm_client
        self.course_name = course_name
        self.textbook_reference = ", ".join(reference_textbooks) if reference_textbooks else "Course Materials"
        
        # Default questions per flashcard if not provided
        self.questions_per_flashcard = questions_per_flashcard or {
            "easy": 2, "medium": 2, "hard": 2, "boss": 2
        }
        self.base_chunk_size = base_chunk_size
        # Optional: explicit per-level starting chunk sizes
        # Keys are level names ("easy", "medium", "hard", "boss")
        self.chunk_size_by_level: Dict[str, int] = chunk_size_by_level or {}
        
        # Cache for prompt templates
        self._prompt_cache: Dict[int, str] = {}
    
    def _get_chunk_size_for_level(self, level: int) -> int:
        """
        Calculate optimal chunk size for a given level.
        
        More questions per flashcard = smaller chunks to stay within token limits.
        
        Args:
            level: Difficulty level (1-4)
            
        Returns:
            Optimal chunk size for this level
        """
        level_name = LEVEL_NAMES.get(level, "easy")
        questions_count = self.questions_per_flashcard.get(level_name, 2)
        
        # Start from an explicit per-level size if provided, otherwise fall back
        # to the global base_chunk_size.
        base_for_level = self.chunk_size_by_level.get(level_name, self.base_chunk_size)
        
        # Dynamic chunk sizing:
        # - If generating many questions (e.g., 5 per flashcard), use smaller chunks
        # - If generating few questions (e.g., 1 per flashcard), use larger chunks
        # Base formula: chunk_size = base_for_level * (2 / questions_count)
        adjusted_size = int(base_for_level * (2 / max(questions_count, 1)))
        
        # Allow going down to 1 flashcard per chunk (we also have split-retry)
        # and cap upper bound to avoid oversized requests.
        return max(1, min(8, adjusted_size))
    
    def _chunk_flashcards(self, flashcards: List[Dict[str, Any]], chunk_size: int) -> List[List[Dict[str, Any]]]:
        """Split flashcards into chunks of specified size."""
        return [flashcards[i:i + chunk_size] for i in range(0, len(flashcards), chunk_size)]
    
    def _get_prompt_template(self, level: int) -> str:
        """Get cached prompt template for a level."""
        if level not in self._prompt_cache:
            self._prompt_cache[level] = get_quiz_prompt(level)
        return self._prompt_cache[level]
    
    def _build_prompt(
        self,
        flashcards: List[Dict[str, Any]],
        level: int
    ) -> str:
        """Build quiz generation prompt for a chunk of flashcards."""
        template = self._get_prompt_template(level)
        
        level_name = LEVEL_NAMES.get(level, "easy")
        questions_count = self.questions_per_flashcard.get(level_name, 2)
        
        # Replace placeholders
        prompt = template.replace("{{COURSE_NAME}}", self.course_name)
        prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
        prompt = prompt.replace("{{QUESTIONS_PER_FLASHCARD}}", str(questions_count))
        
        # Add flashcards as JSON
        flashcards_json = json.dumps(flashcards, indent=2, ensure_ascii=False)
        
        prompt += f"""

## Input Flashcards:

```json
{flashcards_json}
```

**CRITICAL REMINDER:** Generate EXACTLY {questions_count} Level {level} questions for EACH flashcard.
Total expected questions: {len(flashcards) * questions_count}

Generate the quiz questions now.
"""
        return prompt
    
    async def generate_for_chunk_async(
        self,
        flashcards_chunk: List[Dict[str, Any]],
        level: int,
        chunk_idx: int,
        total_chunks: int,
        max_retries: int = 3,
        is_sub_chunk: bool = False
    ) -> Dict[str, Any]:
        """
        Generate quiz questions for a single chunk asynchronously.
        
        Uses "split and retry" strategy: if a chunk fails, it's split into 
        smaller sub-chunks and all sub-chunks are retried. This ensures NO 
        flashcards are lost even when API calls fail.
        
        Args:
            flashcards_chunk: List of flashcards in this chunk
            level: Difficulty level (1-4)
            chunk_idx: Index of this chunk (for logging)
            total_chunks: Total number of chunks (for logging)
            max_retries: Maximum retry attempts before splitting
            is_sub_chunk: Whether this is a sub-chunk from a split (affects logging)
            
        Returns:
            Dict with task metadata and generated questions
        """
        task_id = f"L{level}_C{chunk_idx + 1}/{total_chunks}"
        if is_sub_chunk:
            task_id = f"L{level}_C{chunk_idx + 1}/{total_chunks}(sub)"
        
        chunk_size = len(flashcards_chunk)
        logger.info(f"[{task_id}] Starting quiz generation for {chunk_size} flashcards")
        
        for attempt in range(max_retries):
            try:
                # Build prompt and generate
                prompt = self._build_prompt(flashcards_chunk, level)
                
                response = await self.llm_client.generate_async(prompt)
                
                # Parse questions
                questions = self._parse_quiz_response(response, level)
                
                if questions:
                    logger.info(f"[{task_id}] Generated {len(questions)} questions")
                    return {
                        "task_id": task_id,
                        "level": level,
                        "chunk_idx": chunk_idx,
                        "questions": questions,
                        "success": True,
                        "error": None,
                        "flashcard_count": chunk_size
                    }
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"[{task_id}] No questions generated, retrying (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(1)
                        continue
                        
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[{task_id}] Error on attempt {attempt + 1}/{max_retries}: {error_msg}")
                
                # Check if this is a timeout/deadline error that warrants splitting
                is_timeout_error = any(x in error_msg.lower() for x in ['timeout', 'deadline', '504', '503'])
                
                if is_timeout_error and chunk_size > 1:
                    # Don't retry, proceed to split
                    logger.warning(f"[{task_id}] Timeout error detected, will split chunk")
                    break
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        # ========== SPLIT AND RETRY LOGIC ==========
        # If we reach here, all retries failed. Split the chunk and retry sub-chunks.
        
        if chunk_size <= 1:
            # Can't split further - this single flashcard failed
            logger.error(f"[{task_id}] Cannot split further, single flashcard failed")
            return {
                "task_id": task_id,
                "level": level,
                "chunk_idx": chunk_idx,
                "questions": [],
                "success": False,
                "error": f"Failed after {max_retries} retries (chunk size=1)",
                "flashcard_count": chunk_size
            }
        
        # Split chunk into 2 halves
        mid = chunk_size // 2
        first_half = flashcards_chunk[:mid]
        second_half = flashcards_chunk[mid:]
        
        logger.info(f"[{task_id}] Recovering by splitting chunk ({chunk_size} flashcards) into 2 sub-chunks: {len(first_half)} + {len(second_half)}")
        
        # Process both sub-chunks in parallel
        sub_tasks = [
            self.generate_for_chunk_async(
                first_half, level, chunk_idx, total_chunks, 
                max_retries=2, is_sub_chunk=True
            ),
            self.generate_for_chunk_async(
                second_half, level, chunk_idx, total_chunks, 
                max_retries=2, is_sub_chunk=True
            )
        ]
        
        sub_results = await asyncio.gather(*sub_tasks, return_exceptions=True)
        
        # Aggregate results from sub-chunks
        all_questions = []
        sub_errors = []
        total_flashcards_processed = 0
        
        for sub_result in sub_results:
            if isinstance(sub_result, Exception):
                sub_errors.append(str(sub_result))
            elif sub_result.get("success"):
                all_questions.extend(sub_result.get("questions", []))
                total_flashcards_processed += sub_result.get("flashcard_count", 0)
            else:
                if sub_result.get("error"):
                    sub_errors.append(sub_result.get("error"))
                # Still count the flashcards even if failed
                total_flashcards_processed += sub_result.get("flashcard_count", 0)
        
        # Determine overall success
        success = len(all_questions) > 0
        
        if success:
            logger.info(f"[{task_id}] Split recovery successful: {len(all_questions)} questions from sub-chunks")
        else:
            logger.error(f"[{task_id}] Split recovery failed: {sub_errors}")
        
        return {
            "task_id": task_id,
            "level": level,
            "chunk_idx": chunk_idx,
            "questions": all_questions,
            "success": success,
            "error": "; ".join(sub_errors) if sub_errors else None,
            "flashcard_count": total_flashcards_processed,
            "was_split": True
        }
    
    async def generate_for_level_async(
        self,
        flashcards: List[Dict[str, Any]],
        level: int
    ) -> Dict[str, Any]:
        """
        Generate all quiz questions for a single level asynchronously.
        
        Chunks flashcards and processes each chunk, then aggregates results.
        
        Args:
            flashcards: All flashcards for the lecture
            level: Difficulty level (1-4)
            
        Returns:
            Dict with level metadata and all questions
        """
        level_name = LEVEL_NAMES.get(level, f"level_{level}")
        chunk_size = self._get_chunk_size_for_level(level)
        chunks = self._chunk_flashcards(flashcards, chunk_size)
        
        logger.info(f"Level {level} ({level_name}): Processing {len(flashcards)} flashcards in {len(chunks)} chunks (size={chunk_size})")
        
        # Process all chunks for this level
        tasks = [
            self.generate_for_chunk_async(chunk, level, idx, len(chunks))
            for idx, chunk in enumerate(chunks)
        ]
        
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate questions from all chunks
        all_questions = []
        errors = []
        
        for result in chunk_results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result.get("success"):
                all_questions.extend(result.get("questions", []))
            elif result.get("error"):
                errors.append(result.get("error"))
        
        return {
            "level": level,
            "level_name": level_name,
            "total_questions": len(all_questions),
            "questions": all_questions,
            "chunks_processed": len(chunks),
            "errors": errors if errors else None
        }
    
    async def generate_all_levels_async(
        self,
        flashcards: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate quizzes for all 4 difficulty levels in parallel.
        
        This is the main entry point for efficient quiz generation.
        All 4 levels are processed concurrently, significantly reducing total time.
        
        Args:
            flashcards: All flashcards for the lecture
            
        Returns:
            List of level results: [{"level": 1, "questions": [...]}, ...]
        """
        logger.info(f"Starting parallel quiz generation for {len(flashcards)} flashcards across 4 levels")
        start_time = datetime.now()
        
        # Create tasks for all 4 levels
        level_tasks = [
            self.generate_for_level_async(flashcards, level)
            for level in range(1, 5)
        ]
        
        # Execute all levels in parallel
        results = await asyncio.gather(*level_tasks, return_exceptions=True)
        
        # Process results
        all_levels = []
        for idx, result in enumerate(results):
            level = idx + 1
            if isinstance(result, Exception):
                logger.error(f"Level {level} failed with exception: {str(result)}")
                all_levels.append({
                    "level": level,
                    "level_name": LEVEL_NAMES.get(level),
                    "total_questions": 0,
                    "questions": [],
                    "error": str(result)
                })
            else:
                all_levels.append(result)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        total_questions = sum(lvl.get("total_questions", 0) for lvl in all_levels)
        
        logger.info(f"Parallel quiz generation complete: {total_questions} questions in {elapsed:.1f}s")
        
        return all_levels
    
    # ========== Synchronous Methods (Legacy Support) ==========
    
    def generate(
        self,
        flashcards: List[Dict[str, Any]],
        level: int,
        questions_per_flashcard: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions for a specific difficulty level (synchronous).
        
        Note: Prefer generate_all_levels_async for better performance.
        
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
        
        prompt = self._build_prompt(flashcards, level)
        
        try:
            response = self.llm_client.generate(prompt)
            questions = self._parse_quiz_response(response, level)
            
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
        Generate quizzes for all 4 difficulty levels (synchronous).
        
        Note: Prefer generate_all_levels_async for better performance.
        """
        return asyncio.run(self.generate_all_levels_async(flashcards))
    
    # ========== Response Parsing & Validation ==========
    
    def _parse_quiz_response(self, response_text: str, level: int) -> List[Dict[str, Any]]:
        """Parse LLM response into validated quiz questions."""
        # Remove code fences
        if response_text.startswith("```"):
            parts = response_text.split("```")
            if len(parts) >= 2:
                response_text = parts[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
        
        # Find JSON array
        start_idx = response_text.find("[")
        if start_idx != -1:
            response_text = response_text[start_idx:]
        
        # Try parsing with multiple strategies
        questions = self._try_parse_json_with_fixes(response_text)
        
        if not questions:
            return []
        
        if not isinstance(questions, list):
            logger.warning("Response is not a JSON array")
            return []
        
        # Validate and normalize each question
        valid_questions = []
        for idx, question in enumerate(questions, 1):
            if self._validate_question(question, idx, level):
                # Ensure all required fields with defaults
                question.setdefault("type", "mcq")
                question.setdefault("visual_type", "None")
                question.setdefault("visual_code", "")
                question.setdefault("alt_text", "")
                question.setdefault("tags", [])
                question.setdefault("difficulty_level", level)
                valid_questions.append(question)
        
        return valid_questions
    
    def _try_parse_json_with_fixes(self, json_text: str) -> List[Dict[str, Any]]:
        """Try parsing JSON with multiple fallback strategies."""
        # Strategy 1: Parse as-is
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Fix common issues
        fixed_json = json_text
        
        # Remove trailing commas
        fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
        
        # Fix missing commas between objects
        fixed_json = re.sub(r'}\s*{', '},{', fixed_json)
        
        # Try to close incomplete JSON
        last_bracket = fixed_json.rfind(']')
        if last_bracket == -1:
            brace_count = 0
            last_complete_pos = -1
            for i, char in enumerate(fixed_json):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_complete_pos = i
            
            if last_complete_pos > 0:
                fixed_json = fixed_json[:last_complete_pos + 1] + ']'
        
        # Strategy 3: Parse fixed JSON
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Extract partial valid objects
        objects = []
        brace_count = 0
        start_pos = -1
        
        for i, char in enumerate(fixed_json):
            if char == '{' and brace_count == 0:
                start_pos = i
                brace_count = 1
            elif char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    obj_text = fixed_json[start_pos:i + 1]
                    try:
                        obj = json.loads(obj_text)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start_pos = -1
        
        if objects:
            logger.info(f"Recovered {len(objects)} questions from partial JSON")
            return objects
        
        logger.error("All JSON parsing strategies failed")
        return []
    
    def _validate_question(self, question: Dict[str, Any], question_num: int, level: int) -> bool:
        """Validate a single quiz question has all required fields."""
        required_fields = ['question_text', 'options', 'correct_answer', 'explanation']
        
        # Check required fields
        for field in required_fields:
            if field not in question:
                logger.warning(f"Question {question_num} missing field: {field}")
                return False
        
        # Validate options
        if not isinstance(question['options'], dict):
            logger.warning(f"Question {question_num}: 'options' must be a dict")
            return False
        
        required_options = ['A', 'B', 'C', 'D']
        for opt in required_options:
            if opt not in question['options']:
                logger.warning(f"Question {question_num} missing option: {opt}")
                return False
        
        # Validate and normalize correct_answer
        correct_answer = question.get('correct_answer')
        question_type = question.get('type', 'mcq')
        
        if isinstance(correct_answer, list):
            if len(correct_answer) == 0:
                logger.warning(f"Question {question_num}: empty correct_answer array")
                return False
            
            # Validate MCQ has exactly 1 answer
            if question_type == 'mcq' and len(correct_answer) > 1:
                logger.warning(f"Question {question_num}: MCQ has multiple answers, should be MCA")
                return False
                
        elif isinstance(correct_answer, str):
            # Convert string to array
            if ',' in correct_answer:
                question['correct_answer'] = [ans.strip() for ans in correct_answer.split(',')]
            else:
                question['correct_answer'] = [correct_answer.strip()]
        else:
            logger.warning(f"Question {question_num}: invalid correct_answer type")
            return False
        
        # Validate explanation
        explanation = question['explanation']
        if not explanation:
            logger.warning(f"Question {question_num}: empty explanation")
            return False
        
        if isinstance(explanation, dict) and 'text' not in explanation:
            logger.warning(f"Question {question_num}: enhanced explanation missing 'text'")
            return False
        
        return True
