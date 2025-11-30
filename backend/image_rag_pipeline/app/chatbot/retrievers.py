"""
LangChain retriever integration for the Image-RAG pipeline.
Wraps our existing ImageRetriever to work with LangChain's ecosystem.

ENHANCED: Now handles both flashcard and consolidated_chunk sources.
"""
import logging
from typing import List, Optional, Any, Union
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from ..retrieval.query import ImageRetriever
from ..db.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CourseTextRetriever(BaseRetriever):
    """
    LangChain-compatible retriever for course text content.
    
    ENHANCED: Now retrieves both:
    - Consolidated semantic chunks (rich narrative content for teaching)
    - Flashcards (specific Q&A pairs for fact retrieval)
    
    Both sources have type="text" and are retrieved together, providing
    the AI tutor with comprehensive context for answering questions.
    """
    
    course_id: str
    vector_store: VectorStore
    embedder: Any  # Accepts both Embedder and APIEmbedder
    top_k: int = 5
    lecture_id: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    def __init__(
        self,
        course_id: str,
        vector_store: VectorStore,
        embedder: Any,  # Accepts both Embedder and APIEmbedder
        top_k: int = 5,
        lecture_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the retriever.
        
        Args:
            course_id: Course identifier
            vector_store: Vector store instance
            embedder: Embedder instance
            top_k: Number of results to retrieve
            lecture_id: Optional lecture ID to filter by
        """
        super().__init__(
            course_id=course_id,
            vector_store=vector_store,
            embedder=embedder,
            top_k=top_k,
            lecture_id=lecture_id,
            **kwargs
        )
        # Store lecture_id separately (not handled by BaseRetriever/Pydantic automatically)
        self.lecture_id = lecture_id
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
        
        Returns both consolidated chunks and flashcards, providing
        the AI tutor with rich narrative context and specific facts.
        
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
            top_k=self.top_k,
            lecture_id=self.lecture_id
        )
        
        # Convert to LangChain Document format
        documents = []
        consolidated_count = 0
        flashcard_count = 0
        
        for result in results.get("results", []):
            # Combine text content and metadata for richer context
            page_content = result.get("text", "")
            
            # Base metadata
            metadata = {
                "score": result.get("score", 0.0),
                "source_id": result.get("pdf_id", result.get("source_id", "unknown")),
                "source_path": result.get("pdf_path", result.get("source_path", "")),
                "chunk_index": result.get("chunk_index", result.get("block_index", 0)),
                "course_id": self.course_id,
            }
            
            # Determine source type and add appropriate metadata
            source = result.get("source", "unknown")
            metadata["source"] = source
            
            if source == "consolidated_chunk":
                # Consolidated chunk metadata
                consolidated_count += 1
                metadata["topics"] = result.get("topics", [])
                metadata["key_concepts"] = result.get("key_concepts", [])
                metadata["educational_value"] = result.get("educational_value", 0.5)
                metadata["has_definitions"] = result.get("has_definitions", False)
                metadata["has_examples"] = result.get("has_examples", False)
                
                # Format topics for display in context
                if metadata["topics"]:
                    metadata["context"] = ", ".join(metadata["topics"][:3])
                    
            elif source == "flashcard" or "flashcard_id" in result:
                # Flashcard metadata
                flashcard_count += 1
                metadata["flashcard_id"] = result.get("flashcard_id", "")
                metadata["flashcard_type"] = result.get("flashcard_type", "")
                metadata["context"] = result.get("context", "")
                metadata["tags"] = result.get("tags", [])
            
            documents.append(
                Document(
                    page_content=page_content,
                    metadata=metadata
                )
            )
        
        logger.info(
            f"Retrieved {len(documents)} documents "
            f"({consolidated_count} consolidated chunks, {flashcard_count} flashcards)"
        )
        return documents
