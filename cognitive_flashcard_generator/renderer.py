"""
Diagram Renderer - Handles Mermaid.js diagram rendering to PNG.
"""

import os
import subprocess


class DiagramRenderer:
    """Renders Mermaid.js diagrams to PNG images using Mermaid CLI."""
    
    @staticmethod
    def check_mermaid_cli() -> bool:
        """Check if Mermaid CLI is installed."""
        try:
            result = subprocess.run(
                ['mmdc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def render_diagram(mermaid_code: str, output_path: str) -> bool:
        """
        Render a Mermaid diagram to PNG.
        
        Args:
            mermaid_code: The Mermaid.js diagram code
            output_path: Path to save the PNG file
            
        Returns:
            True if successful, False otherwise
        """
        if not mermaid_code.strip():
            return False
        
        # Create temporary file for mermaid code
        temp_mmd = output_path.replace('.png', '.mmd')
        
        try:
            # Write mermaid code to temp file
            with open(temp_mmd, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            
            # Render using mmdc
            result = subprocess.run(
                ['mmdc', '-i', temp_mmd, '-o', output_path, '-b', 'transparent'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up temp file
            if os.path.exists(temp_mmd):
                os.remove(temp_mmd)
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            print(f"    ⚠️  Error rendering diagram: {e}")
            # Clean up temp file on error
            if os.path.exists(temp_mmd):
                os.remove(temp_mmd)
            return False

