"""
AI-Powered Flashcard Generation System with LaTeX Support
Modular architecture with pluggable LLM providers + Beautiful Math Rendering
"""

import os
import json
import re
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import PyPDF2

# Import configuration
from config import Config
from latex_config import LaTeXConfig, LaTeXTemplates, AnkiConfig


# ==================== AI Provider Interface ====================

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_flashcards(self, content: str, context: str = "") -> List[Dict[str, str]]:
        """
        Generate flashcards from content.
        Returns list of dicts with 'question' and 'answer' keys.
        """
        pass
    
    @abstractmethod
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content to extract key topics and concepts."""
        pass


# ==================== Gemini Provider ====================

class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        try:
            import google.generativeai as genai  # type: ignore
            self.genai = genai
            self.genai.configure(api_key=api_key)  # type: ignore
            self.model = self.genai.GenerativeModel(model)  # type: ignore
        except ImportError:
            raise ImportError(
                "Please install google-generativeai: pip install google-generativeai"
            )
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file."""
        prompt_path = os.path.join(Config.PROMPTS_DIR, filename)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Prompt file {prompt_path} not found. Using fallback prompt.")
            return "Generate flashcards from the given content."
    
    def generate_flashcards(self, content: str, context: str = "") -> List[Dict[str, str]]:
        """Generate flashcards using Gemini with LaTeX support."""
        
        # Load prompt from file
        prompt_template = self._load_prompt("flashcard_generation_prompt.txt")
        prompt = prompt_template.replace(
            "{{CONTEXT_PLACEHOLDER}}", context if context else "Academic lecture material"
        ).replace(
            "{{CONTENT_PLACEHOLDER}}", content
        )
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up response - remove markdown code blocks if present
            if text.startswith('```'):
                # Extract content between code fences
                parts = text.split('```')
                if len(parts) >= 2:
                    text = parts[1]
                    if text.startswith('json'):
                        text = text[4:].strip()
            
            # Try to parse JSON directly first
            try:
                flashcards = json.loads(text)
                return flashcards
            except json.JSONDecodeError:
                # If that fails, try escaping backslashes (AI may output single backslashes)
                try:
                    # Only escape unescaped backslashes
                    # Replace single backslashes with double, but preserve already-escaped ones
                    text_escaped = re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', text)
                    flashcards = json.loads(text_escaped)
                    return flashcards
                except:
                    # If still failing, raise the original error
                    raise
            
        except json.JSONDecodeError as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Response was: {response.text[:500]}")
            print(f"\nTrying alternative parsing method...")
            
            # Fallback: Try to extract cards manually
            try:
                # Find all card-like objects in the text
                card_pattern = r'\{[^}]*"question"[^}]*\}'
                potential_cards = re.findall(card_pattern, response.text, re.DOTALL)
                
                if potential_cards:
                    print(f"Found {len(potential_cards)} potential cards, attempting manual parse...")
                    # This is a last resort - just return empty for now
                    return []
            except:
                pass
            
            return []
        except Exception as e:
            print(f"Error generating flashcards: {e}")
            return []
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content structure and topics."""
        
        # Load prompt from file
        prompt_template = self._load_prompt("content_analysis_prompt.txt")
        prompt = prompt_template.replace("{{CONTENT_PLACEHOLDER}}", content)
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:].strip()
            
            analysis = json.loads(text)
            return analysis
            
        except Exception as e:
            print(f"Error analyzing content: {e}")
            return {
                "title": "Unknown",
                "topics": [],
                "difficulty_level": "intermediate",
                "prerequisites": [],
                "key_formulas": []
            }


# ==================== LaTeX Renderer ====================

class LaTeXRenderer:
    """Generate beautiful LaTeX documents from flashcards."""
    
    @staticmethod
    def generate_latex_document(result: Dict[str, Any], output_path: str):
        """Generate a complete LaTeX document with flashcards."""
        if not Config.LATEX_ENABLED:
            return
        
        title = result['analysis'].get('title', 'Flashcards')
        
        # Generate document header
        latex_content = LaTeXTemplates.get_document_header(title)
        
        # Add course information
        latex_content += LaTeXTemplates.get_course_info_section(
            result['analysis'],
            result['total_flashcards']
        )
        
        # Add each flashcard
        for i, card in enumerate(result['flashcards'], 1):
            card_type = card.get('type', 'general').title()
            difficulty = card.get('difficulty', 'medium').title()
            tags = ', '.join(card.get('tags', []))
            
            latex_content += LaTeXTemplates.get_flashcard_card(
                i, card_type, difficulty,
                card['question'], card['answer'], tags
            )
        
        # Add document footer
        latex_content += LaTeXTemplates.get_document_footer()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
    
    @staticmethod
    def generate_anki_latex_compatible(flashcards: List[Dict[str, str]], output_path: str):
        """Generate Anki-compatible format with LaTeX preserved."""
        if not Config.ANKI_ENABLED:
            return
        
        def convert_latex_to_anki(text: str) -> str:
            """Convert $...$ and $$...$$ to Anki's format."""
            patterns = AnkiConfig.get_conversion_patterns()
            
            # First, handle display math $$...$$ (must be done before inline math)
            text = re.sub(r'(?<!\[)\$\$(?!\])', patterns['display_start'], text)
            text = re.sub(r'(?<!\[/)\$\$(?!\])', patterns['display_end'], text)
            
            # Then handle inline math $...$
            text = re.sub(r'(?<!\$)(?<!\[)\$(?!\$)(?!\])', patterns['inline_start'], text)
            text = re.sub(r'(?<!\$)(?<!/)\$(?!\$)(?!\])', patterns['inline_end'], text)
            
            return text
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(AnkiConfig.FILE_HEADER)
            f.write("\n")
            
            for card in flashcards:
                question = card['question'].replace('|', '\\|')
                answer = card['answer'].replace('|', '\\|')
                tags = ' '.join(card.get('tags', []))
                
                # Convert LaTeX to Anki format
                question = convert_latex_to_anki(question)
                answer = convert_latex_to_anki(answer)
                
                f.write(f"{question}{AnkiConfig.FIELD_SEPARATOR}{answer}{AnkiConfig.FIELD_SEPARATOR}{tags}\n")


