"""
Demo script showing how ContentConsolidator processes slide analyses.

Run this to see how redundant slides are consolidated into topic-based chunks.
"""

import json
from app.content_generation.analyzers.content_consolidator import ContentConsolidator

# Your example data (trimmed for demo)
sample_raw_slide_analyses = [
    {
        "notes": "Title slide for the course...",
        "title": "Customer Experience and Branding",
        "diagrams": [],
        "examples": [],
        "formulas": [],
        "main_text": "Customer Experience and Branding\n\nSession 2: What is Customer Experience ?",
        "definitions": [],
        "key_concepts": ["Customer Experience", "Branding", "Session 2"],
        "slide_number": 1
    },
    {
        "notes": "The slide visually represents a 50/50 balance...",
        "title": "TODAY",
        "diagrams": [
            {"type": "illustration", "key_points": ["Represents idea generation..."], "description": "...lightbulb..."}
        ],
        "examples": [],
        "formulas": [],
        "main_text": "TODAY\n\n50/50",
        "definitions": [],
        "key_concepts": ["Balance in session structure", "Ideation", "Structured communication"],
        "slide_number": 2
    },
    {
        "notes": "The slide presents a comparison between two different checkout flows...",
        "title": "Example of customer experience",
        "diagrams": [
            {
                "type": "comparative screenshots",
                "key_points": [
                    "The 'Control' version is a single-page checkout process.",
                    "The 'Variation 1' version requires users to first choose a checkout method..."
                ],
                "description": "Two screenshots of the Adidas website checkout process..."
            }
        ],
        "examples": [
            "The Adidas online checkout process is used as an example to compare two different user experiences..."
        ],
        "formulas": [],
        "main_text": "adidas\n\nControl\nshipping address...",
        "definitions": [],
        "key_concepts": ["Customer Experience", "Checkout Process", "UI", "UX", "A/B Testing"],
        "slide_number": 11
    },
    {
        "notes": "This is a title slide introducing the philosophical origins...",
        "title": "Origins of the Experience Concept",
        "diagrams": [
            {"type": "image", "key_points": [], "description": "A photograph of a classical marble statue..."}
        ],
        "examples": [],
        "formulas": [],
        "main_text": "• Philosophical approach",
        "definitions": [],
        "key_concepts": ["Experience Concept", "Philosophical approach"],
        "slide_number": 16
    },
    {
        "notes": "This slide defines experience from a philosophical viewpoint...",
        "title": "Origins of the Experience Concept",
        "diagrams": [
            {
                "type": "flowchart",
                "key_points": ["Experience progresses through three forms..."],
                "description": "A horizontal flowchart with three connected chevrons..."
            }
        ],
        "examples": [],
        "formulas": [],
        "main_text": "• Philosophical approach\n\nAccording to the philosophical approach, an experience is an event induced by a stimulus. Therefore, an experience is not self-produced, it is the result of a link between an individual and his or her environment. It produces knowledge and know-how.\n\nBatat (2019) highlights 3 forms of experience in philosophy :",
        "definitions": [
            {
                "term": "Experience (philosophical approach)",
                "definition": "An event induced by a stimulus. It is not self-produced, it is the result of a link between an individual and his or her environment. It produces knowledge and know-how."
            }
        ],
        "key_concepts": ["Philosophical definition of experience", "Stimulus-induced event", "Individual-environment link", "Knowledge and know-how", "Forms of experience (Batat, 2019)"],
        "slide_number": 17
    },
    {
        "notes": "This slide introduces the sociological approach...",
        "title": "Origins of the Experience Concept",
        "diagrams": [
            {"type": "illustration", "key_points": ["Visually represents society..."], "description": "An illustration depicting a large, diverse crowd..."}
        ],
        "examples": [],
        "formulas": [],
        "main_text": "• Sociological approach",
        "definitions": [],
        "key_concepts": ["Experience Concept", "Sociological approach"],
        "slide_number": 21
    },
    {
        "notes": "This slide breaks down the sociological view...",
        "title": "Origins of the Experience Concept",
        "diagrams": [
            {
                "type": "flowchart",
                "key_points": ["Experience is a process...", "The process is cyclical...", "Anchored in sociocultural context."],
                "description": "A horizontal, three-stage process diagram..."
            }
        ],
        "examples": [],
        "formulas": [],
        "main_text": "Sociological approach\n\nWhat the sociological approach brings more to the knowledge of the Experience?\n\nAccording to sociological, we should consider these experiences below ... as anchored to the sociocultural context",
        "definitions": [],
        "key_concepts": ["Sociological approach", "Immediate experience", "Experimentation", "Lived experience", "Sociocultural context"],
        "slide_number": 22
    },
    {
        "notes": "This slide outlines the requirements for project coaching...",
        "title": "Project: Coaching 1",
        "diagrams": [],
        "examples": [],
        "formulas": [],
        "main_text": "• Sit with your group\n• Make sure that you group is up to date on Google Sheet on BlackBoard\n• Be prepared to spend 5/10mn per group with me\n• What I expect from you\n  • App you want to work on...",
        "definitions": [],
        "key_concepts": ["Project coaching", "Group work", "Progress tracking", "Google Sheet", "BlackBoard"],
        "slide_number": 51
    },
    {
        "notes": "Reference: Lemon & Verhoef (2016, p. 71), JM...",
        "title": "From Experience to Customer Experience",
        "diagrams": [
            {
                "type": "timeline",
                "key_points": [
                    "Customer buying behavior process models (1960s–1970s)",
                    "Customer satisfaction and loyalty (1970s)",
                    "Service quality (1980s)",
                    "Relationship marketing (1990s)",
                    "CRM (2000s)",
                    "Customer centricity (2000s–2010s)",
                    "Customer engagement (2010s)"
                ],
                "description": "A horizontal timeline showing the evolution of marketing concepts..."
            }
        ],
        "examples": [],
        "formulas": [],
        "main_text": "• The Roots of Customer Experience In Marketing",
        "definitions": [],
        "key_concepts": ["Customer buying behavior", "Customer satisfaction", "Service quality", "Relationship marketing", "CRM", "Customer centricity", "Customer engagement"],
        "slide_number": 31
    },
    {
        "notes": "The slide compares Traditional Marketing vs Experiential Marketing...",
        "title": "From Experience to Customer Experience",
        "diagrams": [
            {
                "type": "table",
                "key_points": [
                    "Traditional Marketing emphasizes functional benefits...",
                    "Experiential Marketing focuses on customer experiences...",
                    "Clients: rational decision-makers vs rational and emotional actors"
                ],
                "description": "A table comparing 'Traditional Marketing' and 'Experiential Marketing'..."
            }
        ],
        "examples": [],
        "formulas": [],
        "main_text": "• Why do we need to focus on Customer Experience?\n\nElements | Traditional Marketing | Experiential Marketing\n--- | --- | ---\nEmphasis | Focus on functional aspects and benefits | Focus on customer experiences...",
        "definitions": [],
        "key_concepts": ["Traditional Marketing", "Experiential Marketing", "Customer Experience"],
        "slide_number": 46
    }
]


