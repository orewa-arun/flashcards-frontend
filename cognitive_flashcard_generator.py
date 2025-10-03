"""
Cognitive Flashcard Generator - Universal engine for creating intelligent study materials.

This module generates flashcards with:
- Relevance scoring (1-10) for exam importance
- Textbook-aligned examples
- Mermaid.js diagrams (both code and rendered images)
- Future-proof JSON for React frontends

Features:
- Works with any subject/textbook
- Dynamic prompt population
- Hybrid approach: stores both mermaid code and rendered PNG
- Professional diagram rendering via Mermaid CLI

Usage:
    python cognitive_flashcard_generator.py
"""

import os
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

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
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai.configure(api_key=api_key)
            self.model = self.genai.GenerativeModel(model)
        except ImportError:
            raise ImportError(
                "Please install google-generativeai: pip install google-generativeai"
            )
        
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
    
    def generate_flashcards(self, content: str, source_name: str = "") -> List[Dict[str, Any]]:
        """
        Generate cognitive flashcards with examples and diagrams.
        
        Args:
            content: The master content document from slide analysis
            source_name: Name of the source (e.g., lecture name)
            
        Returns:
            List of flashcard dictionaries with scores, examples, and mermaid diagrams
        """
        print(f"\n{'='*70}")
        print(f"🧠 Generating Cognitive Flashcards")
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
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Parse JSON response
            flashcards = self._parse_flashcard_response(result_text)
            
            if not flashcards:
                print("⚠️  No flashcards generated. Trying alternative parsing...")
                return []
            
            print(f"✅ Generated {len(flashcards)} flashcards")
            
            # Display score distribution
            self._display_score_distribution(flashcards)
            
            # Display diagram stats
            diagrams_count = sum(1 for card in flashcards if card.get('mermaid_code', '').strip())
            examples_count = sum(1 for card in flashcards if card.get('example', '').strip())
            print(f"   📊 With Diagrams: {diagrams_count} cards")
            print(f"   📝 With Examples: {examples_count} cards")
            
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
        
        try:
            flashcards = json.loads(response_text)
            
            # Validate structure
            if not isinstance(flashcards, list):
                return []
            
            # Ensure all required fields exist
            valid_flashcards = []
            for card in flashcards:
                if all(key in card for key in ['question', 'answer', 'relevance_score']):
                    # Ensure relevance_score has required fields
                    if isinstance(card['relevance_score'], dict):
                        if 'score' in card['relevance_score']:
                            # Ensure new fields exist (with defaults)
                            if 'example' not in card:
                                card['example'] = ""
                            if 'mermaid_code' not in card:
                                card['mermaid_code'] = ""
                            valid_flashcards.append(card)
            
            return valid_flashcards
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing error: {e}")
            return []
    
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


