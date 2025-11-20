"""
Text chunking module.
Splits extracted text into manageable chunks for embedding.
"""
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into chunks with metadata."""
    
    def __init__(self, chunk_size: int = 400, overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, pdf_id: str, pdf_path: str) -> List[Dict]:
        """
        Split text into chunks.
        
        Args:
            text: Full text to chunk
            pdf_id: PDF identifier
            pdf_path: Path to source PDF
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence or word boundary
            if end < len(text) and not text[end].isspace():
                # Look for last period or space
                last_period = chunk_text.rfind('.')
                last_space = chunk_text.rfind(' ')
                break_point = max(last_period, last_space)
                
                if break_point > self.chunk_size // 2:  # Only break if we're past halfway
                    chunk_text = chunk_text[:break_point + 1]
                    end = start + break_point + 1
            
            # Skip empty chunks
            if chunk_text.strip():
                chunks.append({
                    "id": f"{pdf_id}_chunk_{chunk_index}",
                    "text": chunk_text.strip(),
                    "pdf_id": pdf_id,
                    "pdf_path": pdf_path,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
            
            start = end - self.overlap
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

