"""
LangChain retriever integration for the Image-RAG pipeline.
Wraps our existing ImageRetriever to work with LangChain's ecosystem.
"""
import logging
from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from ..retrieval.query import ImageRetriever
from ..db.vector_store import VectorStore
from ..ingestion.embedder import Embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CourseTextRetriever(BaseRetriever):
    """
    LangChain-compatible retriever for course text content.
    
    This wraps our existing ImageRetriever to make it compatible with
    LangChain's conversational chain components.
    """
    
    course_id: str
    vector_store: VectorStore
    embedder: Embedder
    top_k: int = 5
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    def __init__(
        self,
        course_id: str,
        vector_store: VectorStore,
        embedder: Embedder,
        top_k: int = 5,
        **kwargs
    ):
        """
        Initialize the retriever.
        
        Args:
            course_id: Course identifier
            vector_store: Vector store instance
            embedder: Embedder instance
            top_k: Number of results to retrieve
        """
        super().__init__(
            course_id=course_id,
            vector_store=vector_store,
            embedder=embedder,
            top_k=top_k,
            **kwargs
        )
        # Don't store retriever as attribute (Pydantic v1 doesn't allow it)
        # We'll create it on-the-fly when needed
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """
        Retrieve relevant documents for the query.
        
        Args:
            query: User's question
            run_manager: LangChain callback manager
            
        Returns:
            List of LangChain Document objects
        """
        logger.info(f"Retrieving documents for query: '{query}' in course {self.course_id}")
        
        # Create retriever on-the-fly (avoids Pydantic attribute issues)
        retriever = ImageRetriever(
            vector_store=self.vector_store,
            embedder=self.embedder
        )
        
        results = retriever.query_text_to_text(
            query=query,
            course_id=self.course_id,
            top_k=self.top_k
        )
        
        # Convert to LangChain Document format
        documents = []
        for result in results.get("results", []):
            # Combine text content and metadata for richer context
            page_content = result.get("text", "")
            
            metadata = {
                "score": result.get("score", 0.0),
                "source_id": result.get("pdf_id", result.get("source_id", "unknown")),
                "source_path": result.get("pdf_path", result.get("source_path", "")),
                "chunk_index": result.get("chunk_index", result.get("block_index", 0)),
                "course_id": self.course_id,
            }
            
            # Add flashcard-specific metadata if available
            if "flashcard_id" in result:
                metadata["flashcard_id"] = result["flashcard_id"]
                metadata["flashcard_type"] = result.get("flashcard_type", "")
                metadata["context"] = result.get("context", "")
                metadata["tags"] = result.get("tags", [])
            
            documents.append(
                Document(
                    page_content=page_content,
                    metadata=metadata
                )
            )
        
        logger.info(f"Retrieved {len(documents)} documents")
        return documents

