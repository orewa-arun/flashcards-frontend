# PDF Slide Processor

A modular Python package for extracting information from PDF lecture slides using AI Vision.

## Package Structure

```
pdf_slide_processor/
├── __init__.py       # Package initialization
├── main.py           # Main entry point and orchestrator
├── renderer.py       # SlideRenderer class (PDF to images)
├── analyzer.py       # GeminiVisionAnalyzer class (AI analysis)
├── extractor.py      # InformationExtractor class (document creation)
└── utils.py          # Helper functions (load_courses, etc.)
```

## Usage

### Process a specific course:
```bash
python -m pdf_slide_processor.main MS5130
```

### Process all courses:
```bash
python -m pdf_slide_processor.main
```

## Configuration

The package reads course configurations from `courses_resources/courses.json`.

## Output

Generated files are saved to:
- `courses/[COURSE_ID]/slide_images/` - Rendered slide images
- `courses/[COURSE_ID]/slide_analysis/` - Analysis text and JSON files

## Requirements

- PyMuPDF (fitz)
- google-generativeai
- Valid Gemini API key in config.py

