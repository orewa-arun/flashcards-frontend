"""
Diagram Generator - Creates textbook-quality diagrams for quiz explanations.

Supports multiple diagram types:
- Matplotlib: Statistical plots, distributions, regression lines
- Plotly: Interactive visualizations
- PlantUML: Concept maps, architecture diagrams
- Mermaid: (legacy) flowcharts
- Graphviz: Process flows, decision trees
"""

import io
import base64
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Import visualization libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy import stats
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  Matplotlib not available. Install with: pip install matplotlib numpy scipy")

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly not available. Install with: pip install plotly")

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    print("⚠️  Graphviz not available. Install with: pip install graphviz")


class DiagramGenerator:
    """Generate textbook-quality diagrams for quiz explanations."""
    
    def __init__(self):
        self.matplotlib_style = 'seaborn-v0_8-darkgrid'  # Professional style
        if MATPLOTLIB_AVAILABLE:
            try:
                plt.style.use(self.matplotlib_style)
            except:
                plt.style.use('default')
    
    def generate_matplotlib_plot(self, plot_spec: Dict[str, Any]) -> str:
        """
        Generate matplotlib plot and return base64 encoded PNG image.
        
        Args:
            plot_spec: Dictionary with plot type and parameters
            
        Returns:
            Base64 encoded PNG image string
        """
        if not MATPLOTLIB_AVAILABLE:
            return ""
        
        plot_type = plot_spec.get('plot_type', 'unknown')
        params = plot_spec.get('params', {})
        
        try:
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            
            if plot_type == 'normal_distribution':
                self._plot_normal_distribution(ax, params)
            elif plot_type == 'scatter' or plot_type == 'scatter_regression':
                self._plot_scatter(ax, params)
            elif plot_type == 'residual_plot':
                self._plot_residual_plot(ax, params)
            elif plot_type == 'qq_plot':
                self._plot_qq_plot(ax, params)
            elif plot_type == 'box_plot':
                self._plot_box_plot(ax, params)
            elif plot_type == 'confidence_interval':
                self._plot_confidence_interval(ax, params)
            else:
                ax.text(0.5, 0.5, f'Plot type "{plot_type}" not implemented',
                       ha='center', va='center', fontsize=12)
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close(fig)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            
            return f"data:image/png;base64,{image_base64}"
        
        except Exception as e:
            print(f"Error generating matplotlib plot: {e}")
            plt.close('all')
            return ""
    
    def _plot_normal_distribution(self, ax, params: Dict):
        """Plot normal distribution with shaded confidence interval."""
        mean = params.get('mean', 0)
        std = params.get('std', 1)
        confidence_level = params.get('confidence_level', 0.95)
        shade_interval = params.get('shade_interval', None)
        title = params.get('title', 'Normal Distribution')
        xlabel = params.get('xlabel', 'Value')
        annotations = params.get('annotations', [])
        
        # Generate x values
        x_min = mean - 4 * std
        x_max = mean + 4 * std
        x = np.linspace(x_min, x_max, 1000)
        y = stats.norm.pdf(x, mean, std)
        
        # Plot distribution
        ax.plot(x, y, 'b-', linewidth=2, label='Distribution')
        
        # Shade interval if provided
        if shade_interval:
            lower, upper = shade_interval
            x_shade = x[(x >= lower) & (x <= upper)]
            y_shade = stats.norm.pdf(x_shade, mean, std)
            ax.fill_between(x_shade, y_shade, alpha=0.3, color='blue',
                           label=f'{confidence_level*100:.0f}% Confidence Interval')
        
        # Add vertical line at mean
        ax.axvline(mean, color='red', linestyle='--', linewidth=1.5,
                  label=f'Mean = {mean:.3f}')
        
        # Add annotations
        for annot in annotations:
            x_pos = annot.get('x')
            text = annot.get('text', '')
            arrow = annot.get('arrow', False)
            
            if arrow:
                y_pos = stats.norm.pdf(x_pos, mean, std)
                ax.annotate(text, xy=(x_pos, y_pos), xytext=(x_pos, y_pos + 0.1),
                           arrowprops=dict(arrowstyle='->', color='black'),
                           fontsize=10, ha='center')
            else:
                ax.axvline(x_pos, color='gray', linestyle=':', linewidth=1)
                ax.text(x_pos, ax.get_ylim()[1] * 0.9, text,
                       rotation=90, va='top', ha='right', fontsize=9)
        
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel('Probability Density', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
    
    def _plot_scatter(self, ax, params: Dict):
        """Plot scatter plot with optional regression line and annotations."""
        # Get data from params or generate sample data
        x_data = params.get('x_data')
        y_data = params.get('y_data')
        
        if x_data is not None and y_data is not None:
            x = np.array(x_data)
            y = np.array(y_data)
        else:
            # Generate sample data if not provided
            n = params.get('n_points', 50)
            np.random.seed(params.get('seed', 42))
            x = np.random.uniform(0, 10, n)
            y = 2 * x + 1 + np.random.normal(0, 2, n)
        
        # Scatter plot
        ax.scatter(x, y, alpha=0.6, s=50, label='Data Points', color='steelblue')
        
        # Optional regression line
        if params.get('regression_line', False):
            coeffs = np.polyfit(x, y, 1)
            x_line = np.linspace(x.min(), x.max(), 100)
            y_line = coeffs[0] * x_line + coeffs[1]
            ax.plot(x_line, y_line, 'r-', linewidth=2,
                   label=f'y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}')
        
        # Add annotations for specific points
        annotate_points = params.get('annotate_points', [])
        for annot in annotate_points:
            x_pos = annot.get('x')
            y_pos = annot.get('y')
            text = annot.get('text', '')
            
            # Highlight the annotated point
            ax.scatter([x_pos], [y_pos], color='red', s=100, zorder=5, 
                      marker='o', edgecolors='darkred', linewidths=2)
            
            # Add text annotation with arrow
            ax.annotate(text, xy=(x_pos, y_pos), 
                       xytext=(x_pos + (x.max() - x.min()) * 0.1, y_pos + (y.max() - y.min()) * 0.1),
                       arrowprops=dict(arrowstyle='->', color='red', lw=2),
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
        
        ax.set_xlabel(params.get('xlabel', 'X'), fontsize=12)
        ax.set_ylabel(params.get('ylabel', 'Y'), fontsize=12)
        ax.set_title(params.get('title', 'Scatter Plot'),
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
    
    def _plot_residual_plot(self, ax, params: Dict):
        """Plot residuals vs fitted values."""
        # Sample residual plot
        n = params.get('n_points', 50)
        np.random.seed(params.get('seed', 42))
        
        fitted = np.random.uniform(0, 10, n)
        residuals = np.random.normal(0, 1, n)
        
        ax.scatter(fitted, residuals, alpha=0.6, s=50)
        ax.axhline(0, color='red', linestyle='--', linewidth=2)
        
        ax.set_xlabel('Fitted Values', fontsize=12)
        ax.set_ylabel('Residuals', fontsize=12)
        ax.set_title(params.get('title', 'Residual Plot'), fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def _plot_qq_plot(self, ax, params: Dict):
        """Plot Q-Q plot for normality check."""
        n = params.get('n_points', 100)
        np.random.seed(params.get('seed', 42))
        
        # Generate sample data
        data = np.random.normal(0, 1, n)
        
        # Q-Q plot
        stats.probplot(data, dist="norm", plot=ax)
        
        ax.set_title(params.get('title', 'Q-Q Plot'), fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def _plot_box_plot(self, ax, params: Dict):
        """Plot box plot for outlier detection."""
        data = params.get('data', [np.random.normal(0, 1, 100)])
        labels = params.get('labels', ['Data'])
        
        ax.boxplot(data, labels=labels)
        ax.set_ylabel(params.get('ylabel', 'Value'), fontsize=12)
        ax.set_title(params.get('title', 'Box Plot'), fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_confidence_interval(self, ax, params: Dict):
        """Plot confidence interval visualization."""
        point_estimate = params.get('point_estimate', 0)
        lower = params.get('lower', -1)
        upper = params.get('upper', 1)
        
        # Draw number line
        ax.plot([lower, upper], [0, 0], 'b-', linewidth=3, label='Confidence Interval')
        ax.plot([point_estimate], [0], 'ro', markersize=12, label='Point Estimate')
        
        # Add error bars
        ax.errorbar([point_estimate], [0], xerr=[[point_estimate - lower], [upper - point_estimate]],
                   fmt='none', ecolor='blue', capsize=10, capthick=2)
        
        # Annotations
        ax.text(lower, -0.1, f'{lower:.3f}', ha='center', va='top', fontsize=10)
        ax.text(upper, -0.1, f'{upper:.3f}', ha='center', va='top', fontsize=10)
        ax.text(point_estimate, 0.1, f'{point_estimate:.3f}', ha='center', va='bottom', fontsize=10)
        
        ax.set_xlim(lower - 0.5, upper + 0.5)
        ax.set_ylim(-0.3, 0.3)
        ax.set_xlabel(params.get('xlabel', 'Value'), fontsize=12)
        ax.set_title(params.get('title', 'Confidence Interval'), fontsize=14, fontweight='bold')
        ax.set_yticks([])
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='x')
    
    def generate_plotly_plot(self, plot_spec: Dict[str, Any]) -> Dict:
        """
        Generate Plotly plot and return JSON spec for client-side rendering.
        
        Args:
            plot_spec: Dictionary with plot type and parameters
            
        Returns:
            Dictionary with Plotly data and layout
        """
        if not PLOTLY_AVAILABLE:
            return {}
        
        plot_type = plot_spec.get('plot_type', 'unknown')
        params = plot_spec.get('params', {})
        
        try:
            if plot_type == 'interactive_normal':
                return self._plotly_interactive_normal(params)
            elif plot_type == '3d_surface':
                return self._plotly_3d_surface(params)
            else:
                return {}
        except Exception as e:
            print(f"Error generating Plotly plot: {e}")
            return {}
    
    def _plotly_interactive_normal(self, params: Dict) -> Dict:
        """Create interactive normal distribution plot."""
        mean = params.get('mean', 0)
        std = params.get('std', 1)
        
        x = np.linspace(mean - 4*std, mean + 4*std, 1000)
        y = stats.norm.pdf(x, mean, std)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Distribution'))
        
        fig.update_layout(
            title=params.get('title', 'Normal Distribution'),
            xaxis_title=params.get('xlabel', 'Value'),
            yaxis_title='Probability Density',
            hovermode='x unified'
        )
        
        return json.loads(pio.to_json(fig))
    
    def _plotly_3d_surface(self, params: Dict) -> Dict:
        """Create 3D surface plot for multiple regression."""
        # Sample 3D surface
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        
        fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z)])
        fig.update_layout(
            title=params.get('title', '3D Surface Plot'),
            scene=dict(
                xaxis_title=params.get('xlabel', 'X'),
                yaxis_title=params.get('ylabel', 'Y'),
                zaxis_title=params.get('zlabel', 'Z')
            )
        )
        
        return json.loads(pio.to_json(fig))
    
    def render_mermaid(self, mermaid_code: str) -> str:
        """
        Validate Mermaid syntax and return the code.
        
        Args:
            mermaid_code: Mermaid diagram code
            
        Returns:
            Validated Mermaid code (client-side rendering)
        """
        # Basic validation - check for common syntax
        if not mermaid_code.strip():
            return ""
        
        # Check for valid diagram types
        valid_types = ['graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
                      'stateDiagram', 'erDiagram', 'gantt', 'pie']
        
        first_line = mermaid_code.strip().split('\n')[0].strip()
        if not any(first_line.startswith(t) for t in valid_types):
            print(f"⚠️  Warning: Mermaid diagram may have invalid type: {first_line}")
        
        return mermaid_code
    
    def render_graphviz(self, dot_code: str) -> str:
        """
        Render Graphviz DOT code to SVG.
        
        Args:
            dot_code: Graphviz DOT code
            
        Returns:
            SVG string or empty string if rendering fails
        """
        if not GRAPHVIZ_AVAILABLE:
            return ""
        
        try:
            graph = graphviz.Source(dot_code)
            svg_data = graph.pipe(format='svg').decode('utf-8')
            return svg_data
        except Exception as e:
            print(f"Error rendering Graphviz: {e}")
            return ""
    
    def detect_diagram_type(self, diagram_data: Union[str, Dict]) -> str:
        """
        Detect the type of diagram from the data.
        
        Args:
            diagram_data: String (code) or Dict (plot spec)
            
        Returns:
            Diagram type: 'plantuml', 'mermaid', 'graphviz', 'matplotlib', 'plotly', or 'unknown'
        """
        if isinstance(diagram_data, dict):
            if 'plot_type' in diagram_data:
                return 'matplotlib'
            elif 'data' in diagram_data and 'layout' in diagram_data:
                return 'plotly'
        
        if isinstance(diagram_data, str):
            diagram_lower = diagram_data.lower().strip()
            
            # Check for PlantUML
            if diagram_lower.startswith('@start'):
                return 'plantuml'
            
            # Check for Mermaid
            mermaid_keywords = ['graph', 'flowchart', 'sequencediagram', 'classdiagram']
            if any(diagram_lower.startswith(kw) for kw in mermaid_keywords):
                return 'mermaid'
            
            # Check for Graphviz
            if diagram_lower.startswith('digraph') or diagram_lower.startswith('graph {'):
                return 'graphviz'
        
        return 'unknown'

