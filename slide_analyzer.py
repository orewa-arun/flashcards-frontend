"""
Intelligent Slide Analyzer - Extract information from image-heavy PDF slides using AI Vision.

This module solves the problem of extracting content from slides that have no selectable text.
It renders each slide as a high-quality image and uses Gemini Vision API to:
- Transcribe all visible text
- Describe diagrams and visual elements in detail
- Extract key concepts, definitions, and examples
- Generate structured documents ready for flashcard creation

Usage:
    python slide_analyzer.py

Output:
    - slide_analysis/[PDF_NAME]/[PDF_NAME]_master_content.txt (comprehensive text document)
    - slide_analysis/[PDF_NAME]/[PDF_NAME]_structured_analysis.json (programmatic access)
"""

import os
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any
import fitz  # PyMuPDF

from config import Config


class SlideRenderer:
    """Renders PDF pages as high-quality images for AI analysis."""
    
    def __init__(self, output_dir: str = "./slide_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def render_pdf_to_images(self, pdf_path: str, dpi: int = 200, skip_existing: bool = True) -> List[Dict[str, Any]]:
        """
        Render each page of a PDF as a high-resolution image.
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution (higher = better quality but larger files)
            
        Returns:
            List of dictionaries with slide metadata
        """
        pdf_path = Path(pdf_path)
        pdf_name = pdf_path.stem
        
        print(f"\n{'='*70}")
        print(f"🖼️  Rendering slides: {pdf_path.name}")
        print(f"{'='*70}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"📊 Total slides: {total_pages}")
        
        slides = []
        
        for page_num in range(total_pages):
            page = doc[page_num]
            image_filename = f"{pdf_name}_slide_{page_num + 1:03d}.png"
            image_path = os.path.join(self.output_dir, image_filename)
            
            # Skip if image already exists (efficiency optimization)
            if skip_existing and os.path.exists(image_path):
                slide_info = {
                    'page_number': page_num + 1,
                    'filename': image_filename,
                    'path': image_path,
                    'width': 0,
                    'height': 0
                }
                slides.append(slide_info)
                print(f"  ⏭️  Slide {page_num + 1}/{total_pages} (already exists)")
                continue
            
            # Render page as image
            pix = page.get_pixmap(dpi=dpi)
            pix.save(image_path)
            
            slide_info = {
                'page_number': page_num + 1,
                'filename': image_filename,
                'path': image_path,
                'width': pix.width,
                'height': pix.height
            }
            
            slides.append(slide_info)
            print(f"  ✓ Slide {page_num + 1}/{total_pages} rendered")
        
        doc.close()
        
        print(f"✅ Rendered {len(slides)} slides to {self.output_dir}/")
        return slides


class GeminiVisionAnalyzer:
    """Uses Gemini Vision API to extract information from slide images."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini Vision analyzer.
        
        Args:
            api_key: Gemini API key
            model: Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)
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
    
    def analyze_slide(self, image_path: str, slide_number: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        Analyze a single slide image and extract structured information with retry logic.
        
        Args:
            image_path: Path to the slide image
            slide_number: Slide number (for context)
            max_retries: Maximum number of retry attempts for rate limits
            
        Returns:
            Dictionary with extracted information
        """
        print(f"  🔍 Analyzing slide {slide_number}...", end=" ", flush=True)
        
        # Load the image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Create the analysis prompt
        prompt = self._get_analysis_prompt()
        
        for attempt in range(max_retries):
            try:
                # Send image to Gemini Vision
                response = self.model.generate_content([
                    prompt,
                    {"mime_type": "image/png", "data": image_data}
                ])
                
                result_text = response.text.strip()
                
                # Try to parse as JSON
                try:
                    if result_text.startswith('```'):
                        # Remove code fences
                        parts = result_text.split('```')
                        if len(parts) >= 2:
                            result_text = parts[1]
                            if result_text.startswith('json'):
                                result_text = result_text[4:].strip()
                    
                    structured_data = json.loads(result_text)
                    print("✓")
                    return structured_data
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, return raw text
                    print("⚠️  (raw text)")
                    return {
                        "title": "Slide Content",
                        "main_text": result_text,
                        "key_concepts": [],
                        "diagrams": [],
                        "examples": [],
                        "definitions": []
                    }
            
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "quota" in error_str.lower():
                    # Extract retry delay from error message if available
                    retry_delay = 60  # Default to 60 seconds
                    
                    if "retry in" in error_str.lower():
                        match = re.search(r'retry in (\d+\.?\d*)', error_str.lower())
                        if match:
                            retry_delay = float(match.group(1)) + 1  # Add 1 second buffer
                    
                    if attempt < max_retries - 1:
                        print(f"⏳ Rate limit hit, waiting {retry_delay:.0f}s...", end=" ", flush=True)
                        time.sleep(retry_delay)
                        print("retrying...", end=" ", flush=True)
                        continue
                    else:
                        print(f"❌ Max retries reached")
                        return {
                            "title": f"Slide {slide_number}",
                            "main_text": "",
                            "key_concepts": [],
                            "diagrams": [],
                            "examples": [],
                            "definitions": [],
                            "error": "Rate limit exceeded after retries"
                        }
                else:
                    # Non-rate-limit error
                    print(f"❌ Error: {e}")
                    return {
                        "title": f"Slide {slide_number}",
                        "main_text": "",
                        "key_concepts": [],
                        "diagrams": [],
                        "examples": [],
                        "definitions": [],
                        "error": error_str
                    }
    
    def _get_analysis_prompt(self) -> str:
        """Get the comprehensive prompt for slide analysis."""
        return """You are an expert academic content analyzer. Analyze this lecture slide image and extract ALL information in a structured JSON format.

**Your task:**
1. Read and transcribe ALL visible text (titles, bullet points, labels, captions)
2. Identify and describe ALL diagrams, charts, tables, or visual elements
3. Extract key concepts, definitions, and examples
4. Capture the relationships between concepts shown in the slide

**Output Format (strict JSON):**
{
  "title": "Main title of the slide",
  "main_text": "Complete transcription of all text content on the slide, preserving structure",
  "key_concepts": [
    "Concept 1",
    "Concept 2"
  ],
  "diagrams": [
    {
      "type": "flowchart/diagram/chart/table/etc",
      "description": "Detailed description of what the diagram shows, including all labels and relationships",
      "key_points": ["point 1", "point 2"]
    }
  ],
  "examples": [
    "Any examples mentioned on the slide"
  ],
  "definitions": [
    {
      "term": "Term being defined",
      "definition": "The definition provided"
    }
  ],
  "formulas": [
    "Any mathematical formulas or equations"
  ],
  "notes": "Any additional important information or context"
}

**Important:**
- Be comprehensive - don't miss any text or visual elements
- For diagrams, describe the structure, components, relationships, and flow
- Capture exact wording for definitions and key terms
- If the slide is mostly visual, focus heavily on describing the visual content
- Output ONLY valid JSON, no additional text"""
    
    def analyze_all_slides(self, slides: List[Dict[str, Any]], 
                          delay_seconds: float = 6.5,
                          batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze all slides with intelligent rate limiting.
        
        Args:
            slides: List of slide metadata dictionaries
            delay_seconds: Delay between API calls (default 6.5s for free tier: 10 req/min)
            batch_size: Number of slides to process before a longer pause
            
        Returns:
            List of analyzed slide data
        """
        print(f"\n{'='*70}")
        print(f"🤖 Analyzing {len(slides)} slides with Gemini Vision")
        print(f"   (Rate limit: ~{60/delay_seconds:.1f} requests/min)")
        print(f"{'='*70}")
        
        analyzed_slides = []
        
        for i, slide in enumerate(slides, 1):
            analysis = self.analyze_slide(slide['path'], slide['page_number'])
            
            analyzed_slide = {
                **slide,
                'analysis': analysis
            }
            analyzed_slides.append(analyzed_slide)
            
            # Smart rate limiting
            if i < len(slides):  # Don't wait after the last slide
                # Every batch_size slides, take a longer pause
                if i % batch_size == 0:
                    print(f"  ⏸️  Batch complete ({i}/{len(slides)}), waiting 60s to reset rate limit...")
                    time.sleep(60)
                else:
                    # Regular delay between requests
                    time.sleep(delay_seconds)
        
        print(f"\n✅ Analysis complete for {len(analyzed_slides)} slides")
        
        # Report any errors
        errors = [s for s in analyzed_slides if s['analysis'].get('error')]
        if errors:
            print(f"⚠️  {len(errors)} slides had errors during analysis")
        
        return analyzed_slides


class InformationExtractor:
    """Converts analyzed slides into structured text documents."""
    
    @staticmethod
    def create_master_document(analyzed_slides: List[Dict[str, Any]], 
                               output_path: str) -> str:
        """
        Create a comprehensive text document from analyzed slides.
        
        Args:
            analyzed_slides: List of analyzed slide data
            output_path: Path to save the master document
            
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
        
        for slide in analyzed_slides:
            page_num = slide['page_number']
            analysis = slide.get('analysis', {})
            
            document_lines.append("\n" + "=" * 80)
            document_lines.append(f"SLIDE {page_num}: {analysis.get('title', 'Content')}")
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


def main():
    """Main execution function."""
    
    print("🚀 Intelligent Slide Analyzer with Gemini Vision\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"❌ Configuration Error: {error_msg}")
        return
    
    # Get PDF files
    slides_dir = Config.INPUT_DIR
    pdf_files = list(Path(slides_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {slides_dir}")
        return
    
    print(f"📂 Found {len(pdf_files)} PDF file(s)\n")
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_name = pdf_file.stem
        
        # Create output directories
        slide_images_dir = f"./slide_images/{pdf_name}"
        analysis_output_dir = f"./slide_analysis/{pdf_name}"
        os.makedirs(slide_images_dir, exist_ok=True)
        os.makedirs(analysis_output_dir, exist_ok=True)
        
        try:
            # Step 1: Render slides as images
            renderer = SlideRenderer(output_dir=slide_images_dir)
            slides = renderer.render_pdf_to_images(str(pdf_file))
            
            # Step 2: Analyze slides with Gemini Vision
            analyzer = GeminiVisionAnalyzer(
                api_key=Config.GEMINI_API_KEY,
                model=Config.GEMINI_MODEL
            )
            # Use intelligent rate limiting: 6.5s delay = ~9 req/min (under 10/min limit)
            analyzed_slides = analyzer.analyze_all_slides(slides, delay_seconds=6.5, batch_size=9)
            
            # Step 3: Create master document
            master_doc_path = os.path.join(analysis_output_dir, f"{pdf_name}_master_content.txt")
            master_document = InformationExtractor.create_master_document(
                analyzed_slides, 
                master_doc_path
            )
            
            # Step 4: Save structured JSON
            json_path = os.path.join(analysis_output_dir, f"{pdf_name}_structured_analysis.json")
            InformationExtractor.save_structured_json(analyzed_slides, json_path)
            
            print(f"\n{'='*70}")
            print(f"✅ COMPLETE: {pdf_name}")
            print(f"{'='*70}")
            print(f"📊 Summary:")
            print(f"  • Slides analyzed: {len(analyzed_slides)}")
            print(f"  • Master document: {master_doc_path}")
            print(f"  • Structured data: {json_path}")
            print(f"  • Slide images: {slide_images_dir}/")
            print(f"\n💡 Next step: Use the master document for flashcard generation!")
            
        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

