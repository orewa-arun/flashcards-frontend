"""
Test script for enriched flashcard generation.

This script:
1. Loads lecture data from the database (or uses the saved consolidation output)
2. Builds enriched TopicBriefs
3. Shows what the LLM would receive as context
4. Optionally generates flashcards with the enriched prompt

Usage:
    python test_enriched_flashcards.py [--generate]
    
    --generate: Actually call the LLM to generate flashcards (costs API tokens)
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_consolidation_result(filepath: str) -> Dict[str, Any]:
    """Load consolidation result from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("full_result", data)


def demo_topic_brief_building():
    """Demonstrate how TopicBriefBuilder transforms consolidated content."""
    from app.content_generation.builders.topic_brief_builder import (
        TopicBriefBuilder,
        TopicBrief
    )
    
    # Load the consolidation result from temp folder
    temp_dir = Path(__file__).parent.parent / "temp"
    consolidation_file = temp_dir / "consolidation_lecture_3_Session_3_-_Framework_for_customer_experiencepdf.json"
    
    if not consolidation_file.exists():
        logger.error(f"Consolidation file not found: {consolidation_file}")
        logger.info("Please run test_consolidation_from_db.py first")
        return None
    
    logger.info(f"Loading consolidation result from: {consolidation_file}")
    
    with open(consolidation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    full_result = data.get("full_result", data)
    topics = full_result.get("topics", data.get("topics", []))
    semantic_chunks = full_result.get("semantic_chunks", data.get("semantic_chunks", []))
    
    logger.info(f"Loaded {len(topics)} topics and {len(semantic_chunks)} semantic chunks")
    
    # Build TopicBriefs for each semantic chunk
    builder = TopicBriefBuilder()
    
    briefs = []
    for idx, chunk in enumerate(semantic_chunks, 1):
        brief = builder.build_from_semantic_chunk(
            chunk=chunk,
            all_topics=topics,
            structured_content=None,  # Would come from database
            lecture_title="Session 3 - Framework for customer experience"
        )
        briefs.append(brief)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"TOPIC BRIEF {idx}: {brief.topic_name}")
        logger.info(f"{'='*70}")
        logger.info(f"Educational Value: {brief.educational_value:.2f}")
        logger.info(f"Source Slides: {brief.source_slides}")
        logger.info(f"Definitions: {len(brief.definitions)}")
        logger.info(f"Examples: {len(brief.examples)}")
        logger.info(f"Diagrams: {len(brief.diagrams)}")
        logger.info(f"Key Concepts: {len(brief.key_concepts)}")
        logger.info(f"Academic References: {brief.academic_references}")
        logger.info(f"Relationships: {brief.relationships}")
    
    return briefs


def show_prompt_context(brief):
    """Show what the LLM would receive as context."""
    from app.content_generation.builders.topic_brief_builder import TopicBrief
    
    print("\n" + "="*80)
    print("ENRICHED PROMPT CONTEXT (What the LLM receives)")
    print("="*80 + "\n")
    
    context = brief.to_prompt_context()
    print(context)
    
    print("\n" + "="*80)
    print(f"Context length: {len(context)} characters")
    print("="*80 + "\n")
    
    return context


def save_enriched_context_samples(briefs, output_dir: Path):
    """Save enriched context samples for review."""
    output_dir.mkdir(exist_ok=True)
    
    for idx, brief in enumerate(briefs, 1):
        context = brief.to_prompt_context()
        
        output_file = output_dir / f"enriched_context_chunk_{idx}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# TOPIC BRIEF {idx}: {brief.topic_name}\n")
            f.write(f"# Educational Value: {brief.educational_value:.2f}\n")
            f.write(f"# Definitions: {len(brief.definitions)}\n")
            f.write(f"# Examples: {len(brief.examples)}\n")
            f.write(f"# Diagrams: {len(brief.diagrams)}\n\n")
            f.write(context)
        
        logger.info(f"Saved enriched context to: {output_file}")
    
    return output_dir


