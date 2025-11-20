# Image-RAG Pipeline - Quick Start Guide

Get up and running with the Image-RAG pipeline in 5 minutes.

## Prerequisites

- Python 3.8+
- 4GB+ RAM (8GB+ recommended)
- ~2GB disk space for models and data

## Step 1: Install Dependencies

```bash
cd backend/image_rag_pipeline
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (API server)
- Qdrant client (vector database)
- PyMuPDF (PDF processing)
- OpenCLIP & PyTorch (embeddings)
- Pillow (image processing)

**Note**: First run will download ~1GB OpenCLIP model.

## Step 2: Start the Server

```bash
python -m app.api.server
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

The server is now ready! 🚀

## Step 3: Test the API

Open another terminal and check if it's working:

```bash
curl http://localhost:8001/health
```

You should get:
```json
{
  "status": "healthy",
  "components": { ... },
  "directories": { ... }
}
```

## Step 4: Ingest Your First PDF

### Option A: Via API (Single PDF)

```bash
curl -X POST "http://localhost:8001/ingest-pdf/MS5260" \
  -F "file=@/path/to/your/lecture.pdf" \
  -F "lecture_name=Introduction to MIS" \
  -F "lecture_number=1"
```

### Option B: Batch Ingest All Courses

```bash
# In backend/image_rag_pipeline directory
python scripts/batch_ingest.py
```

This will process all PDFs from `courses_resources/courses.json`.

**Progress**: You'll see logs like:
```
Processing course: MS5260 - Management Information Systems
  Processing: MIS Lecture 1
  ✓ Success: 47 items (35 chunks, 12 images)
```

## Step 5: Search for Images

Now query the system:

```bash
curl -X POST "http://localhost:8001/search-image/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "database ER diagram", "top_k": 3}'
```

Response:
```json
{
  "query": "database ER diagram",
  "course_id": "MS5260",
  "results": [
    {
      "score": 0.87,
      "image_path": "...",
      "filename": "MIS_lec_4_page5_img1.png",
      "page_number": 5,
      "pdf_id": "MIS_lec_4"
    }
  ]
}
```

## Step 6: View the Retrieved Image

Copy the `filename` from the search result:

```bash
# Open in browser
open http://localhost:8001/images/MIS_lec_4_page5_img1.png

# Or download it
curl http://localhost:8001/images/MIS_lec_4_page5_img1.png -o result.png
```

## Step 7: Explore the API

Visit the interactive documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

Try different queries:
- "business model canvas"
- "value chain diagram"
- "product life cycle stages"
- "pricing strategies"

## Common Use Cases

### 1. Find Diagrams

```bash
curl -X POST "http://localhost:8001/search-image/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "system architecture diagram"}'
```

### 2. Search Text Content

```bash
curl -X POST "http://localhost:8001/search-text/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "what is normalization in databases?"}'
```

### 3. Cross-Course Search

Search the same query across different courses:

```bash
# MIS course
curl -X POST "http://localhost:8001/search-image/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "business strategy"}'

# Strategy & Innovation course
curl -X POST "http://localhost:8001/search-image/MS5150" \
  -H "Content-Type: application/json" \
  -d '{"query": "business strategy"}'
```

## Troubleshooting

### Server won't start

**Error**: `ModuleNotFoundError`
```bash
# Make sure you're in the right directory
cd backend/image_rag_pipeline
pip install -r requirements.txt
```

### Out of memory during ingestion

**Solution**: Process one PDF at a time or reduce batch size

```python
# Edit app/ingestion/embedder.py
# Process images in smaller batches (not implemented by default)
```

### No results found

**Check**:
1. Did the PDF ingest successfully?
2. Is the course_id correct?
3. Try broader queries first

```bash
# Check ingestion logs
# Look for "Ingestion complete: X items"
```

### Model download is slow

**First time only**: OpenCLIP downloads ~1GB model

**Solution**: Be patient or pre-download:
```python
import open_clip
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='laion2b_s34b_b79k'
)
```

## Next Steps

1. **Read full documentation**: See `README.md` for advanced usage
2. **Run examples**: `python scripts/example_usage.py`
3. **Customize**: Edit `.env` for configuration
4. **Integrate**: Use the API in your frontend application

## Quick Reference

| Action | Command |
|--------|---------|
| Start server | `python -m app.api.server` |
| Health check | `curl http://localhost:8001/health` |
| Ingest PDF | `POST /ingest-pdf/{course_id}` |
| Search images | `POST /search-image/{course_id}` |
| Search text | `POST /search-text/{course_id}` |
| Get image | `GET /images/{filename}` |
| Batch ingest | `python scripts/batch_ingest.py` |
| Examples | `python scripts/example_usage.py` |

## Support

- Full documentation: `README.md`
- Implementation details: `../../IMAGE_RAG_IMPLEMENTATION.md`
- API docs: http://localhost:8001/docs

Happy searching! 🔍✨

