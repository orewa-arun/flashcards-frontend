"""Slide analysis using Gemini Vision API with parallel batching."""

import asyncio
import logging
import json
import time
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.content_generation.llm.client import LLMClient
from app.content_generation.prompts import get_slide_analysis_prompt, get_batch_slide_analysis_prompt

logger = logging.getLogger(__name__)


class SlideAnalyzer:
    """Analyze slide images using Gemini Vision with parallel batching."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        course_context: Dict[str, Any] = None,
        batch_size: int = 5,
        max_concurrency: int = 3,
        batch_delay_ms: int = 500
    ):
        """
        Initialize slide analyzer.
        
        Args:
            llm_client: LLM client (must support vision)
            course_context: Course metadata (name, textbooks, etc.)
            batch_size: Number of slides per batch API call
            max_concurrency: Maximum parallel batch requests
            batch_delay_ms: Delay between batch dispatches in milliseconds
        """
        self.llm_client = llm_client
        self.course_context = course_context or {}
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
        self.batch_delay_ms = batch_delay_ms
    
    def _build_course_context_string(self) -> str:
        """Build formatted course context string for prompts."""
        if not self.course_context:
            return ""
        
        context_parts = []
        
        course_name = self.course_context.get("course_name", "")
        if course_name:
            context_parts.append(f"**Course:** {course_name}")
        
        course_desc = self.course_context.get("course_description", "")
        if course_desc:
            context_parts.append(f"**Course Description:** {course_desc}")
        
        instructor = self.course_context.get("instructor", "")
        if instructor:
            context_parts.append(f"**Instructor:** {instructor}")
        
        textbooks = self.course_context.get("reference_textbooks", [])
        if textbooks:
            textbooks_str = "\n  - ".join(textbooks)
            context_parts.append(f"**Reference Textbooks:**\n  - {textbooks_str}")
        
        if context_parts:
            return (
                "\n**COURSE CONTEXT:**\n" + 
                "\n".join(context_parts) + 
                "\n\nUse this course context to better understand the subject matter and terminology.\n"
            )
        
        return ""
    
    def _parse_response(self, response_text: str) -> Any:
        """Parse LLM response to JSON."""
        try:
            # Remove code fences if present
            if response_text.startswith("```"):
                parts = response_text.split("```")
                if len(parts) >= 2:
                    response_text = parts[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:].strip()
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return None
    
    def _create_error_result(self, slide_number: int, error: str) -> Dict[str, Any]:
        """Create error result for a slide."""
        return {
            "slide_number": slide_number,
            "title": f"Slide {slide_number}",
            "main_text": "",
            "key_concepts": [],
            "diagrams": [],
            "examples": [],
            "definitions": [],
            "formulas": [],
            "notes": "",
            "error": error
        }
    
    # ============ Single Slide Analysis (Fallback) ============
    
    def analyze_slide(self, image_path: str, slide_number: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        Analyze a single slide image with retry logic.
        
        Args:
            image_path: Path to slide image
            slide_number: Slide number
            max_retries: Maximum retry attempts
            
        Returns:
            Dict with extracted information
        """
        logger.info(f"  Analyzing slide {slide_number} (individual)...")
        
        for attempt in range(max_retries):
            try:
                # Load image
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                
                # Get analysis prompt
                prompt = self._build_single_slide_prompt(slide_number)
                
                # Call vision model
                response_text = self.llm_client.generate_with_images(
                    prompt=prompt,
                    images=[image_bytes]
                )
                
                # Parse JSON response
                structured_data = self._parse_response(response_text)
                
                if structured_data:
                    structured_data["slide_number"] = slide_number
                    logger.info(f"  ✓ Analyzed slide {slide_number}")
                    return structured_data
                else:
                    # Return raw text if JSON parsing fails
                    return {
                        "slide_number": slide_number,
                        "title": "Slide Content",
                        "main_text": response_text,
                        "key_concepts": [],
                        "diagrams": [],
                        "examples": [],
                        "definitions": [],
                        "formulas": [],
                        "notes": ""
                    }
                    
            except Exception as e:
                error_str = str(e)
                
                # Check for rate limit error
                if "429" in error_str or "quota" in error_str.lower():
                    retry_delay = self._extract_retry_delay(error_str)
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"  Rate limit hit, waiting {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                
                logger.error(f"  ✗ Error analyzing slide {slide_number}: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        return self._create_error_result(slide_number, "Analysis failed after retries")
    
    def _build_single_slide_prompt(self, slide_number: int) -> str:
        """Build analysis prompt for single slide."""
        context = self._build_course_context_string()
        base_prompt = get_slide_analysis_prompt()
        
        return f"""{context}

You are an expert academic content analyzer. Analyze this lecture slide image and extract ALL information in a structured JSON format.

**Your task:**
1. Read and transcribe ALL visible text (titles, bullet points, labels, captions)
2. Identify and describe ALL diagrams, charts, tables, or visual elements
3. Extract key concepts, definitions, and examples

Slide Number: {slide_number}

**Output Format (strict JSON):**
{{
    "title": "Main title of the slide",
    "main_text": "Complete transcription of all text content",
    "key_concepts": ["Concept 1", "Concept 2"],
    "diagrams": [
        {{
            "type": "flowchart/diagram/chart/table/etc",
            "description": "Detailed description",
            "key_points": ["point 1", "point 2"]
        }}
    ],
    "examples": ["Any examples mentioned"],
    "definitions": [
        {{
            "term": "Term",
            "definition": "Definition"
        }}
    ],
    "formulas": ["LaTeX formulas"],
    "notes": "Additional important information"
}}

Output ONLY valid JSON, no additional text or markdown code blocks.
"""
    
    def _extract_retry_delay(self, error_str: str) -> float:
        """Extract retry delay from error message."""
        match = re.search(r"retry in (\d+\.?\d*)", error_str.lower())
        if match:
            return float(match.group(1)) + 1  # Add 1 second buffer
        return 60  # Default to 60 seconds
    
    # ============ Batch Analysis (Parallel) ============
    
    async def analyze_slides_parallel(
        self,
        image_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple slides using parallel batch processing.
        
        This is the main entry point for efficient slide analysis.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of analysis results (ordered by slide number)
        """
        total_slides = len(image_paths)
        logger.info(f"\n{'='*70}")
        logger.info(f"🤖 Analyzing {total_slides} slides with parallel batching")
        logger.info(f"   Batch size: {self.batch_size} slides per API call")
        logger.info(f"   Max concurrency: {self.max_concurrency} parallel requests")
        
        # Calculate stats
        num_batches = (total_slides + self.batch_size - 1) // self.batch_size
        logger.info(f"   Total batches: {num_batches}")
        logger.info(f"   Estimated API calls: ~{num_batches}")
        logger.info(f"{'='*70}\n")
        
        # Create batches with metadata
        batches = []
        for batch_idx in range(num_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, total_slides)
            
            batch_slides = []
            for i in range(start_idx, end_idx):
                batch_slides.append({
                    "slide_number": i + 1,
                    "path": image_paths[i]
                })
            
            batches.append({
                "batch_idx": batch_idx,
                "slides": batch_slides
            })
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        # Process batches in parallel
        start_time = time.time()
        
        async def process_batch_with_semaphore(batch: Dict) -> List[Dict[str, Any]]:
            async with semaphore:
                # Add delay between batch dispatches
                await asyncio.sleep(self.batch_delay_ms / 1000.0)
                return await self._analyze_batch_async(batch)
        
        tasks = [process_batch_with_semaphore(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and order results
        all_results = []
        for batch_idx, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Batch {batch_idx} failed with exception: {result}")
                # Create error results for this batch
                batch = batches[batch_idx]
                for slide in batch["slides"]:
                    all_results.append(self._create_error_result(
                        slide["slide_number"],
                        str(result)
                    ))
            else:
                all_results.extend(result)
        
        # Sort by slide number
        all_results.sort(key=lambda x: x.get("slide_number", 0))
        
        elapsed = time.time() - start_time
        logger.info(f"\n✅ Analysis complete for {len(all_results)} slides in {elapsed:.1f}s")
        
        # Report errors
        errors = [r for r in all_results if r.get("error")]
        if errors:
            logger.warning(f"⚠️  {len(errors)} slides had errors")
        
        return all_results
    
    async def _analyze_batch_async(
        self,
        batch: Dict[str, Any],
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Analyze a batch of slides asynchronously.
        
        Args:
            batch: Batch containing slides metadata
            max_retries: Maximum retry attempts
            
        Returns:
            List of analysis results for this batch
        """
        batch_idx = batch["batch_idx"]
        slides = batch["slides"]
        slide_numbers = [s["slide_number"] for s in slides]
        
        logger.info(f"📦 Batch {batch_idx + 1}: Processing slides {slide_numbers}")
        
        # Load all images
        images = []
        for slide in slides:
            try:
                with open(slide["path"], 'rb') as f:
                    images.append(f.read())
            except Exception as e:
                logger.error(f"Failed to load image for slide {slide['slide_number']}: {e}")
                return [self._create_error_result(s["slide_number"], f"Image load error: {e}") 
                        for s in slides]
        
        # Build batch prompt
        course_context = self._build_course_context_string()
        prompt = get_batch_slide_analysis_prompt(len(slides), course_context)
        
        # Try batch analysis
        for attempt in range(max_retries):
            try:
                response_text = await self.llm_client.generate_with_images_async(
                    prompt=prompt,
                    images=images
                )
                
                parsed = self._parse_response(response_text)
                
                if parsed and "slides" in parsed:
                    results = parsed["slides"]
                    
                    # Validate we got correct number of results
                    if len(results) == len(slides):
                        # Add slide numbers if missing
                        for i, result in enumerate(results):
                            if "slide_number" not in result:
                                result["slide_number"] = slides[i]["slide_number"]
                        
                        logger.info(f"   ✓ Batch {batch_idx + 1} completed")
                        return results
                    else:
                        logger.warning(
                            f"   ⚠️  Batch {batch_idx + 1}: Expected {len(slides)} results, "
                            f"got {len(results)}. Falling back to individual analysis."
                        )
                        return await self._fallback_individual_async(slides)
                else:
                    logger.warning(f"   ⚠️  Batch {batch_idx + 1}: Invalid response format")
                    return await self._fallback_individual_async(slides)
                    
            except Exception as e:
                error_str = str(e)
                
                # Handle rate limiting
                if "429" in error_str or "quota" in error_str.lower():
                    retry_delay = self._extract_retry_delay(error_str)
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"   ⏳ Batch {batch_idx + 1}: Rate limit, waiting {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        continue
                
                logger.error(f"   ✗ Batch {batch_idx + 1} error: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
        
        # All retries failed, fall back to individual
        logger.warning(f"   ⚠️  Batch {batch_idx + 1}: All retries failed, using individual analysis")
        return await self._fallback_individual_async(slides)
    
    async def _fallback_individual_async(
        self,
        slides: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fallback to individual slide analysis (runs in thread pool).
        
        Args:
            slides: List of slide metadata
            
        Returns:
            List of individual analysis results
        """
        logger.info(f"   ↳ Falling back to individual analysis for {len(slides)} slides...")
        
        results = []
        for slide in slides:
            # Run sync method in thread pool
            result = await asyncio.to_thread(
                self.analyze_slide,
                slide["path"],
                slide["slide_number"]
            )
            results.append(result)
        
        return results
    
    # ============ Legacy Sync Method ============
    
    def analyze_slides(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple slides (legacy synchronous method).
        
        For better performance, use analyze_slides_parallel() instead.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of analysis results
        """
        logger.warning("Using legacy synchronous analysis. Consider using analyze_slides_parallel() for better performance.")
        
        results = []
        
        for idx, image_path in enumerate(image_paths, 1):
            analysis = self.analyze_slide(image_path, idx)
            results.append({
                "slide_number": idx,
                "analysis": analysis
            })
        
        return results
