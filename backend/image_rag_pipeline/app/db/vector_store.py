"""
Vector Store wrapper for Qdrant.
Manages course-specific collections for storing and retrieving embeddings.
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

try:
    from ..utils.config import Config
except ImportError:
    # Fallback if Config not available (e.g., during testing)
    class Config:
        QDRANT_HOST = "localhost"
        QDRANT_PORT = 6333
        QDRANT_PATH = "data/embeddings"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """Wrapper for Qdrant vector database operations."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, path: Optional[str] = None):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host (defaults to Config.QDRANT_HOST)
            port: Qdrant server port (defaults to Config.QDRANT_PORT)
            path: Path for local persistence (defaults to Config.QDRANT_PATH, if None uses host:port)
        """
        # Use Config defaults if not provided
        if path is None:
            path = Config.QDRANT_PATH if Config.QDRANT_PATH else None
        if host is None:
            host = Config.QDRANT_HOST
        if port is None:
            port = Config.QDRANT_PORT
        
        # Prefer local path if provided, otherwise use host/port
        if path and not path.startswith("http"):
            self.client = QdrantClient(path=path)
            logger.info(f"Connected to Qdrant at local path: {path}")
        else:
            self.client = QdrantClient(host=host, port=port)
            logger.info(f"Connected to Qdrant at {host}:{port}")
    
    def create_collection(self, course_id: str, vector_size: int = 512):
        """
        Create a collection for a specific course.
        
        Args:
            course_id: Unique identifier for the course
            vector_size: Dimension of embedding vectors
        """
        collection_name = f"course_{course_id}"
        
        # Check if collection already exists
        collections = self.client.get_collections().collections
        if any(col.name == collection_name for col in collections):
            logger.info(f"Collection {collection_name} already exists")
            return
        
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        logger.info(f"Created collection: {collection_name}")
    
    def insert_embeddings(
        self,
        course_id: str,
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
        ids: List[Any]  # Accept both int and str IDs
    ):
        """
        Insert embeddings with metadata into a course collection.
        
        Args:
            course_id: Course identifier
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries (must include 'type': 'text' or 'image')
            ids: List of unique IDs for each embedding
        """
        collection_name = f"course_{course_id}"
        
        points = [
            PointStruct(
                id=id_val,
                vector=embedding,
                payload=meta
            )
            for id_val, embedding, meta in zip(ids, embeddings, metadata)
        ]
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"Inserted {len(points)} embeddings into {collection_name}")
    
    def search(
        self,
        course_id: str,
        query_vector: List[float],
        filter_type: str = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in a course collection.
        
        Args:
            course_id: Course identifier
            query_vector: Query embedding vector
            filter_type: Filter by 'type' field ('text' or 'image')
            top_k: Number of results to return
            
        Returns:
            List of search results with scores and metadata
        """
        collection_name = f"course_{course_id}"
        
        # Build filter if specified
        query_filter = None
        if filter_type:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value=filter_type)
                    )
                ]
            )
        
        response = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k
        )
        
        results = response.points
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "metadata": result.payload
            }
            for result in results
        ]
    
    def delete_collection(self, course_id: str):
        """Delete a course collection."""
        collection_name = f"course_{course_id}"
        self.client.delete_collection(collection_name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")

