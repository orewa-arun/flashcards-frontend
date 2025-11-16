"""
Quiz Generator - Generates multi-level quiz questions from cognitive flashcards.
Enhanced with diagram generation for world-class explanations.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import google.generativeai as genai
import time
import threading

from config import Config
from cognitive_flashcard_generator.diagram_generator import DiagramGenerator


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
        self._progress_active = False
        self._progress_thread = None
        self.diagram_generator = DiagramGenerator()  # Initialize diagram generator
    
    def _show_progress(self, interval: int = 15):
        """Show periodic progress messages while waiting for API response."""
        elapsed = 0
        while self._progress_active:
            time.sleep(interval)
            elapsed += interval
            if self._progress_active:
                print(f"   ⏳ Still waiting... ({elapsed} seconds elapsed)")
    
    def _start_progress_indicator(self):
        """Start background thread to show progress."""
        self._progress_active = True
        self._progress_thread = threading.Thread(target=self._show_progress, daemon=True)
        self._progress_thread.start()
    
    def _stop_progress_indicator(self):
        """Stop background progress indicator."""
        self._progress_active = False
        if self._progress_thread:
            self._progress_thread.join(timeout=1)
    
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
        
        # Create logs directory for raw responses
        logs_dir = Path("logs") / "gemini_raw" / "quizzes"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
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
                base_tokens = 50000
                max_tokens = max(4096, int(base_tokens * (0.8 ** attempt)))  # Reduce tokens on retry
                
                generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": 0.8,  # Slightly higher for creative question generation
                }
                
                print(f"   📊 Flashcards: {len(flashcards_chunk)}")
                print(f"   📊 Max output tokens: {max_tokens:,}")
                print(f"   ⏳ Waiting for API response... (this may take 30-90 seconds)")
                
                start_time = time.time()
                self._start_progress_indicator()
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )
                    self._stop_progress_indicator()
                    elapsed_time = time.time() - start_time
                    print(f"   ⏱️  API response received in {elapsed_time:.1f} seconds")
                    result_text = response.text.strip()
                except Exception as api_error:
                    self._stop_progress_indicator()
                    elapsed_time = time.time() - start_time
                    print(f"   ❌ API call failed after {elapsed_time:.1f} seconds: {api_error}")
                    raise
                
                # Parse JSON response
                questions = self._parse_quiz_response(result_text, level)
                
                if questions:
                    print(f"✅ Generated {len(questions)} Level {level} questions")
                    
                    # Process enhanced explanations and generate diagrams
                    questions = self._process_enhanced_explanations(questions)
                    
                    # Display statistics
                    with_visuals = sum(1 for q in questions if q.get('visual_type', 'None') != 'None')
                    enhanced_explanations = sum(1 for q in questions if isinstance(q.get('explanation'), dict))
                    print(f"   📊 Questions with visuals: {with_visuals}")
                    print(f"   📊 Questions with enhanced explanations: {enhanced_explanations}")
                    print(f"   📊 Expected: {len(flashcards_chunk) * 5} questions (5 per flashcard)")
                    
                    return questions
                else:
                    # Log raw response when no questions generated
                    chunk_safe = chunk_info.replace('/', '_').replace(' ', '_') if chunk_info else f"attempt_{attempt + 1}"
                    log_file = logs_dir / f"level_{level}_{chunk_safe}_attempt_{attempt + 1}.txt"
                    
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write(f"=== RAW LLM RESPONSE ===\n")
                        f.write(f"Level: {level}\n")
                        f.write(f"Chunk: {chunk_info}\n")
                        f.write(f"Attempt: {attempt + 1}/{max_retries}\n")
                        f.write(f"Flashcards: {len(flashcards_chunk)}\n")
                        f.write(f"Max tokens: {max_tokens}\n")
                        f.write(f"\n=== RESPONSE TEXT ===\n")
                        f.write(result_text)
                    
                    print(f"⚠️  No questions generated on attempt {attempt + 1}")
                    print(f"   📝 Raw response saved to: {log_file}")
                    if attempt < max_retries - 1:
                        print(f"   🔄 Will retry with smaller chunk...")
                        continue
                    
            except Exception as e:
                # Log exception details
                chunk_safe = chunk_info.replace('/', '_').replace(' ', '_') if chunk_info else f"attempt_{attempt + 1}"
                log_file = logs_dir / f"level_{level}_{chunk_safe}_attempt_{attempt + 1}_ERROR.txt"
                
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== EXCEPTION DURING GENERATION ===\n")
                    f.write(f"Level: {level}\n")
                    f.write(f"Chunk: {chunk_info}\n")
                    f.write(f"Attempt: {attempt + 1}/{max_retries}\n")
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"\n=== TRACEBACK ===\n")
                    import traceback
                    f.write(traceback.format_exc())
                
                print(f"❌ Error on attempt {attempt + 1}: {e}")
                print(f"   📝 Error details saved to: {log_file}")
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
    
    def _process_enhanced_explanations(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process enhanced explanations and question visuals, generating diagrams for quiz questions.
        
        This method:
        1. Processes question_visual fields (matplotlib/plotly plots in questions)
        2. Detects if explanation is a dict (enhanced) or string (simple)
        3. For enhanced explanations, processes step-by-step diagrams
        4. Generates matplotlib/plotly diagrams from specs
        5. Keeps mermaid/graphviz as code for client-side rendering
        """
        if not questions:
            return questions
        
        print(f"\n🎨 Processing question visuals and enhanced explanations...")
        
        for idx, question in enumerate(questions, 1):
            # Process question_visual first
            question_visual = question.get('question_visual')
            question_visual_type = question.get('question_visual_type')
            
            if question_visual and question_visual_type and question_visual_type != 'None':
                if question_visual_type == 'matplotlib' and isinstance(question_visual, dict):
                    try:
                        print(f"   Question {idx}: Generating question matplotlib plot...")
                        diagram_image = self.diagram_generator.generate_matplotlib_plot(question_visual)
                        if diagram_image:
                            # Replace the plot spec with the base64 image
                            question['question_visual'] = diagram_image
                            print(f"   ✓ Question matplotlib plot generated")
                    except Exception as e:
                        print(f"   ⚠️  Failed to generate question matplotlib plot: {e}")
                
                elif question_visual_type == 'plotly' and isinstance(question_visual, dict):
                    try:
                        print(f"   Question {idx}: Generating question plotly plot...")
                        plotly_spec = self.diagram_generator.generate_plotly_plot(question_visual)
                        if plotly_spec:
                            question['question_visual'] = plotly_spec
                            print(f"   ✓ Question plotly plot generated")
                    except Exception as e:
                        print(f"   ⚠️  Failed to generate question plotly plot: {e}")
            
            # Process explanation
            explanation = question.get('explanation')
            
            if not explanation:
                continue
            
            # Skip if explanation is just a string (simple explanation)
            if isinstance(explanation, str):
                continue
            
            # Process enhanced explanation (dict)
            if isinstance(explanation, dict):
                steps = explanation.get('step_by_step', [])
                
                if steps:
                    print(f"   Question {idx}: Processing {len(steps)} explanation step(s)...")
                    
                    for step_idx, step in enumerate(steps, 1):
                        diagram = step.get('diagram')
                        diagram_type = step.get('diagram_type')
                        
                        if diagram and diagram_type:
                            # Generate matplotlib plots
                            if diagram_type == 'matplotlib' and isinstance(diagram, dict):
                                try:
                                    print(f"      Step {step_idx}: Generating matplotlib plot...")
                                    diagram_image = self.diagram_generator.generate_matplotlib_plot(diagram)
                                    if diagram_image:
                                        step['diagram_image'] = diagram_image
                                        print(f"      ✓ Matplotlib plot generated")
                                except Exception as e:
                                    print(f"      ⚠️  Failed to generate matplotlib plot: {e}")
                            
                            # Generate plotly plots
                            elif diagram_type == 'plotly' and isinstance(diagram, dict):
                                try:
                                    print(f"      Step {step_idx}: Generating plotly plot...")
                                    plotly_spec = self.diagram_generator.generate_plotly_plot(diagram)
                                    if plotly_spec:
                                        step['diagram'] = plotly_spec
                                        print(f"      ✓ Plotly plot generated")
                                except Exception as e:
                                    print(f"      ⚠️  Failed to generate plotly plot: {e}")
                            
                            # Validate mermaid diagrams
                            elif diagram_type == 'mermaid' and isinstance(diagram, str):
                                try:
                                    validated = self.diagram_generator.render_mermaid(diagram)
                                    if validated:
                                        step['diagram'] = validated
                                        print(f"      ✓ Mermaid diagram validated")
                                except Exception as e:
                                    print(f"      ⚠️  Mermaid validation warning: {e}")
                            
                            # Render graphviz to SVG
                            elif diagram_type == 'graphviz' and isinstance(diagram, str):
                                try:
                                    svg = self.diagram_generator.render_graphviz(diagram)
                                    if svg:
                                        step['diagram'] = svg
                                        step['diagram_type'] = 'svg'
                                        print(f"      ✓ Graphviz rendered to SVG")
                                except Exception as e:
                                    print(f"      ⚠️  Failed to render graphviz: {e}")
        
        print(f"✓ Question visual and explanation processing complete\n")
        return questions
    
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
        
        # Validate and normalize correct_answer
        # The prompt generates it as an array like ["A"] or ["A", "B", "C"]
        # BOTH MCQ and MCA questions should use arrays for consistency
        correct_answer = question.get('correct_answer')
        question_type = question.get('type', 'mcq')
        
        if isinstance(correct_answer, list):
            if len(correct_answer) == 0:
                print(f"   ⚠️  Question {question_num}: 'correct_answer' array is empty")
                return False
            
            # Keep arrays for both MCQ and MCA (consistent format)
            question['correct_answer'] = correct_answer
            
            # Validate MCQ has exactly 1 answer, MCA has 2+ answers
            if question_type == 'mcq' and len(correct_answer) > 1:
                print(f"   ⚠️  Question {question_num}: MCQ question has multiple correct answers ({len(correct_answer)}), should be type 'mca'")
                return False
            elif question_type == 'mca' and len(correct_answer) < 2:
                print(f"   ⚠️  Question {question_num}: MCA question has only {len(correct_answer)} answer(s), should have 2+")
                return False
                
        elif isinstance(correct_answer, str):
            # Legacy format: convert string to array
            if ',' in correct_answer:
                # Comma-separated string -> array
                answer_array = [ans.strip() for ans in correct_answer.split(',')]
                question['correct_answer'] = answer_array
            else:
                # Single string -> single-element array
                question['correct_answer'] = [correct_answer.strip()]
        elif not correct_answer:
            print(f"   ⚠️  Question {question_num}: 'correct_answer' must not be empty")
            return False
        else:
            print(f"   ⚠️  Question {question_num}: 'correct_answer' must be an array or string, got {type(correct_answer).__name__}")
            return False
        
        # Validate explanation (can be string or enhanced dict)
        if not question['explanation']:
            print(f"   ⚠️  Question {question_num}: 'explanation' must not be empty")
            return False
        
        # If it's a dict (enhanced explanation), validate structure
        if isinstance(question['explanation'], dict):
            if 'text' not in question['explanation']:
                print(f"   ⚠️  Question {question_num}: Enhanced explanation missing 'text' field")
                return False
        # If it's a string, just check it's not empty
        elif not isinstance(question['explanation'], str):
            print(f"   ⚠️  Question {question_num}: 'explanation' must be a string or dict")
            return False
        
        return True

