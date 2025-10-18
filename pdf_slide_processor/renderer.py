"""
Slide Renderer - Converts PDF pages to high-quality images.
"""

import os
from pathlib import Path
from typing import Dict, List, Any
import fitz  # PyMuPDF


class SlideRenderer:
    """Renders PDF pages as high-quality images for AI analysis."""
    
    def __init__(self, output_dir: str = "./slide_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def render_pdf_to_images(self, pdf_path: str, dpi: int = 200, skip_existing: bool = True) -> List[Dict[str, Any]]:
        """
        Render each page of a PDF as a high-resolution image.
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution (higher = better quality but larger files)
            skip_existing: Skip rendering if image already exists
            
        Returns:
            List of dictionaries with slide metadata
        """
        pdf_path = Path(pdf_path)
        pdf_name = pdf_path.stem
        
        print(f"\n{'='*70}")
        print(f"🖼️  Rendering slides: {pdf_path.name}")
        print(f"{'='*70}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"📊 Total slides: {total_pages}")
        
        slides = []
        
        for page_num in range(total_pages):
            page = doc[page_num]
            image_filename = f"{pdf_name}_slide_{page_num + 1:03d}.png"
            image_path = os.path.join(self.output_dir, image_filename)
            
            # Skip if image already exists (efficiency optimization)
            if skip_existing and os.path.exists(image_path):
                slide_info = {
                    'page_number': page_num + 1,
                    'filename': image_filename,
                    'path': image_path,
                    'width': 0,
                    'height': 0
                }
                slides.append(slide_info)
                print(f"  ⏭️  Slide {page_num + 1}/{total_pages} (already exists)")
                continue
            
            # Render page as image
            pix = page.get_pixmap(dpi=dpi)
            pix.save(image_path)
            
            slide_info = {
                'page_number': page_num + 1,
                'filename': image_filename,
                'path': image_path,
                'width': pix.width,
                'height': pix.height
            }
            
            slides.append(slide_info)
            print(f"  ✓ Slide {page_num + 1}/{total_pages} rendered")
        
        doc.close()
        
        print(f"✅ Rendered {len(slides)} slides to {self.output_dir}/")
        return slides

