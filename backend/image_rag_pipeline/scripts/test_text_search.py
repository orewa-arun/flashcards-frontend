"""
Quick test script for text-to-text search.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.vector_store import VectorStore
from app.ingestion.embedder import Embedder
from app.retrieval.query import ImageRetriever
from app.utils.config import Config

def test_text_search(course_id: str, query: str, top_k: int = 5):
    """Test text-to-text search."""
    print(f"\n{'='*60}")
    print(f"TEXT-TO-TEXT SEARCH TEST")
    print(f"{'='*60}\n")
    print(f"Course: {course_id}")
    print(f"Query: '{query}'")
    print(f"Top K: {top_k}\n")
    
    # Initialize components
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    
    # Initialize vector store
    if Config.QDRANT_PATH and not Config.QDRANT_PATH.startswith("http"):
        vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        vector_store = VectorStore(path=vector_db_path)
    else:
        vector_store = VectorStore(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
    
    # Initialize embedder
    embedder = Embedder(
        model_name=Config.CLIP_MODEL,
        pretrained=Config.CLIP_PRETRAINED
    )
    
    # Initialize retriever
    retriever = ImageRetriever(vector_store=vector_store, embedder=embedder)
    
    # Perform search
    try:
        results = retriever.query_text_to_text(
            query=query,
            course_id=course_id,
            top_k=top_k
        )
        
        print(f"{'='*60}")
        print(f"RESULTS: Found {len(results['results'])} text chunks")
        print(f"{'='*60}\n")
        
        if results["results"]:
            for i, result in enumerate(results["results"], 1):
                print(f"{i}. Score: {result['score']:.4f}")
                print(f"   PDF: {result['pdf_id']}")
                print(f"   Chunk Index: {result['chunk_index']}")
                print(f"   Text Preview: {result['text'][:200]}...")
                print()
        else:
            print("No results found. Make sure you've ingested PDFs for this course.")
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test text-to-text search")
    parser.add_argument(
        "--course-id",
        type=str,
        default="MS5260",
        help="Course ID to search in"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Text query to search for"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return"
    )
    
    args = parser.parse_args()
    test_text_search(args.course_id, args.query, args.top_k)