async def generate_flashcards_with_enriched_context(brief, course_name: str = "Customer Experience and Branding"):
    """Actually generate flashcards using the enriched context (costs API tokens)."""
    from app.config import settings
    from app.content_generation.llm.client import create_llm_client
    from app.content_generation.prompts import get_enriched_flashcard_prompt
    
    logger.info("Generating flashcards with enriched context...")
    logger.info(f"Model: {settings.MODEL_FLASHCARDS}")
    
    # Determine provider
    model_name = settings.MODEL_FLASHCARDS
    provider = "anthropic"
    if "gpt" in model_name.lower():
        provider = "openai"
    elif "gemini" in model_name.lower():
        provider = "gemini"
    
    # Get API key
    api_key = settings.ANTHROPIC_API_KEY
    if provider == "openai":
        api_key = settings.OPENAI_API_KEY
    elif provider == "gemini":
        api_key = settings.GEMINI_API_KEY
    
    if not api_key:
        logger.error(f"No API key found for provider: {provider}")
        return None
    
    # Create LLM client
    llm_client = create_llm_client(
        provider=provider,
        model=model_name,
        api_key=api_key,
        temperature=0.7,
        max_tokens=8000
    )
    
    # Build prompt
    template = get_enriched_flashcard_prompt()
    enriched_content = brief.to_prompt_context()
    
    prompt = template.replace("{{COURSE_NAME}}", course_name)
    prompt = prompt.replace("{{TEXTBOOK_REFERENCE}}", "Course Materials")
    prompt = prompt.replace("{{CONTENT_PLACEHOLDER}}", enriched_content)
    
    logger.info(f"Prompt length: {len(prompt)} characters")
    
    # Generate
    try:
        response = llm_client.generate(prompt)
        
        # Parse JSON
        if response.startswith("```"):
            parts = response.split("```")
            if len(parts) >= 2:
                response = parts[1]
                if response.startswith("json"):
                    response = response[4:].strip()
        
        flashcards = json.loads(response)
        
        logger.info(f"Generated {len(flashcards)} flashcards")
        
        return flashcards
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {str(e)}")
        return None


def main():
    """Main execution function."""
    generate_mode = "--generate" in sys.argv
    
    print("\n" + "="*80)
    print("ENRICHED FLASHCARD GENERATION TEST")
    print("="*80 + "\n")
    
    # Step 1: Build TopicBriefs
    logger.info("Step 1: Building TopicBriefs from consolidated content...")
    briefs = demo_topic_brief_building()
    
    if not briefs:
        return
    
    # Step 2: Show sample context
    logger.info("\nStep 2: Showing enriched prompt context for first topic...")
    if briefs:
        context = show_prompt_context(briefs[0])
    
    # Step 3: Save all enriched contexts for review
    logger.info("\nStep 3: Saving enriched contexts to temp folder...")
    temp_dir = Path(__file__).parent.parent / "temp"
    output_dir = temp_dir / "enriched_contexts"
    save_enriched_context_samples(briefs, output_dir)
    
    # Step 4: Optionally generate flashcards
    if generate_mode:
        logger.info("\nStep 4: Generating flashcards (API call)...")
        
        if briefs:
            flashcards = asyncio.run(
                generate_flashcards_with_enriched_context(briefs[0])
            )
            
            if flashcards:
                output_file = temp_dir / "enriched_flashcards_sample.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(flashcards, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved generated flashcards to: {output_file}")
    else:
        logger.info("\nStep 4: Skipping flashcard generation (use --generate to enable)")
        logger.info("         This would cost API tokens")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"\nFiles saved to: {temp_dir}")
    print(f"  - enriched_contexts/ folder contains the structured prompts")
    print(f"\nTo generate flashcards, run: python test_enriched_flashcards.py --generate")


if __name__ == "__main__":
    main()

