"""
Configuration management for Image-RAG Pipeline.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings."""
    
    # Vector Database
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_PATH = os.getenv("QDRANT_PATH", "data/embeddings")
    
    # OpenCLIP Model
    CLIP_MODEL = os.getenv("CLIP_MODEL", "ViT-B-32")
    CLIP_PRETRAINED = os.getenv("CLIP_PRETRAINED", "laion2b_s34b_b79k")
    
    # Text Chunking
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 400))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8001))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

