# Hybrid Ingestion Pipeline - Text from Flashcards, Images from PDFs

## Overview

The Image-RAG pipeline now supports **hybrid ingestion** that intelligently separates text and image extraction:

- **Text**: Extracted from curated `*_flashcards_only.json` files
  - ✅ Clean, structured Q&A content
  - ✅ Multiple answer perspectives (concise, analogy, ELI5, real-world, common mistakes)
  - ✅ Context and tags for better retrieval
  - ❌ Excludes `mermaid_diagrams` and `math_visualizations` (noise for text embeddings)

- **Images**: Extracted from PDF lecture slides
  - ✅ Unique images only (de-duplicated by cross-reference)
  - ✅ Associated with page numbers and metadata

## Why Hybrid Ingestion?

### Problem with PDF Text Extraction
- PDFs contain mixed content: text, diagrams, code, mathematical notation
- Extracting raw PDF text leads to noisy embeddings
- Mermaid diagram code and Graphviz syntax pollute text search results

### Solution: Use Curated Flashcards
- Flashcard JSON files contain clean, pedagogically structured content
- Questions and answers are optimized for learning and retrieval
- Diagrams are rendered separately (not embedded in text)

## Architecture

```
Lecture Material
    │
    ├─→ PDF File ──────────→ PDFExtractor (images_only=True) ──→ Image Embeddings
    │                                                              ↓
    └─→ Flashcard JSON ───→ FlashcardJSONExtractor ────────────→ Text Embeddings
                                                                   ↓
                                                            Qdrant Vector DB
                                                         (Same collection, same course_id)
```

## Usage

### Automatic (Batch Ingestion)

The `batch_ingest.py` script automatically detects flashcard JSON files and uses hybrid ingestion:

```bash
cd backend/image_rag_pipeline

# Process a specific course and lecture
python scripts/batch_ingest.py --course-id MS5260 --lecture-number 1

# Process all lectures in a course
python scripts/batch_ingest.py --course-id MS5260

# Process all courses
python scripts/batch_ingest.py
```

**Behavior:**
- If `*_cognitive_flashcards_only.json` exists → Uses **hybrid ingestion**
- If JSON not found → Falls back to **PDF-only ingestion**

### Programmatic (Python API)

```python
from app.ingestion.loader import IngestionPipeline
from app.db.vector_store import VectorStore
from app.ingestion.embedder import Embedder

# Initialize components
vector_store = VectorStore(path="data/embeddings")
embedder = Embedder()
pipeline = IngestionPipeline(
    image_output_dir="data/images",
    vector_store=vector_store,
    embedder=embedder
)

# Hybrid ingestion
result = pipeline.ingest_lecture_hybrid(
    pdf_path="courses_resources/MS5260/lecture_slides/MIS_lec_1-3.pdf",
    json_path="courses/MS5260/cognitive_flashcards/MIS_lec_1-3/MIS_lec_1-3_cognitive_flashcards_only.json",
    course_id="MS5260",
    lecture_metadata={
        "lecture_name": "MIS Lectures 1-3",
        "lecture_number": "1-3"
    }
)

print(f"Ingested {result['flashcard_blocks']} flashcard blocks and {result['images']} images")
```

## New Components

### 1. FlashcardJSONExtractor (`app/ingestion/json_extractor.py`)

Extracts clean text from flashcard JSON files.

**Extracts:**
- Question
- Answer variants (concise, analogy, eli5, real_world_use_case, common_mistakes)
- Example
- Context
- Tags and metadata

**Ignores:**
- `mermaid_diagrams`
- `math_visualizations`
- `mermaid_code`
- `diagram_image_path`

### 2. PDFExtractor (Enhanced)

Added `images_only` mode:

```python
# Extract both text and images (default)
extractor = PDFExtractor(output_dir="data/images")

# Extract only images (hybrid mode)
extractor = PDFExtractor(output_dir="data/images", images_only=True)
```

### 3. IngestionPipeline (Enhanced)

New method: `ingest_lecture_hybrid()`

```python
def ingest_lecture_hybrid(
    self,
    pdf_path: str,      # For images
    json_path: str,     # For text
    course_id: str,
    lecture_metadata: Optional[Dict] = None
) -> Dict:
```

