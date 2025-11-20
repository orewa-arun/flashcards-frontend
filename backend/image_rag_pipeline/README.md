# Image-RAG Pipeline

A multimodal retrieval-augmented generation (RAG) pipeline that extracts, embeds, and retrieves both text and images from PDF course materials.

## Features

- **PDF Ingestion**: Extract text and images from PDF files
- **Multimodal Embeddings**: Generate embeddings for both text and images using OpenCLIP
- **Vector Storage**: Store embeddings in Qdrant with course-specific collections
- **Text-to-Image Search**: Query images using natural language
- **Text-to-Text Search**: Find relevant text chunks
- **FastAPI Server**: RESTful API for all operations

## Architecture

```
backend/image_rag_pipeline/
├── app/
│   ├── ingestion/         # PDF extraction, chunking, embedding
│   │   ├── extractor.py   # PyMuPDF-based PDF extraction
│   │   ├── chunker.py     # Text chunking logic
│   │   ├── embedder.py    # OpenCLIP embedding generation
│   │   └── loader.py      # Ingestion orchestrator
│   ├── db/
│   │   └── vector_store.py # Qdrant wrapper
│   ├── retrieval/
│   │   └── query.py       # Search functionality
│   └── api/
│       └── server.py      # FastAPI server
├── data/
│   ├── pdfs/              # Uploaded PDFs
│   ├── images/            # Extracted images
│   └── embeddings/        # Qdrant vector DB
└── requirements.txt
```

## Installation

### 1. Install Dependencies

```bash
cd backend/image_rag_pipeline
pip install -r requirements.txt
```

### 2. Install Qdrant (Optional - for remote server)

If you want to use a remote Qdrant instance instead of local storage:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

For local storage (default), no additional setup needed.

## Usage

### Start the Server

```bash
cd backend/image_rag_pipeline
python -m app.api.server
```

The API will be available at `http://localhost:8001`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

### API Endpoints

#### 1. Health Check

```bash
curl http://localhost:8001/health
```

#### 2. Ingest PDF

Upload a PDF for a specific course:

```bash
curl -X POST "http://localhost:8001/ingest-pdf/MS5260" \
  -F "file=@path/to/lecture.pdf" \
  -F "lecture_name=Introduction to MIS" \
  -F "lecture_number=1"
```

Response:
```json
{
  "success": true,
  "message": "PDF ingested successfully",
  "pdf_path": "...",
  "course_id": "MS5260",
  "text_chunks": 45,
  "images": 12,
  "total_items": 57
}
```

#### 3. Search for Images

Find images using a text query:

```bash
curl -X POST "http://localhost:8001/search-image/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "database ER diagram", "top_k": 5}'
```

Response:
```json
{
  "query": "database ER diagram",
  "course_id": "MS5260",
  "results": [
    {
      "score": 0.87,
      "image_path": "/path/to/image.png",
      "filename": "MS5260_page4_img1.png",
      "page_number": 4,
      "pdf_id": "MIS_lec_4",
      "pdf_path": "/path/to/pdf"
    }
  ]
}
```

#### 4. Search for Text

Find relevant text chunks:

```bash
curl -X POST "http://localhost:8001/search-text/MS5260" \
  -H "Content-Type: application/json" \
  -d '{"query": "normalization forms", "top_k": 3}'
```

#### 5. Get Image

Retrieve a specific image:

```bash
curl http://localhost:8001/images/MS5260_page4_img1.png
```

## Integration with Course Materials

The pipeline is designed to work with your existing `courses_resources/courses.json` file:

```python
import json
from app.ingestion.loader import IngestionPipeline
from app.db.vector_store import VectorStore
from app.ingestion.embedder import Embedder

# Load course configuration
with open("../../courses_resources/courses.json") as f:
    courses = json.load(f)

# Initialize components
vector_store = VectorStore(path="data/embeddings")
embedder = Embedder()
pipeline = IngestionPipeline(
    image_output_dir="data/images",
    vector_store=vector_store,
    embedder=embedder
)

# Ingest all lectures for a course
for course in courses:
    course_id = course["course_id"]
    for lecture in course["lecture_slides"]:
        pdf_path = lecture["pdf_path"]
        metadata = {
            "lecture_name": lecture["lecture_name"],
            "lecture_number": lecture["lecture_number"]
        }
        pipeline.ingest_pdf(pdf_path, course_id, metadata)
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_PATH=data/embeddings  # For local storage

# OpenCLIP Model
CLIP_MODEL=ViT-B-32
CLIP_PRETRAINED=laion2b_s34b_b79k

# Chunking
CHUNK_SIZE=400
CHUNK_OVERLAP=50

# API
API_HOST=0.0.0.0
API_PORT=8001
```

### Vector Store Options

**Local Storage (Default)**:
```python
vector_store = VectorStore(path="data/embeddings")
```

**Remote Server**:
```python
vector_store = VectorStore(host="localhost", port=6333)
```

## Advanced Usage

### Batch Ingestion Script

Create `scripts/batch_ingest.py`:

```python
import json
import os
from app.ingestion.loader import IngestionPipeline
from app.db.vector_store import VectorStore
from app.ingestion.embedder import Embedder

def ingest_all_courses():
    # Initialize
    vector_store = VectorStore(path="data/embeddings")
    embedder = Embedder()
    pipeline = IngestionPipeline(
        image_output_dir="data/images",
        vector_store=vector_store,
        embedder=embedder
    )
    
    # Load courses
    with open("../../courses_resources/courses.json") as f:
        courses = json.load(f)
    
    # Ingest each course
    for course in courses:
        course_id = course["course_id"]
        print(f"Processing course: {course_id}")
        
        for lecture in course["lecture_slides"]:
            pdf_path = lecture["pdf_path"]
            
            # Check if PDF exists
            if not os.path.exists(pdf_path):
                print(f"  Skipping missing PDF: {pdf_path}")
                continue
            
            metadata = {
                "course_name": course["course_name"],
                "lecture_name": lecture["lecture_name"],
                "lecture_number": lecture["lecture_number"]
            }
            
            try:
                result = pipeline.ingest_pdf(pdf_path, course_id, metadata)
                print(f"  ✓ {lecture['lecture_name']}: {result['total_items']} items")
            except Exception as e:
                print(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    ingest_all_courses()
```

### Custom Embedder

Use a different CLIP model:

```python
from app.ingestion.embedder import Embedder

# Use a larger model for better accuracy
embedder = Embedder(
    model_name="ViT-L-14",
    pretrained="laion2b_s32b_b82k"
)
```

## Performance Considerations

- **First run**: Model download takes time (~1GB for ViT-B-32)
- **GPU recommended**: Use CUDA for faster embedding generation
- **Batch processing**: Embed multiple items at once for efficiency
- **Storage**: Each course collection grows with content (typical: 100MB-1GB)

## Troubleshooting

### Out of Memory

Reduce batch size in embedder:

```python
# Process images in smaller batches
for i in range(0, len(images), batch_size):
    batch = images[i:i+batch_size]
    embeddings = embedder.embed_image(batch)
```

### Qdrant Connection Error

Check if Qdrant is running:

```bash
# For local storage, ensure directory exists
ls data/embeddings

# For remote server
curl http://localhost:6333/health
```

### CLIP Model Download Issues

Pre-download models:

```python
import open_clip
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32',
    pretrained='laion2b_s34b_b79k'
)
```

## Next Steps

- [ ] Add reranking with cross-encoder
- [ ] Implement VLM-based image captioning
- [ ] Multi-turn conversational search
- [ ] Hybrid search (text + image queries)
- [ ] Result caching for common queries

## License

Part of the Self-Learning AI project.

