"""
JSON extraction module for flashcard files.
Extracts clean text from cognitive_flashcards_only.json files,
excluding mermaid diagrams and mathematical visualizations.
"""
import json
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlashcardJSONExtractor:
    """Extract clean text from flashcard JSON files."""
    
    def __init__(self):
        """Initialize extractor."""
        pass
    
    def extract(self, json_path: str, source_id: str = None) -> Dict:
        """
        Extract text content from a flashcard JSON file.
        
        Extracts:
        - Questions
        - All answer variants (concise, analogy, eli5, real_world_use_case, common_mistakes)
        - Examples
        - Context
        
        Ignores:
        - mermaid_diagrams
        - math_visualizations
        - mermaid_code
        - diagram_image_path
        
        Args:
            json_path: Path to the flashcard JSON file
            source_id: Unique identifier for the source (defaults to filename)
            
        Returns:
            Dictionary containing:
                - text_blocks: List of text content blocks with metadata
                - metadata: Overall file metadata
                - source_path: Original JSON path
                - source_id: Source identifier
        """
        if source_id is None:
            import os
            source_id = os.path.splitext(os.path.basename(json_path))[0]
        
        logger.info(f"Extracting flashcard content from: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON from {json_path}: {e}")
            raise
        
        # Extract metadata
        file_metadata = data.get('metadata', {})
        flashcards = data.get('flashcards', [])
        
        text_blocks = []
        
        for idx, card in enumerate(flashcards):
            # Extract question
            question = card.get('question', '').strip()
            if not question:
                continue
            
            # Build a comprehensive text block for this flashcard
            text_parts = [f"Question: {question}"]
            
            # Extract all answer variants
            answers = card.get('answers', {})
            if answers:
                # Concise answer
                if 'concise' in answers and answers['concise']:
                    text_parts.append(f"Answer: {answers['concise'].strip()}")
                
                # Analogy
                if 'analogy' in answers and answers['analogy']:
                    text_parts.append(f"Analogy: {answers['analogy'].strip()}")
                
                # ELI5 (Explain Like I'm 5)
                if 'eli5' in answers and answers['eli5']:
                    text_parts.append(f"Simple Explanation: {answers['eli5'].strip()}")
                
                # Real world use case
                if 'real_world_use_case' in answers and answers['real_world_use_case']:
                    text_parts.append(f"Real-world Example: {answers['real_world_use_case'].strip()}")
                
                # Common mistakes
                if 'common_mistakes' in answers and answers['common_mistakes']:
                    text_parts.append(f"Common Mistakes: {answers['common_mistakes'].strip()}")
            
            # Extract example (if different from answers)
            example = card.get('example', '').strip()
            if example:
                text_parts.append(f"Example: {example}")
            
            # Extract context
            context = card.get('context', '').strip()
            if context:
                text_parts.append(f"Context: {context}")
            
            # Combine into one text block
            combined_text = "\n\n".join(text_parts)
            
            # Create metadata for this text block
            block_metadata = {
                'flashcard_id': card.get('flashcard_id', f"{source_id}_{idx}"),
                'type': card.get('type', 'unknown'),
                'context': context,
                'tags': card.get('tags', []),
                'relevance_score': card.get('relevance_score', {}).get('score', 0),
                'source_id': source_id,
                'source_path': json_path,
                'block_index': idx
            }
            
            text_blocks.append({
                'text': combined_text,
                'metadata': block_metadata
            })
        
        result = {
            'text_blocks': text_blocks,
            'file_metadata': file_metadata,
            'source_path': json_path,
            'source_id': source_id
        }
        
        logger.info(f"Extraction complete: {len(text_blocks)} text blocks from {len(flashcards)} flashcards")
        
        return result

