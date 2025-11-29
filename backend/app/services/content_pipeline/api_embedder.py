"""
API-based embedder using Google Generative AI.

This is a lightweight alternative to the torch-based OpenCLIP embedder,
designed for production environments where torch is too heavy.
"""

import logging
import os
from typing import List, Union, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)


class APIEmbedder:
    """Generate embeddings using Google Generative AI API."""
    
    # Google's text-embedding model produces 768-dimensional vectors
    EMBEDDING_DIM = 768
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Generative AI embedder.
        
        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = "models/text-embedding-004"
        logger.info(f"Initialized Google API embedder with model: {self.model}")
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text using Google's embedding API.
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            List of embedding vectors (768 dimensions each)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        
        # Process in batches to avoid API limits
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                result = genai.embed_content(
                    model=self.model,
                    content=batch,
                    task_type="retrieval_document"
                )
                
                # Result contains 'embedding' for single text or 'embeddings' for batch
                if isinstance(result.get("embedding"), list) and len(batch) == 1:
                    embeddings.append(result["embedding"])
                else:
                    embeddings.extend(result.get("embedding", []))
                    
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i}: {e}")
                # Return zero embeddings for failed batch
                for _ in batch:
                    embeddings.append([0.0] * self.EMBEDDING_DIM)
        
        logger.info(f"Generated embeddings for {len(texts)} text(s)")
        return embeddings
    
    def embed_image(self, image_paths: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for images.
        
        Note: Google's text embedding API doesn't support images directly.
        For image embeddings, we'd need a different approach (e.g., describe the image first).
        For now, this returns zero vectors as a placeholder.
        
        Args:
            image_paths: Single image path or list of image paths
            
        Returns:
            List of zero embedding vectors
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        logger.warning(f"Image embeddings not supported by API embedder. Returning zero vectors for {len(image_paths)} images.")
        return [[0.0] * self.EMBEDDING_DIM for _ in image_paths]
    
    def get_embedding_dim(self) -> int:
        """Get the dimension of embedding vectors."""
        return self.EMBEDDING_DIM

