"""
Information Extractor - Converts analyzed slides into structured documents.
"""

import json
from typing import Dict, List, Any, Optional


class InformationExtractor:
    """Converts analyzed slides into structured text documents."""
    
    @staticmethod
    def create_master_document(analyzed_slides: List[Dict[str, Any]], 
                               output_path: str,
                               course_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a comprehensive text document from analyzed slides.
        
        Args:
            analyzed_slides: List of analyzed slide data
            output_path: Path to save the master document
            course_metadata: Optional course metadata to include in the document
            
        Returns:
            The master document as a string
        """
        print(f"\n{'='*70}")
        print(f"📝 Creating master document")
        print(f"{'='*70}")
        
        document_lines = []
        document_lines.append("=" * 80)
        document_lines.append("LECTURE CONTENT - EXTRACTED FROM SLIDES")
        document_lines.append("=" * 80)
        document_lines.append("")
        
        # Add course metadata if provided
        if course_metadata:
            document_lines.append("COURSE INFORMATION:")
            document_lines.append(f"  Course: {course_metadata.get('course_name', 'N/A')}")
            document_lines.append(f"  Course Code: {course_metadata.get('course_code', 'N/A')}")
            if course_metadata.get('reference_textbooks'):
                document_lines.append("  Reference Textbooks:")
                for textbook in course_metadata.get('reference_textbooks', []):
                    document_lines.append(f"    - {textbook}")
            if course_metadata.get('course_description'):
                document_lines.append(f"  Description: {course_metadata.get('course_description')}")
            document_lines.append("")
            document_lines.append("=" * 80)
            document_lines.append("")
        
        for slide in analyzed_slides:
            analysis = slide.get('analysis', {})
            
            # Generic separator - no slide numbers for course-agnostic content
            document_lines.append("\n" + "=" * 80)
            document_lines.append(f"TOPIC: {analysis.get('title', 'Content')}")
            document_lines.append("=" * 80)
            document_lines.append("")
            
            # Main text content
            if analysis.get('main_text'):
                document_lines.append("CONTENT:")
                document_lines.append(analysis['main_text'])
                document_lines.append("")
            
            # Key concepts
            if analysis.get('key_concepts'):
                document_lines.append("KEY CONCEPTS:")
                for concept in analysis['key_concepts']:
                    document_lines.append(f"  • {concept}")
                document_lines.append("")
            
            # Definitions
            if analysis.get('definitions'):
                document_lines.append("DEFINITIONS:")
                for defn in analysis['definitions']:
                    term = defn.get('term', 'Unknown')
                    definition = defn.get('definition', 'N/A')
                    document_lines.append(f"  • {term}: {definition}")
                document_lines.append("")
            
            # Diagrams
            if analysis.get('diagrams'):
                document_lines.append("DIAGRAMS & VISUALS:")
                for i, diagram in enumerate(analysis['diagrams'], 1):
                    dtype = diagram.get('type', 'Diagram')
                    desc = diagram.get('description', 'N/A')
                    document_lines.append(f"  {i}. {dtype}:")
                    document_lines.append(f"     {desc}")
                    
                    if diagram.get('key_points'):
                        document_lines.append(f"     Key Points:")
                        for point in diagram['key_points']:
                            document_lines.append(f"       - {point}")
                document_lines.append("")
            
            # Examples
            if analysis.get('examples'):
                document_lines.append("EXAMPLES:")
                for example in analysis['examples']:
                    document_lines.append(f"  • {example}")
                document_lines.append("")
            
            # Formulas
            if analysis.get('formulas'):
                document_lines.append("FORMULAS:")
                for formula in analysis['formulas']:
                    document_lines.append(f"  • {formula}")
                document_lines.append("")
            
            # Notes
            if analysis.get('notes'):
                document_lines.append("NOTES:")
                document_lines.append(f"  {analysis['notes']}")
                document_lines.append("")
        
        # Join all lines
        master_document = "\n".join(document_lines)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(master_document)
        
        print(f"✅ Master document saved: {output_path}")
        print(f"   Total length: {len(master_document):,} characters")
        
        return master_document
    
    @staticmethod
    def save_structured_json(analyzed_slides: List[Dict[str, Any]], output_path: str):
        """Save analyzed slides as structured JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_slides': len(analyzed_slides),
                'slides': analyzed_slides
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Structured JSON saved: {output_path}")