## Flashcard JSON Structure

The pipeline expects flashcard JSON files with this structure:

```json
{
  "metadata": {
    "course_id": "MS5260",
    "course_name": "Management Information Systems",
    "source": "MIS_lec_1-3",
    "total_cards": 20
  },
  "flashcards": [
    {
      "flashcard_id": "MIS_lec_1-3_1",
      "type": "definition",
      "question": "What are Management Information Systems?",
      "answers": {
        "concise": "...",
        "analogy": "...",
        "eli5": "...",
        "real_world_use_case": "...",
        "common_mistakes": "..."
      },
      "example": "...",
      "context": "Core MIS Concepts",
      "tags": ["MIS", "Information Systems"],
      "relevance_score": {"score": 10},
      "mermaid_diagrams": { /* IGNORED */ },
      "math_visualizations": { /* IGNORED */ }
    }
  ]
}
```

## File Locations

The script looks for flashcard JSON files in these locations (in order):

1. `courses/{course_id}/cognitive_flashcards/{lecture_name}/{lecture_name}_cognitive_flashcards_only.json`
2. `backend/courses/{course_id}/cognitive_flashcards/{lecture_name}/{lecture_name}_cognitive_flashcards_only.json`

Example:
- PDF: `courses_resources/MS5260/lecture_slides/MIS_lec_1-3.pdf`
- JSON: `courses/MS5260/cognitive_flashcards/MIS_lec_1-3/MIS_lec_1-3_cognitive_flashcards_only.json`

## Retrieval

Text-to-text search now returns cleaner, more focused results:

```python
# Using the test script
python scripts/test_text_search.py \
    --course-id MS5260 \
    --query "what is competitive advantage" \
    --top-k 5

# Using the API
curl -X POST "http://localhost:8001/search-text/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "competitive advantage", "top_k": 5}'
```

**Results now include:**
- `flashcard_id`: Unique identifier
- `flashcard_type`: definition, concept, comparison, etc.
- `context`: Topic area
- `tags`: Related topics
- `relevance_score`: Pedagogical importance (0-10)

## Benefits

### 1. Better Text Embeddings
- No Mermaid syntax pollution: `graph TD A --> B`
- No Graphviz code: `digraph G { node [fillcolor="..."] }`
- Only natural language Q&A content

### 2. Structured Metadata
- Flashcard type, context, tags
- Relevance scores for filtering
- Multiple answer perspectives

### 3. Optimized Storage
- No duplicate images (de-duplicated by xref)
- No redundant text chunks (flashcards are already chunked)

### 4. Flexible Retrieval
- Filter by flashcard type
- Filter by context/tags
- Sort by relevance score

## Troubleshooting

### "Storage folder already accessed by another instance"

Qdrant local storage doesn't allow concurrent access. Solutions:

1. **Stop other processes:**
   ```bash
   # Find processes
   ps aux | grep "app.api.server"
   
   # Kill them
   pkill -f "app.api.server"
   ```

2. **Use Qdrant server (for concurrent access):**
   ```bash
   # Start Qdrant server
   docker run -p 6333:6333 qdrant/qdrant
   
   # Update .env
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   QDRANT_PATH=
   ```

### "Flashcard JSON not found"

The script will automatically fall back to PDF-only ingestion. Check file locations:

```bash
# List available flashcard files
find courses -name "*_cognitive_flashcards_only.json"
```

### "Document closed" error

This was fixed by saving page count before closing the PDF document. Update to the latest version.

## Performance

Hybrid ingestion is **faster** than PDF-only:

- ✅ No text extraction from PDF (skip OCR)
- ✅ No text chunking (flashcards are pre-chunked)
- ✅ No duplicate image extraction (de-duplicated)

**Typical times (MIS Lecture 1-3):**
- Images: ~10-15 seconds (50-100 unique images)
- Text: ~5-8 seconds (20 flashcard blocks)
- **Total: ~20 seconds** vs ~40 seconds for PDF-only

## Future Enhancements

- [ ] Multi-language support for flashcards
- [ ] Image captioning using VLMs (optional hook)
- [ ] Multi-turn chat context (optional hook)
- [ ] Reranking (optional hook)

