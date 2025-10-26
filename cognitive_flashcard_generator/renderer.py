"""
Diagram Renderer - Handles Mermaid.js and Graphviz diagram rendering to PNG.
"""

import os
import subprocess
import re


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
    
    @staticmethod
    def check_graphviz() -> bool:
        """Check if Graphviz is installed."""
        try:
            result = subprocess.run(
                ['dot', '-V'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def parse_layout_engine(dot_code: str) -> str:
        """
        Parse the recommended layout engine from DOT code comments.
        
        Args:
            dot_code: The Graphviz DOT code
            
        Returns:
            Layout engine name (dot, neato, fdp, circo, twopi, sfdp) or 'dot' as default
        """
        # Look for layout engine in comments: /* layout=neato */
        match = re.search(r'/\*\s*layout\s*=\s*(\w+)\s*\*/', dot_code, re.IGNORECASE)
        if match:
            engine = match.group(1).lower()
            valid_engines = ['dot', 'neato', 'fdp', 'circo', 'twopi', 'sfdp']
            if engine in valid_engines:
                return engine
        
        # Also check for layout= in the graph definition
        match = re.search(r'layout\s*=\s*(\w+)', dot_code, re.IGNORECASE)
        if match:
            engine = match.group(1).lower()
            valid_engines = ['dot', 'neato', 'fdp', 'circo', 'twopi', 'sfdp']
            if engine in valid_engines:
                return engine
        
        # Default to 'dot' if no engine specified
        return 'dot'
    
    @staticmethod
    def render_graphviz(dot_code: str, output_path: str) -> bool:
        """
        Render a Graphviz DOT diagram to PNG.
        
        Args:
            dot_code: The Graphviz DOT code
            output_path: Path to save the PNG file
            
        Returns:
            True if successful, False otherwise
        """
        if not dot_code.strip():
            return False
        
        # Parse layout engine from the code
        layout_engine = DiagramRenderer.parse_layout_engine(dot_code)
        
        # Create temporary file for DOT code
        temp_dot = output_path.replace('.png', '.dot')
        
        try:
            # Write DOT code to temp file
            with open(temp_dot, 'w', encoding='utf-8') as f:
                f.write(dot_code)
            
            # Render using the appropriate layout engine
            # For neato with fixed positions, use -n2 flag
            if layout_engine == 'neato' and 'pos=' in dot_code:
                result = subprocess.run(
                    [layout_engine, '-n2', '-Tpng', '-o', output_path, temp_dot],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                result = subprocess.run(
                    [layout_engine, '-Tpng', '-o', output_path, temp_dot],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            # Clean up temp file
            if os.path.exists(temp_dot):
                os.remove(temp_dot)
            
            # Check if rendering was successful
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"    ⚠️  Graphviz rendering failed. Engine: {layout_engine}. Error: {error_msg}")
                return False
            
            if not os.path.exists(output_path):
                print(f"    ⚠️  Graphviz rendering failed. Output file not created: {output_path}")
                return False
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            error_type = "Timeout" if isinstance(e, subprocess.TimeoutExpired) else "Graphviz not found"
            print(f"    ⚠️  Graphviz rendering failed. Engine: {layout_engine}. Error: {error_type}")
            # Clean up temp file on error
            if os.path.exists(temp_dot):
                os.remove(temp_dot)
            return False
        except Exception as e:
            print(f"    ⚠️  Graphviz rendering failed. Engine: {layout_engine}. Error: {str(e)}")
            # Clean up temp file on error
            if os.path.exists(temp_dot):
                os.remove(temp_dot)
            return False

