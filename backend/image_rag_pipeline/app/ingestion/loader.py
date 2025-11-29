"""
Ingestion orchestrator.
Coordinates the extraction, chunking, embedding, and storage pipeline.

ENHANCED: Added ingest_consolidated_content for semantic chunks from consolidated analysis.
"""
import logging
import os
import hashlib
from typing import Dict, Optional, List, Any
from .extractor import PDFExtractor
from .json_extractor import FlashcardJSONExtractor
from .chunker import TextChunker
from .embedder import Embedder
from ..db.vector_store import VectorStore

from ..utils.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def string_to_int_id(string_id: str) -> int:
    """
    Convert a string ID to an integer ID for Qdrant.
    Uses SHA256 hash and takes first 8 bytes to create a deterministic integer.
    
    Args:
        string_id: String identifier
        
    Returns:
        Integer ID (positive)
    """
    # Use SHA256 to create deterministic hash
    hash_obj = hashlib.sha256(string_id.encode('utf-8'))
    # Take first 8 bytes and convert to int (ensures positive)
    hash_int = int.from_bytes(hash_obj.digest()[:8], byteorder='big')
    # Ensure positive (Qdrant requires positive integers)
    return abs(hash_int)


class IngestionPipeline:
    """Orchestrates the full ingestion pipeline."""
    
    def __init__(
        self,
        image_output_dir: str,
        vector_store: VectorStore,
        embedder: Optional[Embedder] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            image_output_dir: Directory to save extracted images
            vector_store: Vector store instance
            embedder: Embedder instance (created if None)
            chunk_size: Size of text chunks (defaults to Config.CHUNK_SIZE)
            chunk_overlap: Overlap between chunks (defaults to Config.CHUNK_OVERLAP)
        """
        self.pdf_extractor = PDFExtractor(output_dir=image_output_dir)
        self.json_extractor = FlashcardJSONExtractor()
        chunk_size = chunk_size or Config.CHUNK_SIZE
        chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        self.embedder = embedder if embedder else Embedder()
        self.vector_store = vector_store
        self.image_output_dir = image_output_dir
    
    def ingest_pdf(self, pdf_path: str, course_id: str, pdf_metadata: Optional[Dict] = None) -> Dict:
        """
        Run the full ingestion pipeline for a PDF.
        
        Args:
            pdf_path: Path to PDF file
            course_id: Course identifier
            pdf_metadata: Additional metadata about the PDF
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting ingestion for {pdf_path} into course {course_id}")
        
        # Ensure collection exists
        embedding_dim = self.embedder.get_embedding_dim()
        self.vector_store.create_collection(course_id, vector_size=embedding_dim)
        
        # Extract text and images
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]
        extraction_result = self.pdf_extractor.extract(pdf_path, pdf_id=pdf_id)
        
        # Chunk text
        text_chunks = self.chunker.chunk(
            text=extraction_result["text"],
            pdf_id=pdf_id,
            pdf_path=pdf_path
        )
        
        # Embed and store text chunks
        if text_chunks:
            logger.info("Embedding text chunks...")
            text_embeddings = self.embedder.embed_text([chunk["text"] for chunk in text_chunks])
            
            text_metadata = [
                {
                    "type": "text",
                    "pdf_id": chunk["pdf_id"],
                    "pdf_path": chunk["pdf_path"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"][:500],  # Store first 500 chars for preview
                    **(pdf_metadata or {})
                }
                for chunk in text_chunks
            ]
            
            # Convert string IDs to integer IDs for Qdrant
            text_ids = [string_to_int_id(chunk["id"]) for chunk in text_chunks]
            
            self.vector_store.insert_embeddings(
                course_id=course_id,
                embeddings=text_embeddings,
                metadata=text_metadata,
                ids=text_ids
            )
        
        # Embed and store images
        images = extraction_result["images"]
        if images:
            logger.info("Embedding images...")
            image_embeddings = self.embedder.embed_image([img["path"] for img in images])
            
            image_metadata = [
                {
                    "type": "image",
                    "pdf_id": pdf_id,
                    "pdf_path": pdf_path,
                    "page_number": img["page_number"],
                    "image_path": img["path"],
                    "filename": img["filename"],
                    **(pdf_metadata or {})
                }
                for img in images
            ]
            
            # Convert string IDs to integer IDs for Qdrant
            image_ids = [string_to_int_id(img["id"]) for img in images]
            
            self.vector_store.insert_embeddings(
                course_id=course_id,
                embeddings=image_embeddings,
                metadata=image_metadata,
                ids=image_ids
            )
        
        result = {
            "pdf_path": pdf_path,
            "course_id": course_id,
            "text_chunks": len(text_chunks),
            "images": len(images),
            "total_items": len(text_chunks) + len(images)
        }
        
        logger.info(f"Ingestion complete: {result}")
        return result
    
    def ingest_lecture_hybrid(
        self,
        pdf_path: str,
        json_path: str,
        course_id: str,
        lecture_metadata: Optional[Dict] = None,
        skip_images: bool = False
    ) -> Dict:
        """
        Run hybrid ingestion: images from PDF, text from flashcard JSON.
        
        This is the preferred method for ingesting lecture materials when
        flashcard JSON files are available, as it provides cleaner, more
        focused text embeddings by excluding diagram code and math visualizations.
        
        Args:
            pdf_path: Path to PDF file (for images, optional if skip_images=True)
            json_path: Path to flashcard JSON file (for text)
            course_id: Course identifier
            lecture_metadata: Additional metadata about the lecture
            skip_images: If True, skip PDF image extraction
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting hybrid ingestion for {pdf_path} (images) and {json_path} (text) into course {course_id}")
        
        # Ensure collection exists
        embedding_dim = self.embedder.get_embedding_dim()
        self.vector_store.create_collection(course_id, vector_size=embedding_dim)
        
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]
        
        images = []
        # 1. Extract images from PDF (images-only mode)
        if not skip_images and os.path.exists(pdf_path):
            logger.info("Extracting images from PDF...")
            pdf_extractor_images_only = PDFExtractor(
                output_dir=self.image_output_dir,
                images_only=True
            )
            pdf_extraction = pdf_extractor_images_only.extract(pdf_path, pdf_id=pdf_id)
            images = pdf_extraction["images"]
        else:
            logger.info("Skipping image extraction (skip_images=True or PDF not found)")
        
        # 2. Extract text from flashcard JSON
        logger.info("Extracting text from flashcard JSON...")
        json_extraction = self.json_extractor.extract(json_path, source_id=pdf_id)
        text_blocks = json_extraction["text_blocks"]
        
        # 3. Embed and store text blocks (no chunking needed - already well-structured)
        text_count = 0
        if text_blocks:
            logger.info(f"Embedding {len(text_blocks)} flashcard text blocks...")
            
            texts_to_embed = [block["text"] for block in text_blocks]
            text_embeddings = self.embedder.embed_text(texts_to_embed)
            
            text_metadata = [
                {
                    "type": "text",
                    "source": "flashcard",
                    "flashcard_id": block["metadata"]["flashcard_id"],
                    "flashcard_type": block["metadata"]["type"],
                    "context": block["metadata"]["context"],
                    "tags": block["metadata"]["tags"],
                    "relevance_score": block["metadata"]["relevance_score"],
                    "source_id": pdf_id,
                    "source_path": json_path,
                    "text": block["text"][:500],  # Preview
                    **(lecture_metadata or {})
                }
                for block in text_blocks
            ]
            
            # Convert string IDs to integer IDs
            text_ids = [string_to_int_id(block["metadata"]["flashcard_id"]) for block in text_blocks]
            
            self.vector_store.insert_embeddings(
                course_id=course_id,
                embeddings=text_embeddings,
                metadata=text_metadata,
                ids=text_ids
            )
            text_count = len(text_blocks)
        
        # 4. Embed and store images
        image_count = 0
        if images:
            logger.info(f"Embedding {len(images)} images...")
            image_embeddings = self.embedder.embed_image([img["path"] for img in images])
            
            image_metadata = [
                {
                    "type": "image",
                    "source_id": pdf_id,
                    "source_path": pdf_path,
                    "page_number": img["page_number"],
                    "image_path": img["path"],
                    "filename": img["filename"],
                    **(lecture_metadata or {})
                }
                for img in images
            ]
            
            # Convert string IDs to integer IDs
            image_ids = [string_to_int_id(img["id"]) for img in images]
            
            self.vector_store.insert_embeddings(
                course_id=course_id,
                embeddings=image_embeddings,
                metadata=image_metadata,
                ids=image_ids
            )
            image_count = len(images)
        
        result = {
            "pdf_path": pdf_path,
            "json_path": json_path,
            "course_id": course_id,
            "flashcard_blocks": text_count,
            "images": image_count,
            "total_items": text_count + image_count
        }
        
        logger.info(f"Hybrid ingestion complete: {result}")
        return result
    
    def ingest_consolidated_content(
        self,
        consolidated_analysis: Dict[str, Any],
        course_id: str,
        lecture_id: int,
        lecture_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Ingest semantic chunks from consolidated_structured_analysis.
        
        This method embeds the rich, narrative content from the consolidation
        process, which provides better context for the AI tutor than fragmented
        flashcard Q&A pairs.
        
        Args:
            consolidated_analysis: The consolidated_structured_analysis JSON from DB
            course_id: Course identifier (course_code)
            lecture_id: Lecture ID (numeric)
            lecture_metadata: Additional metadata (lecture_title, etc.)
            
        Returns:
            Dictionary with ingestion statistics
        """
        logger.info(f"Starting consolidated content ingestion for lecture {lecture_id} into course {course_id}")
        
        # Ensure collection exists
        embedding_dim = self.embedder.get_embedding_dim()
        self.vector_store.create_collection(course_id, vector_size=embedding_dim)
        
        # Extract semantic chunks
        semantic_chunks = consolidated_analysis.get("semantic_chunks", [])
        topics = consolidated_analysis.get("topics", [])
        
        if not semantic_chunks:
            logger.warning(f"No semantic chunks found in consolidated analysis for lecture {lecture_id}")
            return {
                "course_id": course_id,
                "lecture_id": lecture_id,
                "semantic_chunks": 0,
                "total_items": 0
            }
        
        logger.info(f"Found {len(semantic_chunks)} semantic chunks and {len(topics)} topics")
        
        # Prepare text blocks for embedding
        text_blocks = []
        for i, chunk in enumerate(semantic_chunks):
            # Build a rich text representation of the chunk
            chunk_content = chunk.get("content", "")
            chunk_topics = chunk.get("topics", [])
            chunk_concepts = chunk.get("key_concepts", [])
            
            # Create a unique ID for this chunk
            chunk_id = f"consolidated_{lecture_id}_{i}"
            
            # Check if chunk has definitions or examples (for metadata)
            has_definitions = bool(chunk.get("definitions", []))
            has_examples = bool(chunk.get("examples", []))
            
            text_blocks.append({
                "id": chunk_id,
                "text": chunk_content,
                "topics": chunk_topics,
                "key_concepts": chunk_concepts,
                "educational_value": chunk.get("educational_value", 0.5),
                "has_definitions": has_definitions,
                "has_examples": has_examples,
                "chunk_index": i
            })
        
        # Embed the text blocks
        chunk_count = 0
        if text_blocks:
            logger.info(f"Embedding {len(text_blocks)} consolidated content chunks...")
            
            texts_to_embed = [block["text"] for block in text_blocks]
            text_embeddings = self.embedder.embed_text(texts_to_embed)
            
            # Prepare metadata for each chunk
            text_metadata = [
                {
                    "type": "text",
                    "source": "consolidated_chunk",  # Distinct from "flashcard"
                    "chunk_id": block["id"],
                    "lecture_id": str(lecture_id),
                    "topics": block["topics"],
                    "key_concepts": block["key_concepts"][:10],  # Limit for storage
                    "educational_value": block["educational_value"],
                    "has_definitions": block["has_definitions"],
                    "has_examples": block["has_examples"],
                    "chunk_index": block["chunk_index"],
                    "text": block["text"][:500],  # Preview for debugging
                    **(lecture_metadata or {})
                }
                for block in text_blocks
            ]
            
            # Convert string IDs to integer IDs for Qdrant
            chunk_ids = [string_to_int_id(block["id"]) for block in text_blocks]
            
            self.vector_store.insert_embeddings(
                course_id=course_id,
                embeddings=text_embeddings,
                metadata=text_metadata,
                ids=chunk_ids
            )
            chunk_count = len(text_blocks)
        
        result = {
            "course_id": course_id,
            "lecture_id": lecture_id,
            "semantic_chunks": chunk_count,
            "topics_count": len(topics),
            "total_items": chunk_count
        }
        
        logger.info(f"Consolidated content ingestion complete: {result}")
        return result
    
    def ingest_lecture_full(
        self,
        consolidated_analysis: Dict[str, Any],
        flashcards: Optional[Dict[str, Any]],
        course_id: str,
        lecture_id: int,
        lecture_metadata: Optional[Dict] = None,
        include_flashcards: bool = True
    ) -> Dict:
        """
        Full ingestion: consolidated semantic chunks + optionally flashcards.
        
        This is the recommended method for new lectures, providing both:
        - Rich narrative content (consolidated chunks) for teaching
        - Specific Q&A pairs (flashcards) for precise fact retrieval
        
        Args:
            consolidated_analysis: The consolidated_structured_analysis JSON
            flashcards: The flashcards JSON (optional)
            course_id: Course identifier
            lecture_id: Lecture ID
            lecture_metadata: Additional metadata
            include_flashcards: Whether to also ingest flashcards
            
        Returns:
            Combined ingestion statistics
        """
        logger.info(f"Starting full ingestion for lecture {lecture_id}")
        
        # 1. Ingest consolidated content (primary)
        consolidated_result = self.ingest_consolidated_content(
            consolidated_analysis=consolidated_analysis,
            course_id=course_id,
            lecture_id=lecture_id,
            lecture_metadata=lecture_metadata
        )
        
        flashcard_count = 0
        
        # 2. Optionally ingest flashcards
        if include_flashcards and flashcards:
            flashcard_items = flashcards.get("flashcards", [])
            if flashcard_items:
                logger.info(f"Ingesting {len(flashcard_items)} flashcards...")
                flashcard_count = self._ingest_flashcards_from_dict(
                    flashcards=flashcard_items,
                    course_id=course_id,
                    lecture_id=lecture_id,
                    lecture_metadata=lecture_metadata
                )
        
        result = {
            "course_id": course_id,
            "lecture_id": lecture_id,
            "semantic_chunks": consolidated_result.get("semantic_chunks", 0),
            "flashcards": flashcard_count,
            "total_items": consolidated_result.get("semantic_chunks", 0) + flashcard_count
        }
        
        logger.info(f"Full ingestion complete: {result}")
        return result
    
    def _ingest_flashcards_from_dict(
        self,
        flashcards: List[Dict[str, Any]],
        course_id: str,
        lecture_id: int,
        lecture_metadata: Optional[Dict] = None
    ) -> int:
        """
        Helper to ingest flashcards from a list of flashcard dicts.
        
        Returns the count of ingested flashcards.
        """
        if not flashcards:
            return 0
        
        text_blocks = []
        for fc in flashcards:
            # Build text from question and answers
            question = fc.get("question", "")
            answers = fc.get("answers", {})
            context = fc.get("context", "")
            tags = fc.get("tags", [])
            flashcard_id = fc.get("id", "")
            
            # Combine question with concise answer for embedding
            concise = answers.get("concise", "")
            text = f"Question: {question}\n\nAnswer: {concise}"
            
            if context:
                text = f"[Topic: {context}]\n\n{text}"
            
            text_blocks.append({
                "id": flashcard_id,
                "text": text,
                "context": context,
                "tags": tags,
                "flashcard_type": fc.get("type", "concept")
            })
        
        if not text_blocks:
            return 0
        
        # Embed
        texts_to_embed = [block["text"] for block in text_blocks]
        text_embeddings = self.embedder.embed_text(texts_to_embed)
        
        # Prepare metadata
        text_metadata = [
            {
                "type": "text",
                "source": "flashcard",
                "flashcard_id": block["id"],
                "flashcard_type": block["flashcard_type"],
                "context": block["context"],
                "tags": block["tags"],
                "lecture_id": str(lecture_id),
                "text": block["text"][:500],
                **(lecture_metadata or {})
            }
            for block in text_blocks
        ]
        
        # Insert
        chunk_ids = [string_to_int_id(block["id"]) for block in text_blocks]
        self.vector_store.insert_embeddings(
            course_id=course_id,
            embeddings=text_embeddings,
            metadata=text_metadata,
            ids=chunk_ids
        )
        
        return len(text_blocks)
