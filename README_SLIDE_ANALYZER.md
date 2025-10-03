# 🧠 Intelligent Slide Analyzer

## Overview

This tool intelligently extracts information from image-heavy PDF slides using AI vision. Unlike traditional PDF text extractors, this system:

1. **Renders each slide as a high-quality image** (not fragmented pieces)
2. **Uses Gemini Vision API** to understand the content
3. **Extracts structured information** including:
   - All text content (titles, bullet points, labels)
   - Diagrams and visual explanations
   - Definitions and key concepts
   - Examples and formulas
4. **Creates a master document** ready for flashcard generation

## Why This Approach?

Your slides are **image-based**, meaning:
- No selectable text in the PDF
- Lots of diagrams and visual content
- Traditional PDF text extraction returns nothing useful

**Solution:** We treat each slide as an image and use AI vision to "read" and "understand" it.

## How It Works

```
PDF Slides → Render as Images → Gemini Vision Analysis → Master Document → Flashcards
```

### Step 1: Slide Rendering
Each PDF page is rendered as a high-resolution PNG image. This preserves all visual information in context.

### Step 2: AI Vision Analysis
Gemini Vision API analyzes each slide image and extracts:
- **Text transcription**: All visible text on the slide
- **Diagram descriptions**: Detailed explanations of visual elements
- **Structured data**: Concepts, definitions, examples organized for learning

### Step 3: Master Document Creation
All extracted information is compiled into a comprehensive text document that captures the full content of your slides.

### Step 4: Flashcard Generation
The master document can be fed into your existing flashcard generator to create study materials.

## Usage

### Basic Usage

```bash
# Activate your virtual environment
source .venv/bin/activate

# Run the analyzer
python slide_analyzer.py
```

The script will:
1. Find all PDFs in `./slides/`
2. Render each slide as an image
3. Analyze with Gemini Vision
4. Generate master documents and structured JSON

### Output Structure

```
slide_images/
└── PDF_NAME/
    ├── PDF_NAME_slide_001.png
    ├── PDF_NAME_slide_002.png
    └── ...

slide_analysis/
└── PDF_NAME/
    ├── PDF_NAME_master_content.txt       # Ready for flashcard generation
    └── PDF_NAME_structured_analysis.json # Structured data for advanced use
```

## Configuration

Edit your `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash        # or gemini-1.5-pro for better quality
INPUT_DIR=./slides
```

**Model recommendations:**
- `gemini-1.5-flash`: Fast and cost-effective, good for most slides
- `gemini-1.5-pro`: Higher quality analysis, better for complex diagrams

## Next Steps

After running the slide analyzer, you'll have a comprehensive master document. You can:

1. **Generate flashcards** from the master document
2. **Review the structured JSON** for programmatic access
3. **Manually refine** any AI-extracted content if needed

### Integrate with Flashcard Generator

Update your flashcard generation workflow to use the master document:

```python
# Instead of processing the PDF directly
content = open('./slide_analysis/MIS_lec_1-3/MIS_lec_1-3_master_content.txt').read()

# Feed it to your flashcard generator
generator.generate_flashcards(content)
```

## Cost Considerations

- Each slide requires one Gemini Vision API call
- **Gemini 1.5 Flash**: ~$0.00025 per image (very affordable)
- **Gemini 1.5 Pro**: ~$0.0025 per image (10x more expensive)

For a 23-slide deck with Flash: ~$0.006 (less than a cent!)

## Troubleshooting

### "No text extracted"
✓ This is expected! Your slides are image-based. Use this analyzer instead.

### "Rate limit errors"
- Increase `delay_seconds` in `analyze_all_slides()` 
- Default is 0.5 seconds between requests

### "Analysis quality is poor"
- Switch to `gemini-1.5-pro` model for better understanding
- Increase DPI in `render_pdf_to_images()` for higher resolution images

## Advanced Usage

### Analyze a specific PDF

```python
from slide_analyzer import SlideRenderer, GeminiVisionAnalyzer, InformationExtractor

# Render slides
renderer = SlideRenderer(output_dir="./my_slides")
slides = renderer.render_pdf_to_images("path/to/lecture.pdf")

# Analyze with AI
analyzer = GeminiVisionAnalyzer(api_key="your_key", model="gemini-1.5-flash")
analyzed = analyzer.analyze_all_slides(slides)

# Create document
InformationExtractor.create_master_document(analyzed, "output.txt")
```

### Custom Analysis Prompt

Modify `_get_analysis_prompt()` in `GeminiVisionAnalyzer` to customize what information is extracted.

## Architecture

- **SlideRenderer**: Converts PDF pages to images using PyMuPDF
- **GeminiVisionAnalyzer**: Sends images to Gemini Vision and extracts structured information
- **InformationExtractor**: Converts AI analysis into human-readable documents

Clean, modular, and extensible!

