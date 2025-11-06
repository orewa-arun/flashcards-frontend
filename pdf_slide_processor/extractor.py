"""
Information Extractor - Converts analyzed slides into structured documents.
"""

import json
from typing import Dict, List, Any, Optional


class InformationExtractor:
    """Converts analyzed slides into structured text documents."""
    
    @staticmethod
    def save_structured_json(analyzed_slides: List[Dict[str, Any]], output_path: str):
        """Save analyzed slides as structured JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_slides': len(analyzed_slides),
                'slides': analyzed_slides
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Structured JSON saved: {output_path}")

