"""
Async Quiz Generator - Generates multi-level quiz questions with batching support.
"""

import os
import json
import asyncio
from typing import Dict, List, Any
import google.generativeai as genai

from config import Config


class AsyncQuizGenerator:
    """Async quiz generator with batching support."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 course_name: str = "", textbook_reference: str = ""):
        """
        Initialize the async quiz generator.
        
        Args:
            api_key: Gemini API key
            model: Gemini model to use
            course_name: Name of the course
            textbook_reference: Full textbook citation
        """
        self.genai = genai
        self.genai.configure(api_key=api_key)
        self.model = self.genai.GenerativeModel(model)
        self.course_name = course_name
        self.textbook_reference = textbook_reference
        self._prompt_templates = {}  # Cache for prompt templates
    
    def _load_quiz_prompt_template(self, level: int) -> str:
        """Load the quiz prompt template for a specific difficulty level (cached)."""
        if level not in self._prompt_templates:
            prompt_path = os.path.join(Config.PROMPTS_DIR, f"level_{level}_quiz_prompt.txt")
            
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._prompt_templates[level] = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Quiz prompt file not found: {prompt_path}\n"
                    f"Please ensure level_{level}_quiz_prompt.txt exists in the prompts/ directory."
                )
        
        return self._prompt_templates[level]
    
    async def generate_quiz_questions_async(self, flashcards_chunk: List[Dict[str, Any]], 
                                           level: int, chunk_info: str = "", 
                                           task_id: str = "") -> Dict[str, Any]:
        """
        Generate quiz questions asynchronously.
        
        Args:
            flashcards_chunk: List of flashcard dictionaries
            level: Difficulty level (1-4)
            chunk_info: Optional info about which chunk this is
            task_id: Unique identifier for this task
            
        Returns:
            Dictionary with task_id, questions, and metadata
        """
        print(f"🚀 [Task {task_id}] Starting async quiz generation Level {level} {chunk_info}")
        
        try:
            questions = await self._generate_with_retry_async(
                flashcards_chunk, level, chunk_info, task_id
            )
            
            return {
                'task_id': task_id,
                'level': level,
                'chunk_info': chunk_info,
                'questions': questions,
                'success': len(questions) > 0,
                'error': None
            }
        except Exception as e:
            print(f"❌ [Task {task_id}] Error: {e}")
            return {
                'task_id': task_id,
                'level': level,
                'chunk_info': chunk_info,
                'questions': [],
                'success': False,
                'error': str(e)
            }
    
    async def _generate_with_retry_async(self, flashcards_chunk: List[Dict[str, Any]], 
                                        level: int, chunk_info: str = "", 
                                        task_id: str = "", max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Generate quiz questions with retry logic asynchronously.
        """
        original_chunk = flashcards_chunk
        
        for attempt in range(max_retries):
            try:
                # Reduce chunk size on each retry
                if attempt > 0:
                    reduction_factor = 0.7 ** attempt
                    max_cards = max(1, int(len(original_chunk) * reduction_factor))
                    flashcards_chunk = original_chunk[:max_cards]
                    print(f"🔄 [Task {task_id}] Retry {attempt + 1}/{max_retries}: Reduced to {len(flashcards_chunk)} flashcards")
                
                # Convert flashcards to JSON string
                flashcards_json = json.dumps(flashcards_chunk, indent=2, ensure_ascii=False)
                
                # Load and populate template
                prompt_template = self._load_quiz_prompt_template(level)
                prompt = prompt_template.replace("{{COURSE_NAME}}", self.course_name)
                prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
                prompt = prompt + f"\n\n## Input Flashcards:\n\n```json\n{flashcards_json}\n```\n\nGenerate the quiz questions now."
                
                # Configure generation
                base_tokens = 50000
                max_tokens = max(4096, int(base_tokens * (0.8 ** attempt)))
                
                generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                }
                
                # Run the blocking API call in a thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt, generation_config=generation_config)
                )
                
                result_text = response.text.strip()
                
                # Parse JSON response
                questions = self._parse_quiz_response(result_text)
                
                if questions:
                    print(f"✅ [Task {task_id}] Generated {len(questions)} questions")
                    return questions
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️  [Task {task_id}] No questions on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(1)
                        continue
                    
            except Exception as e:
                # Log the full error to see the root cause
                print(f"❌ [Task {task_id}] API Error on attempt {attempt + 1}: {type(e).__name__} - {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    raise
        
        return []
    
    def _parse_quiz_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the AI response into structured quiz questions."""
        # Remove code fences if present
        if response_text.startswith('```'):
            parts = response_text.split('```')
            if len(parts) >= 2:
                response_text = parts[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
        
        # Find the JSON array
        start_idx = response_text.find('[')
        if start_idx != -1:
            response_text = response_text[start_idx:]
        
        # Try to parse JSON
        try:
            questions = json.loads(response_text)
            
            if not isinstance(questions, list):
                return []
            
            # Validate each question
            valid_questions = []
            for q in questions:
                if self._validate_question(q):
                    valid_questions.append(q)
            
            return valid_questions
            
        except json.JSONDecodeError:
            # Try to extract partial valid JSON objects
            import re
            objects = []
            brace_count = 0
            start_pos = -1
            
            for i, char in enumerate(response_text):
                if char == '{' and brace_count == 0:
                    start_pos = i
                    brace_count = 1
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_pos != -1:
                        obj_text = response_text[start_pos:i+1]
                        try:
                            obj = json.loads(obj_text)
                            if self._validate_question(obj):
                                objects.append(obj)
                        except json.JSONDecodeError:
                            pass
                        start_pos = -1
            
            return objects
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate a single quiz question has all required fields."""
        required_fields = ['type', 'question_text', 'options', 'correct_answer', 
                          'explanation', 'difficulty_level', 'source_flashcard_id']
        
        # Check all required fields exist
        for field in required_fields:
            if field not in question:
                return False
        
        # Validate options is a dictionary with at least 2 items
        if not isinstance(question['options'], dict) or len(question['options']) < 2:
            return False
        
        # Validate correct_answer is a non-empty list
        if not isinstance(question['correct_answer'], list) or len(question['correct_answer']) < 1:
            return False
        
        # Validate explanation (can be string or enhanced dict)
        if not question['explanation']:
            return False
        
        # If it's a dict (enhanced explanation), validate structure
        if isinstance(question['explanation'], dict):
            if 'text' not in question['explanation']:
                return False
        # If it's a string, just check it's not empty
        elif not isinstance(question['explanation'], str):
            return False
        
        # Type-specific validation
        question_type = question.get('type')
        if question_type == 'mcq':
            # MCQ must have exactly 1 correct answer
            if len(question['correct_answer']) != 1:
                return False
        elif question_type == 'mca':
            # MCA must have at least 1 correct answer (typically 2-3)
            if len(question['correct_answer']) < 1:
                return False
        
        return True