# ==================== Flashcard Generator ====================

class FlashcardGenerator:
    """Main flashcard generation orchestrator."""
    
    def __init__(self, ai_provider: AIProvider, output_dir: str = "flashcards"):
        self.ai_provider = ai_provider
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    text += f"\n--- Page {page_num} ---\n{page_text}"
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        return text
    
    def chunk_content(self, text: str) -> List[str]:
        """Split content into manageable chunks for AI processing."""
        max_chunk_size = Config.MAX_CHUNK_SIZE
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any] | None:
        """Process a single PDF and generate flashcards."""
        print(f"\n{'='*60}")
        print(f"Processing: {Path(pdf_path).name}")
        print(f"{'='*60}")
        
        # Extract text
        print("📄 Extracting text from PDF...")
        content = self.extract_text_from_pdf(pdf_path)
        
        if not content.strip():
            print("❌ No text could be extracted from PDF")
            return None
        
        print(f"✓ Extracted {len(content)} characters")
        
        # Analyze content
        print("🔍 Analyzing content structure...")
        analysis = self.ai_provider.analyze_content(content[:3000])
        print(f"✓ Topic: {analysis.get('title', 'Unknown')}")
        print(f"✓ Key topics: {', '.join(analysis.get('topics', [])[:5])}")
        
        # Generate flashcards
        print("🎴 Generating flashcards with AI (LaTeX-enabled)...")
        chunks = self.chunk_content(content)
        all_flashcards = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"  Processing chunk {i}/{len(chunks)}...")
            context = f"{analysis.get('title', 'Lecture material')} - Part {i}"
            flashcards = self.ai_provider.generate_flashcards(chunk, context)
            all_flashcards.extend(flashcards)
        
        print(f"✓ Generated {len(all_flashcards)} flashcards")
        
        # Prepare output
        result = {
            "source": Path(pdf_path).name,
            "analysis": analysis,
            "flashcards": all_flashcards,
            "total_flashcards": len(all_flashcards)
        }
        
        # Save output
        self._save_flashcards(result)
        
        return result
    
    def _save_flashcards(self, result: Dict[str, Any]):
        """Save flashcards in multiple formats including LaTeX."""
        base_name = Path(result['source']).stem
        
        # 1. Save as JSON (with LaTeX preserved)
        if Config.GENERATE_JSON:
            json_path = os.path.join(self.output_dir, f"{base_name}_flashcards.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved JSON: {json_path}")
        
        # 2. Save as readable text (with LaTeX preserved)
        if Config.GENERATE_TXT:
            txt_path = os.path.join(self.output_dir, f"{base_name}_flashcards.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"FLASHCARDS: {result['analysis'].get('title', result['source'])}\n")
                f.write(f"{'='*80}\n\n")
                f.write(f"Topics: {', '.join(result['analysis'].get('topics', []))}\n")
                f.write(f"Total Cards: {result['total_flashcards']}\n")
                f.write(f"Note: Math formulas are in LaTeX format ($...$ or $$...$$)\n")
                f.write(f"{'='*80}\n\n")
                
                for i, card in enumerate(result['flashcards'], 1):
                    f.write(f"CARD {i}\n")
                    f.write(f"Type: {card.get('type', 'general').upper()}")
                    f.write(f" | Difficulty: {card.get('difficulty', 'medium').upper()}\n")
                    f.write(f"Tags: {', '.join(card.get('tags', []))}\n\n")
                    f.write(f"Q: {card['question']}\n\n")
                    f.write(f"A: {card['answer']}\n")
                    f.write(f"{'-'*80}\n\n")
            
            print(f"💾 Saved TXT: {txt_path}")
        
        # 3. Save as Beautiful LaTeX Document
        if Config.GENERATE_TEX and Config.LATEX_ENABLED:
            latex_path = os.path.join(self.output_dir, f"{base_name}_flashcards.tex")
            LaTeXRenderer.generate_latex_document(result, latex_path)
            print(f"📐 Saved LaTeX: {latex_path}")
            print(f"   → Compile with: {Config.LATEX_COMPILE_COMMAND} {latex_path}")
        
        # 4. Save as Anki-compatible format (LaTeX preserved)
        if Config.GENERATE_ANKI and Config.ANKI_ENABLED:
            anki_path = os.path.join(self.output_dir, f"{base_name}_anki.txt")
            LaTeXRenderer.generate_anki_latex_compatible(result['flashcards'], anki_path)
            print(f"🃏 Saved Anki (LaTeX): {anki_path}")
        
        # 5. Save as CSV (for simple import, LaTeX preserved)
        if Config.GENERATE_CSV:
            csv_path = os.path.join(self.output_dir, f"{base_name}_simple.csv")
            with open(csv_path, 'w', encoding='utf-8') as f:
                for card in result['flashcards']:
                    question = card['question'].replace('"', '""').replace('\n', ' ')
                    answer = card['answer'].replace('"', '""').replace('\n', ' ')
                    tags = ' '.join(card.get('tags', []))
                    f.write(f'"{question}","{answer}","{tags}"\n')
            
            print(f"💾 Saved CSV: {csv_path}")
        
        # Create README for LaTeX compilation
        readme_path = os.path.join(self.output_dir, "README_LATEX.txt")
        with open(readme_path, 'w') as f:
            f.write("""LaTeX Flashcards - Compilation Instructions
=============================================

Your flashcards have been generated with beautiful LaTeX formatting!

TO COMPILE THE PDF:
1. Install LaTeX (TeXLive, MiKTeX, or MacTeX)
2. Run: pdflatex filename_flashcards.tex
3. This will generate a PDF with beautifully formatted math

TO USE IN ANKI:
1. Install Anki
2. Go to Tools > Manage Note Types > Add
3. Choose "Basic" and enable LaTeX
4. Import the *_anki.txt file
5. Anki will render LaTeX automatically!

TO USE IN OTHER APPS:
- The JSON and TXT files preserve LaTeX notation ($...$ for inline, $$...$$ for display)
- Most modern flashcard apps support LaTeX rendering
- You can also build custom web interfaces using MathJax or KaTeX

FORMATS PROVIDED:
- .tex  → Full LaTeX document (compile to PDF)
- .json → Machine-readable with LaTeX preserved
- .txt  → Human-readable with LaTeX preserved
- .csv  → Simple import format
- _anki.txt → Anki-specific format with LaTeX
""")
        print(f"📖 Saved README: {readme_path}")
    
    def process_directory(self, directory: str):
        """Process all PDFs in a directory."""
        pdf_files = list(Path(directory).glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory}")
            return
        
        print(f"\n🎯 Found {len(pdf_files)} PDF files to process")
        
        results = []
        for pdf_file in pdf_files:
            result = self.process_pdf(str(pdf_file))
            if result:
                results.append(result)
        
        print(f"\n{'='*60}")
        print(f"✅ COMPLETE! Processed {len(results)} files")
        print(f"📂 Output directory: {self.output_dir}")
        print(f"📐 LaTeX files ready for compilation!")
        print(f"{'='*60}")


# ==================== Main Script ====================

def main():
    """Main execution function."""
    
    print("🚀 AI-Powered Flashcard Generator\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"❌ Configuration Error: {error_msg}")
        print("💡 Please check your .env file or set the required environment variables")
        print("📄 See .env.example for reference")
        return
    
    # Print configuration
    Config.print_config()
    
    # Create necessary directories
    Config.create_directories()
    
    # Initialize AI provider
    print("\n🤖 Initializing Gemini AI provider with LaTeX support...")
    ai_provider = GeminiProvider(api_key=Config.GEMINI_API_KEY, model=Config.GEMINI_MODEL)
    
    # Initialize flashcard generator
    generator = FlashcardGenerator(
        ai_provider=ai_provider,
        output_dir=Config.OUTPUT_DIR
    )
    
    # Process PDFs
    print(f"\n📂 Processing PDFs from: {Config.INPUT_DIR}\n")
    generator.process_directory(Config.INPUT_DIR)
    
    # Print summary
    print("\n✨ Flashcards generated successfully!")
    print(f"\n📂 Output directory: {Config.OUTPUT_DIR}")
    print("\n📐 Generated formats:")
    
    if Config.GENERATE_JSON:
        print("  • .json - Machine-readable with LaTeX preserved")
    if Config.GENERATE_TXT:
        print("  • .txt  - Human-readable with LaTeX preserved")
    if Config.GENERATE_CSV:
        print("  • .csv  - Simple import format")
    if Config.GENERATE_TEX and Config.LATEX_ENABLED:
        print(f"  • .tex  - Compile to PDF: {Config.LATEX_COMPILE_COMMAND} filename.tex")
    if Config.GENERATE_ANKI and Config.ANKI_ENABLED:
        print("  • _anki.txt - Import directly into Anki (LaTeX-enabled)")
    
    print(f"\n💡 Tips:")
    print(f"  • See README_LATEX.txt in {Config.OUTPUT_DIR} for detailed instructions")
    print(f"  • Customize prompts in {Config.PROMPTS_DIR}/ directory")
    print(f"  • Adjust settings in .env file")


if __name__ == "__main__":
    main()