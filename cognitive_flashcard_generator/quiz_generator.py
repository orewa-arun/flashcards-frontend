"""
Quiz Generator - Generates multi-level quiz questions from cognitive flashcards.
"""

import os
import json
from typing import Dict, List, Any
import google.generativeai as genai

from config import Config


class QuizGenerator:
    """Generates quiz questions at different difficulty levels from flashcard content."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 course_name: str = "", textbook_reference: str = ""):
        """
        Initialize the quiz generator.
        
        Args:
            api_key: Gemini API key
            model: Gemini model to use
            course_name: Name of the course (e.g., "Information Systems")
            textbook_reference: Full textbook citation
        """
        self.genai = genai
        self.genai.configure(api_key=api_key)
        self.model = self.genai.GenerativeModel(model)
        self.course_name = course_name
        self.textbook_reference = textbook_reference
    
    def _load_quiz_prompt_template(self, level: int) -> str:
        """
        Load the quiz prompt template for a specific difficulty level.
        
        Args:
            level: Difficulty level (1-4)
            
        Returns:
            Prompt template as string
        """
        prompt_path = os.path.join(Config.PROMPTS_DIR, f"level_{level}_quiz_prompt.txt")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Quiz prompt file not found: {prompt_path}\n"
                f"Please ensure level_{level}_quiz_prompt.txt exists in the prompts/ directory."
            )
    
    def generate_quiz_questions(self, flashcards_chunk: List[Dict[str, Any]], level: int,
                               chunk_info: str = "") -> List[Dict[str, Any]]:
        """
        Generate quiz questions for a chunk of flashcards at a specific difficulty level.
        
        Args:
            flashcards_chunk: List of flashcard dictionaries (3-5 flashcards)
            level: Difficulty level (1-4)
            chunk_info: Optional info about which chunk this is
            
        Returns:
            List of quiz question dictionaries
        """
        chunk_display = f" ({chunk_info})" if chunk_info else ""
        print(f"\n{'='*70}")
        print(f"🎯 Generating Level {level} Quiz Questions{chunk_display}")
        print(f"📚 Course: {self.course_name}")
        print(f"📖 Reference: {self.textbook_reference}")
        print(f"📊 Flashcards in chunk: {len(flashcards_chunk)}")
        print(f"{'='*70}")
        
        return self._generate_with_retry(flashcards_chunk, level, chunk_info)
    
    def _generate_with_retry(self, flashcards_chunk: List[Dict[str, Any]], level: int,
                            chunk_info: str = "", max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Generate quiz questions with retry logic and progressive chunk size reduction.
        """
        original_chunk = flashcards_chunk
        
        for attempt in range(max_retries):
            try:
                # Reduce chunk size on each retry to avoid token limits
                if attempt > 0:
                    reduction_factor = 0.7 ** attempt  # Reduce by 30% each attempt
                    max_cards = max(1, int(len(original_chunk) * reduction_factor))
                    flashcards_chunk = original_chunk[:max_cards]
                    print(f"🔄 Retry {attempt + 1}/{max_retries}: Reduced to {len(flashcards_chunk)} flashcard(s)")
                
                # Convert flashcards to JSON string for the prompt
                flashcards_json = json.dumps(flashcards_chunk, indent=2, ensure_ascii=False)
                
                # Load and populate template
                prompt_template = self._load_quiz_prompt_template(level)
                prompt = prompt_template.replace("{{COURSE_NAME}}", self.course_name)
                prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
                
                # Replace the content placeholder with the flashcards JSON
                # The prompt expects a JSON array of flashcards
                prompt = prompt + f"\n\n## Input Flashcards:\n\n```json\n{flashcards_json}\n```\n\nGenerate the quiz questions now."
                
                print(f"🤖 Analyzing {len(flashcards_chunk)} flashcard(s) and generating Level {level} questions...")
                
                # Configure generation with progressive token limit reduction
                base_tokens = 16384
                max_tokens = max(4096, int(base_tokens * (0.8 ** attempt)))  # Reduce tokens on retry
                
                generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": 0.8,  # Slightly higher for creative question generation
                }
                
                print(f"   📊 Flashcards: {len(flashcards_chunk)}")
                print(f"   📊 Max output tokens: {max_tokens:,}")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                result_text = response.text.strip()
                
                # Parse JSON response
                questions = self._parse_quiz_response(result_text, level)
                
                if questions:
                    print(f"✅ Generated {len(questions)} Level {level} questions")
                    
                    # Display statistics
                    with_visuals = sum(1 for q in questions if q.get('visual_type', 'None') != 'None')
                    print(f"   📊 Questions with visuals: {with_visuals}")
                    print(f"   📊 Expected: {len(flashcards_chunk) * 5} questions (5 per flashcard)")
                    
                    return questions
                else:
                    print(f"⚠️  No questions generated on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        print(f"   🔄 Will retry with smaller chunk...")
                        continue
                    
            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"   🔄 Retrying with reduced chunk size...")
                    continue
                else:
                    print(f"❌ All retry attempts failed")
                    import traceback
                    traceback.print_exc()
        
        print("⚠️  No questions generated from this chunk after all retries")
        return []
    
    def _parse_quiz_response(self, response_text: str, level: int) -> List[Dict[str, Any]]:
        """Parse the AI response into structured quiz questions with robust error handling."""
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
        
        # Try to parse JSON with multiple fallback strategies
        questions = self._try_parse_json_with_fixes(response_text)
        
        if not questions:
            return []
        
        # Validate structure
        if not isinstance(questions, list):
            print("⚠️  Response is not a JSON array")
            return []
        
        # Validate and normalize each question
        valid_questions = []
        for i, question in enumerate(questions, 1):
            if self._validate_question(question, i, level):
                # Ensure all required fields exist with defaults if missing
                if 'type' not in question:
                    question['type'] = 'mcq'
                if 'visual_type' not in question:
                    question['visual_type'] = 'None'
                if 'visual_code' not in question or question['visual_code'] is None:
                    question['visual_code'] = ""
                if 'alt_text' not in question or question['alt_text'] is None:
                    question['alt_text'] = ""
                if 'tags' not in question:
                    question['tags'] = []
                if 'difficulty_level' not in question:
                    question['difficulty_level'] = level
                valid_questions.append(question)
        
        return valid_questions
    
    def _try_parse_json_with_fixes(self, json_text: str) -> List[Dict[str, Any]]:
        """
        Try to parse JSON with multiple fallback strategies to handle common AI generation errors.
        """
        import re
        
        # Strategy 1: Try parsing as-is
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"🔧 Initial JSON parse failed: {e}")
            print(f"   Attempting to fix common JSON errors...")
        
        # Strategy 2: Fix common JSON issues
        fixed_json = json_text
        
        # Fix 1: Remove trailing commas
        try:
            fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
            print("   🔧 Removed trailing commas")
        except Exception:
            pass
        
        # Fix 2: Handle missing commas between objects
        try:
            fixed_json = re.sub(r'}\s*{', '},{', fixed_json)
            print("   🔧 Fixed missing commas between objects")
        except Exception:
            pass
        
        # Fix 3: Handle incomplete JSON by finding the last complete object
        try:
            last_bracket = fixed_json.rfind(']')
            if last_bracket == -1:
                # No closing bracket found, try to add one
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
                    print("   🔧 Added missing closing bracket")
        except Exception:
            pass
        
        # Strategy 3: Try parsing the fixed JSON
        try:
            result = json.loads(fixed_json)
            print("   ✅ Successfully parsed JSON after fixes")
            return result
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON still invalid after fixes: {e}")
        
        # Strategy 4: Try to extract partial valid JSON objects
        try:
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
                        # Found a complete object
                        obj_text = fixed_json[start_pos:i+1]
                        try:
                            obj = json.loads(obj_text)
                            objects.append(obj)
                        except json.JSONDecodeError:
                            pass  # Skip invalid objects
                        start_pos = -1
            
            if objects:
                print(f"   🔧 Extracted {len(objects)} valid objects from partial JSON")
                return objects
        except Exception:
            pass
        
        print("   ❌ All JSON parsing strategies failed")
        return []
    
    def _validate_question(self, question: Dict[str, Any], question_num: int, level: int) -> bool:
        """Validate a single quiz question has all required fields."""
        required_fields = ['question_text', 'options', 'correct_answer', 'explanation']
        
        # Check basic required fields
        for field in required_fields:
            if field not in question:
                print(f"   ⚠️  Question {question_num} missing required field: {field}")
                return False
        
        # Validate options structure
        if not isinstance(question['options'], dict):
            print(f"   ⚠️  Question {question_num}: 'options' must be an object/dict")
            return False
        
        # Check all 4 options are present (A, B, C, D)
        required_options = ['A', 'B', 'C', 'D']
        for option in required_options:
            if option not in question['options']:
                print(f"   ⚠️  Question {question_num} missing option: {option}")
                return False
        
        # Validate correct_answer is not empty
        if not question['correct_answer'] or not isinstance(question['correct_answer'], str):
            print(f"   ⚠️  Question {question_num}: 'correct_answer' must be a non-empty string")
            return False
        
        # Validate explanation is not empty
        if not question['explanation'] or not isinstance(question['explanation'], str):
            print(f"   ⚠️  Question {question_num}: 'explanation' must be a non-empty string")
            return False
        
        return True

