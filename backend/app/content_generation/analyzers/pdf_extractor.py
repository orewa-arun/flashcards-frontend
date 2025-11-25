"""PDF image extraction utilities using PyMuPDF (like existing pdf_slide_processor)."""

import logging
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import os
import io

logger = logging.getLogger(__name__)


class PDFImageExtractor:
    """Extract images from PDF slides using PyMuPDF (no Poppler required)."""
    
    def __init__(self, dpi: int = 200):
        """
        Initialize PDF extractor.
        
        Args:
            dpi: Resolution for image extraction
        """
        self.dpi = dpi
    
    def extract_images(self, pdf_path: str) -> List[str]:
        """
        Extract slides from PDF as images using PyMuPDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of paths to extracted images
        """
        try:
            import fitz  # PyMuPDF
            
            logger.info(f"Extracting images from PDF: {pdf_path}")
            
            # Open PDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Create temp directory for images
            temp_dir = tempfile.mkdtemp(prefix="pdf_slides_")
            image_paths = []
            
            # Render each page as image
            for page_num in range(total_pages):
                page = doc[page_num]
                image_path = os.path.join(temp_dir, f"slide_{page_num + 1:03d}.png")
                
                # Render page as image
                pix = page.get_pixmap(dpi=self.dpi)
                pix.save(image_path)
                image_paths.append(image_path)
                
                logger.debug(f"Rendered slide {page_num + 1}/{total_pages}")
            
            doc.close()
            
            logger.info(f"Extracted {len(image_paths)} slides")
            return image_paths
            
        except ImportError:
            raise ImportError(
                "Please install PyMuPDF: pip install PyMuPDF"
            )
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {str(e)}")
            raise
    
    def extract_from_bytes(self, pdf_bytes: bytes) -> List[str]:
        """
        Extract slides from PDF bytes using PyMuPDF.
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            List of paths to extracted images
        """
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
        
        try:
            return self.extract_images(temp_pdf_path)
        finally:
            # Clean up temp PDF
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)

