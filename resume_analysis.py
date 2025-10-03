"""
Resume Slide Analysis - Continue analyzing slides that failed due to rate limits
"""

import json
from pathlib import Path
from slide_analyzer import SlideRenderer, GeminiVisionAnalyzer, InformationExtractor
from config import Config


def resume_analysis(pdf_name: str):
    """
    Resume analysis for slides that had errors.
    
    Args:
        pdf_name: Name of the PDF (without extension)
    """
    analysis_dir = f"./slide_analysis/{pdf_name}"
    json_path = Path(analysis_dir) / f"{pdf_name}_structured_analysis.json"
    
    if not json_path.exists():
        print(f"❌ No existing analysis found for {pdf_name}")
        return
    
    # Load existing analysis
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    analyzed_slides = data['slides']
    
    # Find slides with errors
    error_slides = [s for s in analyzed_slides if s['analysis'].get('error')]
    
    if not error_slides:
        print(f"✅ All slides already analyzed successfully!")
        return
    
    print(f"\n{'='*70}")
    print(f"🔄 Resuming analysis for {pdf_name}")
    print(f"{'='*70}")
    print(f"Found {len(error_slides)} slides with errors")
    
    # Re-analyze failed slides
    analyzer = GeminiVisionAnalyzer(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL
    )
    
    for slide in error_slides:
        page_num = slide['page_number']
        image_path = slide['path']
        
        print(f"\n  🔄 Re-analyzing slide {page_num}...")
        new_analysis = analyzer.analyze_slide(image_path, page_num)
        
        # Update the analysis
        for s in analyzed_slides:
            if s['page_number'] == page_num:
                s['analysis'] = new_analysis
                break
        
        # Save progress after each slide
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_slides': len(analyzed_slides),
                'slides': analyzed_slides
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved progress")
    
    # Regenerate master document with complete data
    print(f"\n📝 Regenerating master document...")
    master_doc_path = Path(analysis_dir) / f"{pdf_name}_master_content.txt"
    InformationExtractor.create_master_document(analyzed_slides, str(master_doc_path))
    
    print(f"\n{'='*70}")
    print(f"✅ Analysis complete for {pdf_name}")
    print(f"{'='*70}")


if __name__ == "__main__":
    # Resume for MIS_lec_1-3
    resume_analysis("MIS_lec_1-3")

