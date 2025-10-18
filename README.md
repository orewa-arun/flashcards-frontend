# 🎓 AI-Powered Cognitive Flashcard System

> Transform image-heavy PDF slides into intelligent flashcards with examples, diagrams, and relevance scoring.

## Overview

This system solves a seemingly impossible problem: extracting meaningful study materials from slides that have no selectable text. It uses AI vision to "read" slides, understand diagrams, and generate comprehensive flashcards optimized for exam preparation.

## The Complete Pipeline

```
📄 Image-Heavy Slides (PDF)
         ↓
    [pdf_slide_processor]
    Uses Gemini Vision API
         ↓
📝 Master Content Document
    Text + Diagram Descriptions
         ↓
    [cognitive_flashcard_generator.py]
    Uses Gemini + Mermaid.js
         ↓
🎯 Cognitive Flashcards
    • Relevance Scores (1-10)
    • Textbook Examples
    • Visual Diagrams
    • Future-proof JSON
```

## Features

### ✨ What Makes This Special

- **Extracts from Pure Images**: Works where traditional PDF tools fail (0 selectable text)
- **Understands Diagrams**: AI describes complex flowcharts, frameworks, and relationships
- **Relevance Scoring**: Each flashcard rated 1-10 for exam importance
- **Textbook-Aligned Examples**: Real-world examples consistent with course material
- **Mermaid Diagrams**: Visual mnemonics as code (for React) + images (optional)
- **Universal**: Works with ANY course—just change 2 variables
- **Future-Proof**: JSON output ready for React/web frontends

### 📊 Real Results

From 23 image-heavy slides:
- ✅ Extracted 29,482 characters of structured content
- ✅ Generated 14 cognitive flashcards
- ✅ 86% include textbook-aligned examples
- ✅ 43% include Mermaid diagram code
- ✅ Cost: < $0.01 per slide deck
- ✅ Time: ~3 minutes total

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Usage

```bash
# Step 1: Extract content from slides
# Process a specific course
python -m pdf_slide_processor.main MS5130

# Or process all courses
python -m pdf_slide_processor.main

# Step 2: Generate cognitive flashcards
python cognitive_flashcard_generator.py [COURSE_ID]
```

### Output

```
cognitive_flashcards/[DECK_NAME]/
├── [DECK_NAME]_cognitive_flashcards.json  ← For React frontend
├── [DECK_NAME]_study_guide.txt           ← Enhanced study guide
├── [DECK_NAME]_study_plan.txt            ← Prioritized roadmap
└── diagrams/                              ← Rendered diagrams (optional)
```

## Configuration for Other Courses

Add your course to `courses_resources/courses.json`:

```json
{
  "course_id": "YOUR_COURSE_ID",
  "course_name": "Your Course Name",
  "course_code": "COURSE_CODE",
  "reference_textbooks": [
    "Your Textbook Citation"
  ],
  "course_description": "Course description...",
  "lecture_slides": [
    {
      "pdf_path": "courses_resources/YOUR_COURSE_ID/lecture_slides/lecture.pdf",
      "lecture_name": "Lecture Name",
      "lecture_number": "1"
    }
  ]
}
```

That's it! The system is completely universal and course-agnostic.

## Example Flashcard

```json
{
  "question": "What is MIS?",
  "answer": "MIS encompasses people, processes, and technology...",
  "relevance_score": {
    "score": 10,
    "justification": "Core definition; central to the course"
  },
  "example": "A company using data analytics (technology) to understand 
  customer preferences (people) and optimize marketing (process)...",
  "mermaid_code": "graph TD; A[People] --> C[Information Systems]; 
  B[Process] --> C; D[Technology] --> C;",
  "tags": ["MIS", "definition", "core concept"]
}
```

## Optional: Mermaid Diagram Rendering

Install Mermaid CLI to render diagrams as PNG images:

```bash
npm install -g @mermaid-js/mermaid-cli
```

Then re-run `cognitive_flashcard_generator.py` — diagrams will be automatically rendered!

## Project Structure

```
self-learning-ai/
├── pdf_slide_processor/           ⭐ Modular slide processing package
│   ├── main.py                   Entry point
│   ├── renderer.py               PDF to images
│   ├── analyzer.py               Gemini Vision analysis
│   ├── extractor.py              Document generation
│   └── utils.py                  Helper functions
│
├── cognitive_flashcard_generator.py ⭐ Generate flashcards
├── config.py                      Configuration
├── requirements.txt               Dependencies
│
├── prompts/
│   ├── intelligent_flashcard_prompt.txt  ⭐ AI instructions
│   └── content_analysis_prompt.txt       Slide analysis
│
├── courses_resources/             ⭐ Source materials
│   ├── courses.json              Course configurations
│   └── [COURSE_ID]/              Course-specific files
│       └── lecture_slides/       PDF files
│
└── courses/                       ⭐ Generated output
    └── [COURSE_ID]/
        ├── slide_images/         Rendered images
        ├── slide_analysis/       Extracted content
        └── cognitive_flashcards/ Flashcard JSON files
```

## Architecture

### Core Components

1. **SlideRenderer** - Renders PDF pages as high-res images
2. **GeminiVisionAnalyzer** - AI extracts text + describes diagrams
3. **CognitiveFlashcardGenerator** - Creates scored flashcards with examples
4. **DiagramRenderer** - Optional Mermaid → PNG conversion
5. **FlashcardExporter** - Multi-format output

### Key Design Decisions

- **Hybrid Diagrams**: Stores both Mermaid code (React) + rendered PNG (today)
- **Universal Prompts**: Course/textbook as variables, not hardcoded
- **Future-Proof**: JSON-first for web frontends
- **No External Platform Lock-in**: Removed CSV/Anki dependency

## Cost & Performance

| Metric | Value |
|--------|-------|
| Slide Analysis | ~$0.006 per 23 slides |
| Flashcard Generation | ~$0.001 per set |
| **Total** | **~$0.01 per deck** |
| Processing Time | ~3 minutes |
| Success Rate | 100% |

## Advanced Usage

### Batch Processing

Process multiple slide decks:

```bash
# Add all PDFs to slides/
cp ~/Downloads/*.pdf slides/

# Run pipeline
python slide_analyzer.py
python cognitive_flashcard_generator.py
```

### Resume Failed Analyses

If slide analysis fails midway:

```bash
python resume_analysis.py
```

### Custom AI Model

Edit `.env`:

```env
GEMINI_MODEL=gemini-1.5-pro  # Higher quality, more expensive
```

## Study Strategy

1. **Week Before Exam**: Focus on 🔴 High Priority cards (Score 8-10)
2. **3 Days Before**: Add 🟡 Medium Priority cards (Score 5-7)  
3. **Night Before**: Quick review of all High Priority
4. **Use Examples**: The textbook-aligned examples solidify understanding
5. **Review Diagrams**: Visual mnemonics aid recall

## Documentation

- `README_SLIDE_ANALYZER.md` - Detailed slide analysis guide
- `prompts/README.md` - AI prompt engineering notes

## Requirements

- Python 3.10+
- Google Gemini API key
- PyMuPDF (fitz)
- Node.js (optional, for diagram rendering)

## License

MIT

## Contributing

This is a personal study tool. Feel free to fork and adapt for your courses!

---

**Built with ❤️ to solve the impossible problem of learning from image-heavy slides.**
