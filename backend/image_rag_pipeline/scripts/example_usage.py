"""
Example usage script demonstrating the Image-RAG pipeline.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.vector_store import VectorStore
from app.ingestion.loader import IngestionPipeline
from app.ingestion.embedder import Embedder
from app.retrieval.query import ImageRetriever
from app.utils.config import Config


def example_single_pdf():
    """Example: Ingest a single PDF and search for images."""
    print("\n" + "="*60)
    print("EXAMPLE: Single PDF Ingestion and Search")
    print("="*60 + "\n")
    
    # Initialize components
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(base_dir, "data")
    
    # Use Config for initialization
    if Config.QDRANT_PATH and not Config.QDRANT_PATH.startswith("http"):
        vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        vector_store = VectorStore(path=vector_db_path)
    else:
        vector_store = VectorStore(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
    
    embedder = Embedder(
        model_name=Config.CLIP_MODEL,
        pretrained=Config.CLIP_PRETRAINED
    )
    
    pipeline = IngestionPipeline(
        image_output_dir=os.path.join(data_dir, "images"),
        vector_store=vector_store,
        embedder=embedder,
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    # Example: Ingest a PDF
    pdf_path = "path/to/your/lecture.pdf"  # Update this path
    course_id = "MS5260"
    
    if os.path.exists(pdf_path):
        print(f"Ingesting PDF: {pdf_path}")
        result = pipeline.ingest_pdf(
            pdf_path=pdf_path,
            course_id=course_id,
            pdf_metadata={
                "lecture_name": "Example Lecture",
                "lecture_number": "1"
            }
        )
        print(f"✓ Ingested {result['total_items']} items")
        print(f"  - Text chunks: {result['text_chunks']}")
        print(f"  - Images: {result['images']}")
    else:
        print(f"⚠ PDF not found: {pdf_path}")
        print("Skipping ingestion, will demonstrate search on existing data")
    
    # Search for images
    print("\n" + "-"*60)
    print("Searching for images...")
    print("-"*60 + "\n")
    
    retriever = ImageRetriever(vector_store=vector_store, embedder=embedder)
    
    queries = [
        "database diagram",
        "entity relationship model",
        "normalization example"
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        try:
            results = retriever.query_text_to_image(
                query=query,
                course_id=course_id,
                top_k=3
            )
            
            if results["results"]:
                print(f"Found {len(results['results'])} results:")
                for i, result in enumerate(results["results"], 1):
                    print(f"  {i}. Score: {result['score']:.3f}")
                    print(f"     Page: {result['page_number']}")
                    print(f"     File: {result['filename']}")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()


def example_text_search():
    """Example: Search for relevant text chunks."""
    print("\n" + "="*60)
    print("EXAMPLE: Text Search")
    print("="*60 + "\n")
    
    # Initialize components
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(base_dir, "data")
    
    # Use Config for initialization
    if Config.QDRANT_PATH and not Config.QDRANT_PATH.startswith("http"):
        vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        vector_store = VectorStore(path=vector_db_path)
    else:
        vector_store = VectorStore(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
    
    embedder = Embedder(
        model_name=Config.CLIP_MODEL,
        pretrained=Config.CLIP_PRETRAINED
    )
    retriever = ImageRetriever(vector_store=vector_store, embedder=embedder)
    
    # Search for text
    query = "What is normalization in databases?"
    course_id = "MS5260"
    
    print(f"Query: '{query}'")
    print(f"Course: {course_id}\n")
    
    try:
        results = retriever.query_text_to_text(
            query=query,
            course_id=course_id,
            top_k=3
        )
        
        if results["results"]:
            print(f"Found {len(results['results'])} results:\n")
            for i, result in enumerate(results["results"], 1):
                print(f"{i}. Score: {result['score']:.3f}")
                print(f"   Text: {result['text'][:200]}...")
                print(f"   Source: {result['pdf_id']}")
                print()
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")


def example_course_comparison():
    """Example: Compare search results across different courses."""
    print("\n" + "="*60)
    print("EXAMPLE: Cross-Course Image Search")
    print("="*60 + "\n")
    
    # Initialize components
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(base_dir, "data")
    
    # Use Config for initialization
    if Config.QDRANT_PATH and not Config.QDRANT_PATH.startswith("http"):
        vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        vector_store = VectorStore(path=vector_db_path)
    else:
        vector_store = VectorStore(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
    
    embedder = Embedder(
        model_name=Config.CLIP_MODEL,
        pretrained=Config.CLIP_PRETRAINED
    )
    retriever = ImageRetriever(vector_store=vector_store, embedder=embedder)
    
    query = "business model diagram"
    courses = ["MS5260", "MS5150"]
    
    print(f"Query: '{query}'")
    print(f"Searching across courses: {', '.join(courses)}\n")
    
    for course_id in courses:
        print(f"Course: {course_id}")
        try:
            results = retriever.query_text_to_image(
                query=query,
                course_id=course_id,
                top_k=2
            )
            
            if results["results"]:
                for i, result in enumerate(results["results"], 1):
                    print(f"  {i}. Score: {result['score']:.3f} - {result['filename']}")
            else:
                print("  No results found")
        except Exception as e:
            print(f"  Error: {e}")
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Example usage of Image-RAG pipeline")
    parser.add_argument(
        "--example",
        type=str,
        choices=["single", "text", "compare", "all"],
        default="all",
        help="Which example to run"
    )
    
    args = parser.parse_args()
    
    if args.example in ["single", "all"]:
        example_single_pdf()
    
    if args.example in ["text", "all"]:
        example_text_search()
    
    if args.example in ["compare", "all"]:
        example_course_comparison()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60 + "\n")

