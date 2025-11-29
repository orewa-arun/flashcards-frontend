"""
Retrieval module for text-to-image search.
"""
import logging
from typing import List, Dict, Optional
from ..db.vector_store import VectorStore
from ..ingestion.embedder import Embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageRetriever:
    """Retrieve images based on text queries."""
    
    def __init__(self, vector_store: VectorStore, embedder: Embedder = None):
        """
        Initialize retriever.
        
        Args:
            vector_store: Vector store instance
            embedder: Embedder instance (created if None)
        """
        self.vector_store = vector_store
        self.embedder = embedder if embedder else Embedder()
    
    def query_text_to_image(
        self,
        query: str,
        course_id: str,
        top_k: int = 5,
        lecture_id: Optional[str] = None
    ) -> Dict:
        """
        Search for images using text query.
        
        Args:
            query: Text query
            course_id: Course identifier
            top_k: Number of results to return
            
        Returns:
            Dictionary with query and results
        """
        logger.info(f"Querying '{query}' in course {course_id}")
        
        # Embed query
        query_embedding = self.embedder.embed_text(query)[0]
        
        # Search for images only
        results = self.vector_store.search(
            course_id=course_id,
            query_vector=query_embedding,
            filter_type="image",
            top_k=top_k,
            lecture_id=lecture_id
        )
        
        # Format results
        formatted_results = [
            {
                "score": result["score"],
                "image_path": result["metadata"].get("image_path"),
                "filename": result["metadata"].get("filename"),
                "page_number": result["metadata"].get("page_number"),
                "pdf_id": result["metadata"].get("pdf_id"),
                "pdf_path": result["metadata"].get("pdf_path")
            }
            for result in results
        ]
        
        logger.info(f"Found {len(formatted_results)} image results")
        
        return {
            "query": query,
            "course_id": course_id,
            "results": formatted_results
        }
    
    def query_text_to_text(
        self,
        query: str,
        course_id: str,
        top_k: int = 5,
        lecture_id: Optional[str] = None
    ) -> Dict:
        """
        Search for text chunks using text query.
        
        Args:
            query: Text query
            course_id: Course identifier
            top_k: Number of results to return
            
        Returns:
            Dictionary with query and results
        """
        logger.info(f"Querying text '{query}' in course {course_id}")
        
        # Embed query
        query_embedding = self.embedder.embed_text(query)[0]
        
        # Search for text only
        results = self.vector_store.search(
            course_id=course_id,
            query_vector=query_embedding,
            filter_type="text",
            top_k=top_k,
            lecture_id=lecture_id
        )
        
        # Format results - include all metadata for richer context
        formatted_results = []
        for result in results:
            meta = result["metadata"]
            formatted_result = {
                "score": result["score"],
                "text": meta.get("text", ""),
                "chunk_index": meta.get("chunk_index"),
                "block_index": meta.get("block_index"),
                "pdf_id": meta.get("pdf_id"),
                "source_id": meta.get("source_id"),
                "pdf_path": meta.get("pdf_path"),
                "source_path": meta.get("source_path"),
                "source": meta.get("source", "unknown"),  # "flashcard" or "consolidated_chunk"
            }
            
            # Add consolidated chunk metadata if available
            if meta.get("source") == "consolidated_chunk":
                formatted_result.update({
                    "topics": meta.get("topics", []),
                    "key_concepts": meta.get("key_concepts", []),
                    "educational_value": meta.get("educational_value", 0.5),
                    "has_definitions": meta.get("has_definitions", False),
                    "has_examples": meta.get("has_examples", False),
                })
            
            # Add flashcard-specific metadata if available
            if "flashcard_id" in meta:
                formatted_result.update({
                    "flashcard_id": meta.get("flashcard_id"),
                    "flashcard_type": meta.get("flashcard_type"),
                    "context": meta.get("context"),
                    "tags": meta.get("tags", []),
                    "relevance_score": meta.get("relevance_score"),
                })
            
            formatted_results.append(formatted_result)
        
        logger.info(f"Found {len(formatted_results)} text results")
        
        return {
            "query": query,
            "course_id": course_id,
            "results": formatted_results
        }