def main():
    print("=" * 70)
    print("CONTENT CONSOLIDATION DEMO")
    print("=" * 70)
    
    # Initialize consolidator
    consolidator = ContentConsolidator(
        topic_similarity_threshold=0.5,
        min_educational_value=0.3,
        consolidate_by_title=True
    )
    
    # Process the slides
    result = consolidator.consolidate(
        raw_slide_analyses=sample_raw_slide_analyses,
        lecture_title="Customer Experience and Branding - Session 2"
    )
    
    # Print summary
    print(f"\n📊 CONSOLIDATION RESULTS:")
    print(f"   Original slides: {result['total_original_slides']}")
    print(f"   Educational slides: {result['educational_slides_count']}")
    print(f"   Filtered (non-educational): {result['filtered_slides_count']}")
    print(f"   Consolidated topics: {result['topic_count']}")
    
    print(f"\n📝 SUMMARY: {result['consolidation_summary']}")
    
    # Show topics
    print("\n\n🎯 CONSOLIDATED TOPICS:")
    print("-" * 70)
    
    for i, topic in enumerate(result['topics'], 1):
        print(f"\n{i}. {topic['name'].upper()}")
        print(f"   Slides: {topic['slides']}")
        print(f"   Educational Value: {topic['educational_value']:.2f}")
        print(f"   Key Concepts: {', '.join(topic['key_concepts'][:5])}")
        if topic['definitions']:
            print(f"   Definitions: {len(topic['definitions'])}")
        if topic['examples']:
            print(f"   Examples: {len(topic['examples'])}")
        if topic['diagrams']:
            print(f"   Diagrams: {len(topic['diagrams'])} (non-decorative)")
    
    # Show semantic chunks
    print("\n\n📦 SEMANTIC CHUNKS (Ready for Flashcard Generation):")
    print("-" * 70)
    
    for i, chunk in enumerate(result['semantic_chunks'], 1):
        topics = chunk['topics']
        content_preview = chunk['content'][:300].replace('\n', ' ')
        print(f"\nChunk {i}:")
        print(f"   Topics: {', '.join(topics)}")
        print(f"   Key Concepts: {', '.join(chunk['key_concepts'][:5])}")
        print(f"   Content Size: {len(chunk['content'])} chars")
        print(f"   Educational Value: {chunk['educational_value']:.2f}")
        print(f"   Preview: {content_preview}...")
    
    # Show what was filtered
    print("\n\n🚫 FILTERING ANALYSIS:")
    print("-" * 70)
    print("Slides with low educational value are filtered based on:")
    print("  - Title slides, logos, accreditation info")
    print("  - Logistics (assignments, schedule, BlackBoard, coaching)")
    print("  - Agenda/overview slides with minimal content")
    print("  - Decorative illustrations without educational content")
    
    # Save full result for inspection
    with open('consolidation_demo_output.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n\n✅ Full result saved to: consolidation_demo_output.json")


if __name__ == "__main__":
    main()

