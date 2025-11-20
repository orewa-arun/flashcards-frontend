# Image-RAG Pipeline - Setup Guide

Quick setup guide to get your Image-RAG pipeline running.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- ~2GB free disk space (for models and data)

## Step 1: Navigate to the Pipeline Directory

```bash
cd backend/image_rag_pipeline
```

## Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will download:
- FastAPI and Uvicorn (API server)
- Qdrant client (vector database)
- PyMuPDF (PDF processing)
- OpenCLIP and PyTorch (~1GB for the model, first time only)
- Other dependencies

## Step 4: Configure Environment Variables

The `.env` file is already created with default values. You can customize it if needed:

```bash
# Edit .env file (optional)
nano .env
# or
vim .env
```

**Default configuration works out of the box!** You only need to edit `.env` if you want to:
- Use a remote Qdrant server instead of local storage
- Change the CLIP model (for better accuracy/speed tradeoff)
- Adjust chunk sizes
- Change API port

## Step 5: Start the API Server

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

The server is now running! 🚀

## Step 6: Test the Server

Open a **new terminal** (keep the server running) and test:

```bash
# Health check
curl http://localhost:8001/health

# Or visit in browser:
# http://localhost:8001/docs (Swagger UI)
# http://localhost:8001/redoc (ReDoc)
```

## Step 7: Ingest Your First PDF

### Option A: Via API (Single PDF)

```bash
curl -X POST "http://localhost:8001/ingest-pdf/MS5260" \
  -F "file=@/path/to/your/lecture.pdf" \
  -F "lecture_name=Introduction to MIS" \
  -F "lecture_number=1"
```

### Option B: Batch Ingest All Courses

```bash
# Make sure you're in backend/image_rag_pipeline directory
python scripts/batch_ingest.py
```

This will process all PDFs from `courses_resources/courses.json`.

## Step 8: Search for Images

```bash
curl -X POST "http://localhost:8001/search-image/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "database ER diagram", "top_k": 5}'
```

## Quick Command Reference

| Task | Command |
|------|---------|
| Start server | `python -m app.api.server` |
| Health check | `curl http://localhost:8001/health` |
| Batch ingest | `python scripts/batch_ingest.py` |
| Run examples | `python scripts/example_usage.py` |
| View API docs | Open `http://localhost:8001/docs` |

## Troubleshooting

### Port Already in Use

If port 8001 is already in use, change it in `.env`:
```env
API_PORT=8002
```

### Out of Memory

If you run out of memory during ingestion:
1. Process PDFs one at a time via API
2. Use a smaller CLIP model (ViT-B-32 is smallest)
3. Reduce batch processing

### Model Download Issues

First run downloads ~1GB model. If it fails:
- Check internet connection
- Ensure sufficient disk space
- Try again (downloads are cached)

### Qdrant Connection Error

If using local storage (default), ensure the directory exists:
```bash
mkdir -p data/embeddings
```

## Next Steps

- Read `README.md` for detailed documentation
- Check `QUICKSTART.md` for more examples
- Explore API docs at `http://localhost:8001/docs`

Happy searching! 🔍

