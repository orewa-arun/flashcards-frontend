"""
Cognitive Flashcard Generator - Core AI generation logic.
"""

import os
import json
from typing import Dict, List, Any
import google.generativeai as genai

from config import Config


class CognitiveFlashcardGenerator:
    """Universal flashcard generator with diagram support."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash",
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
        prompt_path = os.path.join(Config.PROMPTS_DIR, "intelligent_flashcard_prompt.txt")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                "Please ensure intelligent_flashcard_prompt.txt exists in the prompts/ directory."
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
        
        # Load and populate template
        prompt_template = self.load_prompt_template()
        prompt = prompt_template.replace("{{COURSE_NAME}}", self.course_name)
        prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", self.textbook_reference)
        prompt = prompt.replace("{{CONTENT_PLACEHOLDER}}", content)
        
        print(f"🤖 Analyzing content and generating flashcards with diagrams...")
        
        try:
            # Generate flashcards with AI
            # Configure generation with higher output token limit
            generation_config = {
                "max_output_tokens": 16384,  # Doubled to handle multiple diagrams per flashcard
                "temperature": 0.7,
            }
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            result_text = response.text.strip()
            
            # Parse JSON response
            flashcards = self._parse_flashcard_response(result_text)
            
            if not flashcards:
                print("⚠️  No flashcards generated from this chunk")
                return []
            
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
            recall_q_count = sum(len(card.get('recall_questions', [])) for card in flashcards)
            print(f"   📊 Mermaid Diagrams: {total_diagrams} across all answer types")
            print(f"   🔢 Math Visualizations: {total_math_viz} Graphviz diagrams")
            print(f"   📝 With Examples: {examples_count} cards")
            print(f"   🧠 Recall Questions: {recall_q_count} total")
            
            return flashcards
            
        except Exception as e:
            print(f"❌ Error generating flashcards: {e}")
            import traceback
            traceback.print_exc()
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
        
        try:
            flashcards = json.loads(response_text)
            
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
                    if 'recall_questions' not in card:
                        card['recall_questions'] = []
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
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error: {e}")
            print(f"   This might be due to truncated output. The chunking strategy should prevent this.")
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