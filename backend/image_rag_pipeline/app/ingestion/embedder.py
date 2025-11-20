"""
Embedding generation module using OpenCLIP.
Generates embeddings for both text and images.
"""
import logging
import torch
from PIL import Image
import open_clip
from typing import List, Union, Optional

try:
    from ..utils.config import Config
except ImportError:
    # Fallback if Config not available
    class Config:
        CLIP_MODEL = "ViT-B-32"
        CLIP_PRETRAINED = "laion2b_s34b_b79k"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Embedder:
    """Generate embeddings using OpenCLIP model."""
    
    def __init__(self, model_name: Optional[str] = None, pretrained: Optional[str] = None):
        """
        Initialize OpenCLIP model.
        
        Args:
            model_name: CLIP model architecture (defaults to Config.CLIP_MODEL)
            pretrained: Pretrained weights to use (defaults to Config.CLIP_PRETRAINED)
        """
        model_name = model_name or Config.CLIP_MODEL
        pretrained = pretrained or Config.CLIP_PRETRAINED
        logger.info(f"Loading OpenCLIP model: {model_name} ({pretrained})")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Model loaded on device: {self.device}")
    
    def embed_text(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text.
        
        Args:
            texts: Single text string or list of text strings
            
        Returns:
            List of embedding vectors
        """
        if isinstance(texts, str):
            texts = [texts]
        
        with torch.no_grad():
            text_tokens = self.tokenizer(texts).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        embeddings = text_features.cpu().numpy().tolist()
        logger.info(f"Generated embeddings for {len(texts)} text(s)")
        return embeddings
    
    def embed_image(self, image_paths: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for images.
        
        Args:
            image_paths: Single image path or list of image paths
            
        Returns:
            List of embedding vectors
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]
        
        images = []
        for path in image_paths:
            try:
                img = Image.open(path).convert("RGB")
                images.append(self.preprocess(img))
            except Exception as e:
                logger.error(f"Failed to load image {path}: {e}")
                # Create a zero embedding for failed images
                images.append(torch.zeros(3, 224, 224))
        
        with torch.no_grad():
            image_input = torch.stack(images).to(self.device)
            image_features = self.model.encode_image(image_input)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        embeddings = image_features.cpu().numpy().tolist()
        logger.info(f"Generated embeddings for {len(image_paths)} image(s)")
        return embeddings
    
    def get_embedding_dim(self) -> int:
        """Get the dimension of embedding vectors."""
        with torch.no_grad():
            dummy_text = self.tokenizer(["test"]).to(self.device)
            features = self.model.encode_text(dummy_text)
        return features.shape[-1]

