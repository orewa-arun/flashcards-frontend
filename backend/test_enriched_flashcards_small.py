"""
Small test script for enriched flashcard generation with minimal chunk.

Tests TopicBriefBuilder with a small sample chunk and saves output to temp folder.
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.content_generation.builders.topic_brief_builder import TopicBriefBuilder


def main():
    """Test with a small chunk."""
    print("\n" + "="*80)
    print("SMALL CHUNK TEST - Enriched Flashcard Context")
    print("="*80 + "\n")
    
    # Load consolidation result
    temp_dir = Path(__file__).parent.parent / "temp"
    consolidation_file = temp_dir / "consolidation_lecture_3_Session_3_-_Framework_for_customer_experiencepdf.json"
    
    if not consolidation_file.exists():
        print(f"Error: {consolidation_file} not found")
        return
    
    with open(consolidation_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    full_result = data.get("full_result", data)
    topics = full_result.get("topics", data.get("topics", []))
    semantic_chunks = full_result.get("semantic_chunks", data.get("semantic_chunks", []))
    
    if not semantic_chunks:
        print("No semantic chunks found")
        return
    
    # Use only the FIRST chunk (smallest test)
    chunk = semantic_chunks[0]
    topic_names = chunk.get("topics", [])
    
    print(f"Testing with chunk 1/{len(semantic_chunks)}")
    print(f"Topics: {', '.join(topic_names)}")
    print(f"Content size: {len(chunk.get('content', ''))} characters\n")
    
    # Build TopicBrief
    builder = TopicBriefBuilder()
    brief = builder.build_from_semantic_chunk(
        chunk=chunk,
        all_topics=topics,
        structured_content=None,
        lecture_title="Session 3 - Framework for customer experience"
    )
    
    print(f"TopicBrief created:")
    print(f"  Name: {brief.topic_name}")
    print(f"  Educational Value: {brief.educational_value:.2f}")
    print(f"  Definitions: {len(brief.definitions)}")
    print(f"  Examples: {len(brief.examples)}")
    print(f"  Diagrams: {len(brief.diagrams)}")
    print(f"  Key Concepts: {len(brief.key_concepts)}")
    print(f"  Academic References: {brief.academic_references}")
    print(f"  Relationships: {brief.relationships}\n")
    
    # Generate enriched context
    enriched_context = brief.to_prompt_context()
    
    print(f"Enriched context length: {len(enriched_context)} characters")
    print(f"Preview (first 500 chars):\n{enriched_context[:500]}...\n")
    
    # Save to temp folder
    output_file = temp_dir / "enriched_context_sample.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# TOPIC BRIEF: {brief.topic_name}\n")
        f.write(f"# Educational Value: {brief.educational_value:.2f}\n")
        f.write(f"# Definitions: {len(brief.definitions)}\n")
        f.write(f"# Examples: {len(brief.examples)}\n")
        f.write(f"# Diagrams: {len(brief.diagrams)}\n")
        f.write(f"# Key Concepts: {len(brief.key_concepts)}\n")
        f.write(f"# Academic References: {', '.join(brief.academic_references)}\n\n")
        f.write("="*80 + "\n")
        f.write("ENRICHED PROMPT CONTEXT\n")
        f.write("="*80 + "\n\n")
        f.write(enriched_context)
    
    print(f"✅ Saved enriched context to: {output_file}")
    
    # Also save a JSON summary
    summary = {
        "topic_name": brief.topic_name,
        "educational_value": brief.educational_value,
        "source_slides": brief.source_slides,
        "statistics": {
            "definitions_count": len(brief.definitions),
            "examples_count": len(brief.examples),
            "diagrams_count": len(brief.diagrams),
            "key_concepts_count": len(brief.key_concepts),
            "academic_references": brief.academic_references,
            "relationships": brief.relationships
        },
        "sample_definitions": brief.definitions[:3],
        "sample_examples": brief.examples[:3],
        "sample_key_concepts": brief.key_concepts[:10],
        "context_length": len(enriched_context)
    }
    
    summary_file = temp_dir / "enriched_context_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved summary to: {summary_file}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"\nOutput files in temp folder:")
    print(f"  - enriched_context_sample.txt (full context)")
    print(f"  - enriched_context_summary.json (statistics)")


if __name__ == "__main__":
    main()







