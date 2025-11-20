"""
PDF extraction module.
Extracts text and images from PDF files using PyMuPDF.
"""
import os
import logging
from typing import Dict, List
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and images from PDF files."""
    
    def __init__(self, output_dir: str, images_only: bool = False):
        """
        Initialize extractor.
        
        Args:
            output_dir: Directory to save extracted images
            images_only: If True, only extract images (skip text extraction)
        """
        self.output_dir = output_dir
        self.images_only = images_only
        os.makedirs(output_dir, exist_ok=True)
    
    def extract(self, pdf_path: str, pdf_id: str = None) -> Dict:
        """
        Extract text and images from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            pdf_id: Unique identifier for the PDF (defaults to filename)
            
        Returns:
            Dictionary containing:
                - text: Full extracted text
                - images: List of image metadata dicts
                - pdf_path: Original PDF path
                - pdf_id: PDF identifier
        """
        if pdf_id is None:
            pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]
        
        logger.info(f"Extracting content from: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        full_text = ""
        images = []
        processed_xrefs = set()  # Keep track of processed image cross-reference numbers

        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text (unless images_only mode)
            if not self.images_only:
                page_text = page.get_text()
                full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            # Extract images
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]

                # If we have already processed this image, skip it
                if xref in processed_xrefs:
                    continue

                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image
                image_filename = f"{pdf_id}_page{page_num + 1}_img{img_index + 1}.{image_ext}"
                image_path = os.path.join(self.output_dir, image_filename)
                
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                images.append({
                    "id": f"{pdf_id}_p{page_num + 1}_i{img_index + 1}",
                    "path": image_path,
                    "page_number": page_num + 1,
                    "filename": image_filename
                })

                # Mark this image as processed
                processed_xrefs.add(xref)

                # Log periodically to avoid spam (every 50 images)
                if len(images) % 50 == 0:
                    logger.debug(f"Extracted {len(images)} unique images so far...")
        
        # Save page count before closing document
        num_pages = len(doc)
        doc.close()
        
        result = {
            "text": full_text,
            "images": images,
            "pdf_path": pdf_path,
            "pdf_id": pdf_id
        }
        
        if self.images_only:
            logger.info(f"Extraction complete (images only): {len(images)} unique images from {num_pages} pages")
        else:
            logger.info(f"Extraction complete: {len(images)} images from {num_pages} pages, {len(full_text)} chars of text")
        
        return result