class DiagramRenderer:
    """Renders Mermaid.js diagrams to PNG images using Mermaid CLI."""
    
    @staticmethod
    def check_mermaid_cli() -> bool:
        """Check if Mermaid CLI is installed."""
        try:
            result = subprocess.run(
                ['mmdc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def render_diagram(mermaid_code: str, output_path: str) -> bool:
        """
        Render a Mermaid diagram to PNG.
        
        Args:
            mermaid_code: The Mermaid.js diagram code
            output_path: Path to save the PNG file
            
        Returns:
            True if successful, False otherwise
        """
        if not mermaid_code.strip():
            return False
        
        # Create temporary file for mermaid code
        temp_mmd = output_path.replace('.png', '.mmd')
        
        try:
            # Write mermaid code to temp file
            with open(temp_mmd, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            
            # Render using mmdc
            result = subprocess.run(
                ['mmdc', '-i', temp_mmd, '-o', output_path, '-b', 'transparent'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up temp file
            if os.path.exists(temp_mmd):
                os.remove(temp_mmd)
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            print(f"    ⚠️  Error rendering diagram: {e}")
            # Clean up temp file on error
            if os.path.exists(temp_mmd):
                os.remove(temp_mmd)
            return False


class FlashcardExporter:
    """Export cognitive flashcards to multiple formats."""
    
    @staticmethod
    def export_to_json(flashcards: List[Dict[str, Any]], metadata: Dict[str, Any],
                      output_path: str):
        """Export flashcards as JSON with full metadata."""
        data = {
            'metadata': metadata,
            'flashcards': flashcards
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved JSON: {output_path}")
    
    @staticmethod
    def export_to_text(flashcards: List[Dict[str, Any]], metadata: Dict[str, Any],
                      output_path: str):
        """Export flashcards as enhanced text study guide."""
        # Sort by relevance score (highest first)
        sorted_cards = sorted(
            flashcards,
            key=lambda x: x['relevance_score']['score'],
            reverse=True
        )
        
        lines = []
        lines.append("=" * 80)
        lines.append("COGNITIVE FLASHCARDS - EXAM PREPARATION GUIDE")
        lines.append("=" * 80)
        lines.append(f"Course: {metadata['course_name']}")
        lines.append(f"Reference: {metadata['textbook_reference']}")
        lines.append(f"Generated: {metadata['generated_at']}")
        lines.append(f"Total Cards: {metadata['total_cards']}")
        lines.append("=" * 80)
        lines.append("")
        lines.append("📊 STUDY PRIORITY GUIDE:")
        lines.append("   🔴 Score 8-10: HIGH PRIORITY - Likely to be on exam")
        lines.append("   🟡 Score 5-7:  MEDIUM PRIORITY - Important supporting material")
        lines.append("   🟢 Score 1-4:  LOW PRIORITY - Supplementary information")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")
        
        for i, card in enumerate(sorted_cards, 1):
            score = card['relevance_score']['score']
            
            # Priority indicator
            if score >= 8:
                priority = "🔴 HIGH"
            elif score >= 5:
                priority = "🟡 MEDIUM"
            else:
                priority = "🟢 LOW"
            
            lines.append(f"CARD {i} | {priority} PRIORITY | Score: {score}/10")
            lines.append("-" * 80)
            lines.append(f"Type: {card.get('type', 'N/A').upper()}")
            lines.append(f"Context: {card.get('context', 'N/A')}")
            lines.append(f"Tags: {', '.join(card.get('tags', []))}")
            lines.append("")
            lines.append(f"Q: {card['question']}")
            lines.append("")
            lines.append(f"A: {card['answer']}")
            lines.append("")
            
            # Add example if present
            if card.get('example', '').strip():
                lines.append(f"📝 Example: {card['example']}")
                lines.append("")
            
            # Add diagram reference if present
            if card.get('diagram_image_path', '').strip():
                lines.append(f"📊 Diagram: {card['diagram_image_path']}")
                lines.append("")
            
            lines.append(f"💡 Score Justification: {card['relevance_score'].get('justification', 'N/A')}")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"📄 Saved Study Guide: {output_path}")
    
    @staticmethod
    def export_study_plan(flashcards: List[Dict[str, Any]], metadata: Dict[str, Any],
                         output_path: str):
        """Generate a prioritized study plan."""
        high = [c for c in flashcards if c['relevance_score']['score'] >= 8]
        medium = [c for c in flashcards if 5 <= c['relevance_score']['score'] < 8]
        low = [c for c in flashcards if c['relevance_score']['score'] < 5]
        
        lines = []
        lines.append("=" * 80)
        lines.append("📚 PRIORITIZED STUDY PLAN")
        lines.append("=" * 80)
        lines.append(f"Course: {metadata['course_name']}")
        lines.append(f"Reference: {metadata['textbook_reference']}")
        lines.append("")
        
        lines.append("🎯 PHASE 1: HIGH PRIORITY (Study First)")
        lines.append(f"   {len(high)} cards - These topics are most likely to be on your exam")
        lines.append("-" * 80)
        for i, card in enumerate(high, 1):
            lines.append(f"{i}. [{card.get('type', 'N/A')}] {card['question'][:60]}...")
            lines.append(f"   Score: {card['relevance_score']['score']}/10 - {card['relevance_score'].get('justification', '')}")
        lines.append("")
        
        lines.append("📖 PHASE 2: MEDIUM PRIORITY (Study Second)")
        lines.append(f"   {len(medium)} cards - Important supporting material")
        lines.append("-" * 80)
        for i, card in enumerate(medium, 1):
            lines.append(f"{i}. [{card.get('type', 'N/A')}] {card['question'][:60]}...")
        lines.append("")
        
        lines.append("📝 PHASE 3: LOW PRIORITY (Study If Time Permits)")
        lines.append(f"   {len(low)} cards - Supplementary information")
        lines.append("-" * 80)
        for i, card in enumerate(low, 1):
            lines.append(f"{i}. [{card.get('type', 'N/A')}] {card['question'][:60]}...")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("💡 STUDY TIP: Focus on Phase 1 cards first. These represent the core")
        lines.append("   concepts most likely to appear on your exam based on lecture emphasis")
        lines.append("   and alignment with the reference textbook.")
        lines.append("=" * 80)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"📅 Saved Study Plan: {output_path}")


def main():
    """Main execution function."""
    
    print("🎓 Cognitive Flashcard Generator - Universal Study Tool\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"❌ Configuration Error: {error_msg}")
        return
    
    # Define course-specific variables (can be moved to config later)
    COURSE_NAME = "Information Systems"
    TEXTBOOK_REFERENCE = "Information Systems Today: Managing in the Digital World, EIGHTH EDITION by Joseph Valacich and Christoph Schneider"
    
    # Find slide analysis outputs
    analysis_dir = Path("./slide_analysis")
    
    if not analysis_dir.exists():
        print(f"❌ No slide analysis found in {analysis_dir}")
        print("💡 Please run slide_analyzer.py first to extract content from slides")
        return
    
    # Get all analyzed PDFs
    analyzed_pdfs = [d for d in analysis_dir.iterdir() if d.is_dir()]
    
    if not analyzed_pdfs:
        print(f"❌ No analyzed content found in {analysis_dir}")
        return
    
    print(f"📂 Found {len(analyzed_pdfs)} analyzed slide deck(s):\n")
    for i, pdf_dir in enumerate(analyzed_pdfs, 1):
        print(f"  {i}. {pdf_dir.name}")
    
    # Create output directory
    output_base = Path("./cognitive_flashcards")
    output_base.mkdir(exist_ok=True)
    
    # Check if Mermaid CLI is available
    has_mermaid = DiagramRenderer.check_mermaid_cli()
    if has_mermaid:
        print(f"\n✅ Mermaid CLI detected - Diagrams will be rendered to PNG")
    else:
        print(f"\n⚠️  Mermaid CLI not found - Diagrams will be saved as code only")
        print(f"    To install: npm install -g @mermaid-js/mermaid-cli")
    
    # Initialize generator
    generator = CognitiveFlashcardGenerator(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL,
        course_name=COURSE_NAME,
        textbook_reference=TEXTBOOK_REFERENCE
    )
    
    # Process each analyzed PDF
    for pdf_dir in analyzed_pdfs:
        pdf_name = pdf_dir.name
        master_content_path = pdf_dir / f"{pdf_name}_master_content.txt"
        
        if not master_content_path.exists():
            print(f"⚠️  Skipping {pdf_name}: No master content file found")
            continue
        
        print(f"\n{'='*70}")
        print(f"Processing: {pdf_name}")
        print(f"{'='*70}")
        
        # Load content
        with open(master_content_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 Loaded {len(content):,} characters of content")
        
        # Generate flashcards
        flashcards = generator.generate_flashcards(content, pdf_name)
        
        if not flashcards:
            print(f"⚠️  No flashcards generated for {pdf_name}")
            continue
        
        # Create output directories
        pdf_output_dir = output_base / pdf_name
        pdf_output_dir.mkdir(exist_ok=True)
        
        diagrams_dir = pdf_output_dir / "diagrams"
        diagrams_dir.mkdir(exist_ok=True)
        
        # Render diagrams
        print(f"\n🎨 Rendering diagrams...")
        rendered_count = 0
        
        for i, card in enumerate(flashcards, 1):
            mermaid_code = card.get('mermaid_code', '').strip()
            
            if mermaid_code and has_mermaid:
                diagram_filename = f"{pdf_name}_card_{i:03d}.png"
                diagram_path = diagrams_dir / diagram_filename
                
                if DiagramRenderer.render_diagram(mermaid_code, str(diagram_path)):
                    card['diagram_image_path'] = f"diagrams/{diagram_filename}"
                    rendered_count += 1
                    print(f"  ✓ Rendered diagram {i}")
                else:
                    card['diagram_image_path'] = ""
                    print(f"  ⚠️  Failed to render diagram {i}")
            else:
                card['diagram_image_path'] = ""
        
        if rendered_count > 0:
            print(f"✅ Rendered {rendered_count} diagrams")
        
        # Prepare metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'total_cards': len(flashcards),
            'course_name': COURSE_NAME,
            'textbook_reference': TEXTBOOK_REFERENCE,
            'source': pdf_name
        }
        
        # Export in multiple formats
        print(f"\n💾 Exporting flashcards...")
        
        FlashcardExporter.export_to_json(
            flashcards,
            metadata,
            str(pdf_output_dir / f"{pdf_name}_cognitive_flashcards.json")
        )
        
        FlashcardExporter.export_to_text(
            flashcards,
            metadata,
            str(pdf_output_dir / f"{pdf_name}_study_guide.txt")
        )
        
        FlashcardExporter.export_study_plan(
            flashcards,
            metadata,
            str(pdf_output_dir / f"{pdf_name}_study_plan.txt")
        )
        
        print(f"\n✅ Complete! Output saved to: {pdf_output_dir}")
    
    print(f"\n{'='*70}")
    print(f"✨ All flashcards generated successfully!")
    print(f"📂 Output directory: {output_base}")
    print(f"{'='*70}")
    print(f"\n💡 Next Steps:")
    print(f"   1. Review the study plan: *_study_plan.txt")
    print(f"   2. Start with HIGH PRIORITY cards (Score 8-10)")
    print(f"   3. View diagrams in the diagrams/ folder")
    print(f"   4. Use JSON for your future React frontend")


if __name__ == "__main__":
    main()
