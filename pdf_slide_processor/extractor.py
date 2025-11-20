"""
Information Extractor - Converts analyzed slides into structured documents.
"""

import json
from typing import Dict, List, Any, Optional


class InformationExtractor:
    """Converts analyzed slides into structured text documents."""
    
    @staticmethod
    def save_structured_json(
        analyzed_slides: List[Dict[str, Any]], 
        output_path: str,
        lecture_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save analyzed slides as structured JSON.
        
        Args:
            analyzed_slides: List of analyzed slide data
            output_path: Path to save the JSON file
            lecture_metadata: Optional metadata like summary and key concepts
        """
        data = {
            'total_slides': len(analyzed_slides),
            'slides': analyzed_slides
        }
        
        # Add lecture metadata if provided (summary, key concepts, etc.)
        if lecture_metadata:
            data.update(lecture_metadata)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Structured JSON saved: {output_path}")

