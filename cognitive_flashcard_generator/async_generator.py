"""
Async Cognitive Flashcard Generator - Batched AI generation logic.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
import google.generativeai as genai

from config import Config


class AsyncCognitiveFlashcardGenerator:
    """Async flashcard generator with batching support."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 course_name: str = "", textbook_reference: str = ""):
        """
        Initialize the async cognitive flashcard generator.
        
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
        self._prompt_template = None
    
    def load_prompt_template(self) -> str:
        """Load the generic prompt template (cached)."""
        if self._prompt_template is None:
            prompt_path = os.path.join(Config.PROMPTS_DIR, "intelligent_flashcard_only_prompt_v2.txt")
            
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._prompt_template = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Prompt file not found: {prompt_path}\n"
                    "Please ensure intelligent_flashcard_only_prompt_v2.txt exists in the prompts/ directory."
                )
        
        return self._prompt_template
    
    async def generate_flashcards_async(self, content: str, source_name: str = "", 
                                       chunk_info: str = "", task_id: str = "") -> Dict[str, Any]:
        """
        Generate cognitive flashcards asynchronously.
        
        Args:
            content: The content to generate flashcards from
            source_name: Name of the source (e.g., lecture name)
            chunk_info: Optional info about which chunk this is
            task_id: Unique identifier for this task
            
        Returns:
            Dictionary with task_id, flashcards, and metadata
        """
        print(f"🚀 [Task {task_id}] Starting async generation for {source_name} {chunk_info}")
        
        try:
            flashcards = await self._generate_with_retry_async(content, source_name, chunk_info, task_id)
            
            return {
                'task_id': task_id,
                'source_name': source_name,
                'chunk_info': chunk_info,
                'flashcards': flashcards,
                'success': len(flashcards) > 0,
                'error': None
            }
        except Exception as e:
            print(f"❌ [Task {task_id}] Error: {e}")
            return {
                'task_id': task_id,
                'source_name': source_name,
                'chunk_info': chunk_info,
                'flashcards': [],
                'success': False,
                'error': str(e)
            }
    
    async def _generate_with_retry_async(self, content: str, source_name: str = "", 
                                        chunk_info: str = "", task_id: str = "",
                                        max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Generate flashcards with retry logic asynchronously.
        """
        original_content = content
        
        for attempt in range(max_retries):
            try:
                # Reduce content size on each retry
                if attempt > 0:
                    reduction_factor = 0.7 ** attempt
                    max_chars = int(len(original_content) * reduction_factor)
                    content = original_content[:max_chars]
                    print(f"🔄 [Task {task_id}] Retry {attempt + 1}/{max_retries}: Reduced to {len(content):,} chars")
                
                # Load and populate template
                prompt_template = self.load_prompt_template()
                prompt = prompt_template.replace("{{COURSE_NAME}}", self.course_name)
                prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
                prompt = prompt.replace("{{CONTENT_PLACEHOLDER}}", content)
                
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
                flashcards = self._parse_flashcard_response(result_text)
                
                if flashcards:
                    print(f"✅ [Task {task_id}] Generated {len(flashcards)} flashcards")
                    return flashcards
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️  [Task {task_id}] No flashcards on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    
            except Exception as e:
                print(f"❌ [Task {task_id}] Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Longer delay on error
                    continue
                else:
                    raise
        
        return []
    
    def _parse_flashcard_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the AI response into structured flashcards."""
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
        flashcards = self._try_parse_json_with_fixes(response_text)
        
        if not flashcards or not isinstance(flashcards, list):
            return []
        
        # Validate and normalize each flashcard
        valid_flashcards = []
        for i, card in enumerate(flashcards, 1):
            if self._validate_flashcard(card, i):
                # Ensure optional fields exist
                if 'example' not in card:
                    card['example'] = ""
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
        """Try to parse JSON with multiple fallback strategies."""
        import re
        
        # Strategy 1: Try parsing as-is
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Fix common JSON issues
        fixed_json = json_text
        
        # Remove trailing commas
        try:
            fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
        except Exception:
            pass
        
        # Try parsing the fixed JSON
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract partial valid JSON objects
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
                        obj_text = fixed_json[start_pos:i+1]
                        try:
                            obj = json.loads(obj_text)
                            objects.append(obj)
                        except json.JSONDecodeError:
                            pass
                        start_pos = -1
            
            if objects:
                return objects
        except Exception:
            pass
        
        return []
    
    def _validate_flashcard(self, card: Dict[str, Any], card_num: int) -> bool:
        """Validate a single flashcard has all required fields."""
        required_fields = ['question', 'answers', 'relevance_score', 'mermaid_diagrams', 'math_visualizations']
        
        for field in required_fields:
            if field not in card:
                return False
        
        if not isinstance(card['answers'], dict):
            return False
        
        required_answer_types = ['concise', 'analogy', 'eli5', 'real_world_use_case', 'common_mistakes']
        for answer_type in required_answer_types:
            if answer_type not in card['answers']:
                return False
        
        if not isinstance(card['mermaid_diagrams'], dict):
            return False
        
        if not isinstance(card['math_visualizations'], dict):
            return False
        
        if not isinstance(card['relevance_score'], dict):
            return False
        
        if 'score' not in card['relevance_score']:
            return False
        
        return True

