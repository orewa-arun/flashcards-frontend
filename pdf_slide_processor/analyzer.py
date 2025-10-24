"""
Gemini Vision Analyzer - Extracts information from slide images using AI.
"""

import json
import re
import time
from typing import Dict, List, Any, Optional


class GeminiVisionAnalyzer:
    """Uses Gemini Vision API to extract information from slide images."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        course_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Gemini Vision analyzer.

        Args:
            api_key: Gemini API key
            model: Gemini model to use (gemini-1.5-flash or gemini-1.5-pro)
            course_context: Dictionary containing course metadata (name, textbooks, etc.)
        """
        try:
            import google.generativeai as genai

            self.genai = genai
            self.genai.configure(api_key=api_key)
            self.model = self.genai.GenerativeModel(model)
            self.course_context = course_context or {}
        except ImportError:
            raise ImportError(
                "Please install google-generativeai: pip install google-generativeai"
            )

    def analyze_slide(
        self, image_path: str, slide_number: int, max_retries: int = 3
    ) -> Dict[str, Any]:
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
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Create the analysis prompt
        prompt = self._get_analysis_prompt()

        for attempt in range(max_retries):
            try:
                # Send image to Gemini Vision
                response = self.model.generate_content(
                    [prompt, {"mime_type": "image/png", "data": image_data}]
                )

                result_text = response.text.strip()

                # Try to parse as JSON
                try:
                    if result_text.startswith("```"):
                        # Remove code fences
                        parts = result_text.split("```")
                        if len(parts) >= 2:
                            result_text = parts[1]
                            if result_text.startswith("json"):
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
                        "definitions": [],
                    }

            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error (429)
                if "429" in error_str or "quota" in error_str.lower():
                    # Extract retry delay from error message if available
                    retry_delay = 60  # Default to 60 seconds

                    if "retry in" in error_str.lower():
                        match = re.search(r"retry in (\d+\.?\d*)", error_str.lower())
                        if match:
                            retry_delay = (
                                float(match.group(1)) + 1
                            )  # Add 1 second buffer

                    if attempt < max_retries - 1:
                        print(
                            f"⏳ Rate limit hit, waiting {retry_delay:.0f}s...",
                            end=" ",
                            flush=True,
                        )
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
                            "error": "Rate limit exceeded after retries",
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
                        "error": error_str,
                    }

        # Fallback if all retries exhausted (shouldn't reach here normally)
        return {
            "title": f"Slide {slide_number}",
            "main_text": "",
            "key_concepts": [],
            "diagrams": [],
            "examples": [],
            "definitions": [],
            "error": "Analysis failed after all retries",
        }

    def _get_analysis_prompt(self) -> str:
        """Get the comprehensive prompt for slide analysis with course context."""

        # Build course context section
        context_section = ""
        if self.course_context:
            course_name = self.course_context.get("course_name", "")
            textbooks = self.course_context.get("reference_textbooks", [])
            course_desc = self.course_context.get("course_description", "")

            context_parts = []
            if course_name:
                context_parts.append(f"**Course:** {course_name}")
            if course_desc:
                context_parts.append(f"**Course Description:** {course_desc}")
            if textbooks:
                textbooks_str = "\n  - ".join(textbooks)
                context_parts.append(f"**Reference Textbooks:**\n  - {textbooks_str}")

            if context_parts:
                context_section = (
                    "\n\n**COURSE CONTEXT:**\n" + "\n".join(context_parts) + "\n"
                )
                context_section += "\nUse this course context to better understand the subject matter and terminology used in the slide.\n"

        return f"""You are an expert academic content analyzer. Analyze this lecture slide image and extract ALL information in a structured JSON format.
{context_section}
**Your task:**
1. Read and transcribe ALL visible text (titles, bullet points, labels, captions)
2. Identify and describe ALL diagrams, charts, tables, or visual elements
3. Extract key concepts, definitions, and examples
4. Capture the relationships between concepts shown in the slide
5. Use the course context above to interpret domain-specific terminology accurately

**Output Format (strict JSON):**
{{
  "title": "Main title of the slide",
  "main_text": "Complete transcription of all text content on the slide, preserving structure",
  "key_concepts": [
    "Concept 1",
    "Concept 2"
  ],
  "diagrams": [
    {{
      "type": "flowchart/diagram/chart/table/etc",
      "description": "Detailed description of what the diagram shows, including all labels and relationships",
      "key_points": ["point 1", "point 2"]
    }}
  ],
  "examples": [
    "Any examples mentioned on the slide"
  ],
  "definitions": [
    {{
      "term": "Term being defined",
      "definition": "The definition provided"
    }}
  ],
  "formulas": [
    "Any mathematical formulas or equations"
  ],
  "notes": "Any additional important information or context"
}}

**Important:**
- Be comprehensive - don't miss any text or visual elements
- For diagrams, describe the structure, components, relationships, and flow
- Capture exact wording for definitions and key terms
- If the slide is mostly visual, focus heavily on describing the visual content
- Use the course context to properly interpret subject-specific terminology
- Output ONLY valid JSON, no additional text"""

    def analyze_all_slides(
        self,
        slides: List[Dict[str, Any]],
        delay_seconds: float = 6.5,
        batch_size: int = 10,
    ) -> List[Dict[str, Any]]:
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
            analysis = self.analyze_slide(slide["path"], slide["page_number"])

            analyzed_slide = {**slide, "analysis": analysis}
            analyzed_slides.append(analyzed_slide)

            # Smart rate limiting
            if i < len(slides):  # Don't wait after the last slide
                # Every batch_size slides, take a longer pause
                if i % batch_size == 0:
                    print(
                        f"  ⏸️  Batch complete ({i}/{len(slides)}), waiting 60s to reset rate limit..."
                    )
                    time.sleep(60)
                else:
                    # Regular delay between requests
                    time.sleep(delay_seconds)

        print(f"\n✅ Analysis complete for {len(analyzed_slides)} slides")

        # Report any errors
        errors = [s for s in analyzed_slides if s["analysis"].get("error")]
        if errors:
            print(f"⚠️  {len(errors)} slides had errors during analysis")

        return analyzed_slides
