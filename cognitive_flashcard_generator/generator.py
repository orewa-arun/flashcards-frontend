"""
Cognitive Flashcard Generator - Core AI generation logic.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
import google.generativeai as genai

from config import Config


class CognitiveFlashcardGenerator:
    """Universal flashcard generator with diagram support."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 course_name: str = "", textbook_reference: str = ""):
        """
        Initialize the cognitive flashcard generator.
        
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
    
    def load_prompt_template(self) -> str:
        """Load the generic prompt template."""
        prompt_path = os.path.join(Config.PROMPTS_DIR, "intelligent_flashcard_only_prompt_v2.txt")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                "Please ensure intelligent_flashcard_only_prompt_v2.txt exists in the prompts/ directory."
            )
    
    def generate_flashcards(self, content: str, source_name: str = "", chunk_info: str = "") -> List[Dict[str, Any]]:
        """
        Generate cognitive flashcards with examples and diagrams.
        
        Args:
            content: The content to generate flashcards from
            source_name: Name of the source (e.g., lecture name)
            chunk_info: Optional info about which chunk this is (e.g., "Chunk 1/5")
            
        Returns:
            List of flashcard dictionaries with scores, examples, and mermaid diagrams
        """
        # chunk_info is now passed from main.py, making this print statement useful
        chunk_display = f" ({chunk_info})" if chunk_info else "" 
        print(f"\n{'='*70}")
        print(f"🧠 Generating Cognitive Flashcards{chunk_display}")
        print(f"📚 Course: {self.course_name}")
        print(f"📖 Reference: {self.textbook_reference}")
        print(f"{'='*70}")
        
        return self._generate_with_retry(content, source_name, chunk_info)
    
    def _generate_with_retry(self, content: str, source_name: str = "", chunk_info: str = "", max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Generate flashcards with retry logic and progressive chunk size reduction.
        """
        original_content = content
        
        # Create logs directory for raw responses
        logs_dir = Path("logs") / "gemini_raw" / "flashcards"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(max_retries):
            try:
                # Reduce content size on each retry to avoid token limits
                if attempt > 0:
                    reduction_factor = 0.7 ** attempt  # Reduce by 30% each attempt
                    max_chars = int(len(original_content) * reduction_factor)
                    content = original_content[:max_chars]
                    print(f"🔄 Retry {attempt + 1}/{max_retries}: Reduced content to {len(content):,} characters")
                
                # Load and populate template
                prompt_template = self.load_prompt_template()
                prompt = prompt_template.replace("{{COURSE_NAME}}", self.course_name)
                prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
                prompt = prompt.replace("{{CONTENT_PLACEHOLDER}}", content)
                
                print(f"🤖 Analyzing content and generating flashcards with diagrams...")
                
                # Configure generation with progressive token limit reduction
                base_tokens = 50000
                max_tokens = max(4096, int(base_tokens * (0.8 ** attempt)))  # Reduce tokens on retry
                
                generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                }
                
                print(f"   📊 Content size: {len(content):,} characters")
                print(f"   📊 Max output tokens: {max_tokens:,}")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                result_text = response.text.strip()
                
                # Parse JSON response
                flashcards = self._parse_flashcard_response(result_text)
                
                if flashcards:
                    print(f"✅ Generated {len(flashcards)} flashcards")
                    
                    # Display score distribution
                    self._display_score_distribution(flashcards)
                    
                    # Display stats
                    total_diagrams = 0
                    total_math_viz = 0
                    for card in flashcards:
                        diagrams = card.get('mermaid_diagrams', {})
                        total_diagrams += sum(1 for diagram in diagrams.values() if diagram.strip())
                        math_viz = card.get('math_visualizations', {})
                        total_math_viz += sum(1 for viz in math_viz.values() if viz.strip())
                    
                    examples_count = sum(1 for card in flashcards if card.get('example', '').strip())
                    print(f"   📊 Mermaid Diagrams: {total_diagrams} across all answer types")
                    print(f"   🔢 Math Visualizations: {total_math_viz} Graphviz diagrams")
                    print(f"   📝 With Examples: {examples_count} cards")
                    
                    return flashcards
                else:
                    # Log raw response when no flashcards generated
                    source_safe = source_name.replace('/', '_').replace(' ', '_') if source_name else "unknown"
                    chunk_safe = chunk_info.replace('/', '_').replace(' ', '_') if chunk_info else f"attempt_{attempt + 1}"
                    log_file = logs_dir / f"{source_safe}_{chunk_safe}_attempt_{attempt + 1}.txt"
                    
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write(f"=== RAW LLM RESPONSE ===\n")
                        f.write(f"Source: {source_name}\n")
                        f.write(f"Chunk: {chunk_info}\n")
                        f.write(f"Attempt: {attempt + 1}/{max_retries}\n")
                        f.write(f"Content size: {len(content)} characters\n")
                        f.write(f"Max tokens: {max_tokens}\n")
                        f.write(f"\n=== RESPONSE TEXT ===\n")
                        f.write(result_text)
                    
                    print(f"⚠️  No flashcards generated on attempt {attempt + 1}")
                    print(f"   📝 Raw response saved to: {log_file}")
                    if attempt < max_retries - 1:
                        print(f"   🔄 Will retry with smaller content size...")
                        continue
                    
            except Exception as e:
                # Log exception details
                source_safe = source_name.replace('/', '_').replace(' ', '_') if source_name else "unknown"
                chunk_safe = chunk_info.replace('/', '_').replace(' ', '_') if chunk_info else f"attempt_{attempt + 1}"
                log_file = logs_dir / f"{source_safe}_{chunk_safe}_attempt_{attempt + 1}_ERROR.txt"
                
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"=== EXCEPTION DURING GENERATION ===\n")
                    f.write(f"Source: {source_name}\n")
                    f.write(f"Chunk: {chunk_info}\n")
                    f.write(f"Attempt: {attempt + 1}/{max_retries}\n")
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"\n=== TRACEBACK ===\n")
                    import traceback
                    f.write(traceback.format_exc())
                
                print(f"❌ Error on attempt {attempt + 1}: {e}")
                print(f"   📝 Error details saved to: {log_file}")
                if attempt < max_retries - 1:
                    print(f"   🔄 Retrying with reduced content size...")
                    continue
                else:
                    print(f"❌ All retry attempts failed")
                    import traceback
                    traceback.print_exc()
        
        print("⚠️  No flashcards generated from this chunk after all retries")
        return []
    
    def _parse_flashcard_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the AI response into structured flashcards with robust error handling."""
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
        flashcards = self._try_parse_json_with_fixes(response_text)
        
        if not flashcards:
            return []
        
        # Validate structure
        if not isinstance(flashcards, list):
            print("⚠️  Response is not a JSON array")
            return []
        
        # Validate and normalize each flashcard
        valid_flashcards = []
        for i, card in enumerate(flashcards, 1):
            if self._validate_flashcard(card, i):
                # Ensure optional fields exist
                if 'example' not in card:
                    card['example'] = ""
                # Ensure all diagram types exist (already validated above, but ensure they're strings)
                if 'mermaid_diagrams' not in card:
                    card['mermaid_diagrams'] = {}
                if 'math_visualizations' not in card:
                    card['math_visualizations'] = {}
                diagram_types = ['concise', 'analogy', 'eli5', 'real_world_use_case', 'common_mistakes', 'example']
                for diagram_type in diagram_types:
                    if diagram_type not in card['mermaid_diagrams']:
                        card['mermaid_diagrams'][diagram_type] = ""
                    if diagram_type not in card['math_visualizations']:
                        card['math_visualizations'][diagram_type] = ""
                valid_flashcards.append(card)
        
        return valid_flashcards
    
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
        
        # Fix 1: Handle unterminated strings by finding the last quote and closing it
        try:
            # Find unterminated strings (quotes that aren't properly closed)
            quote_pattern = r'"([^"\\]*(\\.[^"\\]*)*)'
            matches = list(re.finditer(quote_pattern, fixed_json))
            if matches:
                last_match = matches[-1]
                if not fixed_json[last_match.end():].strip().startswith('"'):
                    # Add closing quote if missing
                    fixed_json = fixed_json[:last_match.end()] + '"' + fixed_json[last_match.end():]
                    print("   🔧 Fixed unterminated string")
        except Exception:
            pass
        
        # Fix 2: Handle missing commas between objects
        try:
            fixed_json = re.sub(r'}\s*{', '},{', fixed_json)
            print("   🔧 Fixed missing commas between objects")
        except Exception:
            pass
        
        # Fix 3: Remove trailing commas
        try:
            fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
            print("   🔧 Removed trailing commas")
        except Exception:
            pass
        
        # Fix 4: Handle incomplete JSON by finding the last complete object
        try:
            # Find the last complete closing bracket for the array
            last_bracket = fixed_json.rfind(']')
            if last_bracket == -1:
                # No closing bracket found, try to add one
                # First, find the last complete object
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
            # Find individual complete JSON objects within the text
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
        
        # Strategy 5: Last resort - try to find any valid JSON array in the text
        try:
            # Look for patterns like [{"key": "value"}] in the text
            array_pattern = r'\[[\s\S]*?\]'
            matches = re.findall(array_pattern, fixed_json)
            
            for match in matches:
                try:
                    result = json.loads(match)
                    if isinstance(result, list) and len(result) > 0:
                        print(f"   🔧 Found valid JSON array with {len(result)} items")
                        return result
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        
        print("   ❌ All JSON parsing strategies failed")
        return []
    
    def _validate_flashcard(self, card: Dict[str, Any], card_num: int) -> bool:
        """Validate a single flashcard has all required fields."""
        required_fields = ['question', 'answers', 'relevance_score', 'mermaid_diagrams', 'math_visualizations']
        
        # Check basic required fields
        for field in required_fields:
            if field not in card:
                print(f"   ⚠️  Flashcard {card_num} missing required field: {field}")
                return False
        
        # Validate answers structure
        if not isinstance(card['answers'], dict):
            print(f"   ⚠️  Flashcard {card_num}: 'answers' must be an object/dict")
            return False
        
        # Check all 5 answer types are present
        required_answer_types = ['concise', 'analogy', 'eli5', 'real_world_use_case', 'common_mistakes']
        for answer_type in required_answer_types:
            if answer_type not in card['answers']:
                print(f"   ⚠️  Flashcard {card_num} missing answer type: {answer_type}")
                return False
        
        # Validate mermaid_diagrams structure
        if not isinstance(card['mermaid_diagrams'], dict):
            print(f"   ⚠️  Flashcard {card_num}: 'mermaid_diagrams' must be an object/dict")
            return False
        
        # Check all 6 diagram types are present (including example)
        required_diagram_types = ['concise', 'analogy', 'eli5', 'real_world_use_case', 'common_mistakes', 'example']
        for diagram_type in required_diagram_types:
            if diagram_type not in card['mermaid_diagrams']:
                print(f"   ⚠️  Flashcard {card_num} missing diagram type: {diagram_type}")
                return False
            # Validate that diagram content is a string (can be empty)
            if not isinstance(card['mermaid_diagrams'][diagram_type], str):
                print(f"   ⚠️  Flashcard {card_num} diagram '{diagram_type}' must be a string")
                return False
        
        # Validate math_visualizations structure (optional but must exist)
        if not isinstance(card['math_visualizations'], dict):
            print(f"   ⚠️  Flashcard {card_num}: 'math_visualizations' must be an object/dict")
            return False
        
        # Check all 6 math visualization types are present (can be empty strings)
        for viz_type in required_diagram_types:
            if viz_type not in card['math_visualizations']:
                print(f"   ⚠️  Flashcard {card_num} missing math_visualization type: {viz_type}")
                return False
            # Validate that math visualization content is a string (can be empty)
            if not isinstance(card['math_visualizations'][viz_type], str):
                print(f"   ⚠️  Flashcard {card_num} math_visualization '{viz_type}' must be a string")
                return False
        
        # Validate relevance_score
        if not isinstance(card['relevance_score'], dict):
            print(f"   ⚠️  Flashcard {card_num}: 'relevance_score' must be an object/dict")
            return False
        
        if 'score' not in card['relevance_score']:
            print(f"   ⚠️  Flashcard {card_num}: 'relevance_score' missing 'score' field")
            return False
        
        return True
    
    def _display_score_distribution(self, flashcards: List[Dict[str, Any]]):
        """Display the distribution of relevance scores."""
        scores = [card['relevance_score']['score'] for card in flashcards]
        
        high_priority = sum(1 for s in scores if s >= 8)
        medium_priority = sum(1 for s in scores if 5 <= s < 8)
        low_priority = sum(1 for s in scores if s < 5)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        print(f"\n📊 Relevance Score Distribution:")
        print(f"   🔴 High Priority (8-10):   {high_priority} cards")
        print(f"   🟡 Medium Priority (5-7):  {medium_priority} cards")
        print(f"   🟢 Low Priority (1-4):     {low_priority} cards")
        print(f"   📈 Average Score: {avg_score:.1f}/10")