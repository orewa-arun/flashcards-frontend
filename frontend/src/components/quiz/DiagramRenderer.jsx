/**
 * DiagramRenderer - Renders various diagram types for quiz explanations
 * Supports: Mermaid, Graphviz, Matplotlib (images), Plotly, LaTeX
 */

import React, { useEffect, useRef } from 'react';
import { graphviz } from 'd3-graphviz';
import Plot from 'react-plotly.js';
import { InlineMath, BlockMath } from 'react-katex';
import mermaid from 'mermaid';
import 'katex/dist/katex.min.css';
import './DiagramRenderer.css';

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'Arial, sans-serif'
});

const DiagramRenderer = ({ diagram, diagramType, altText }) => {
  const graphvizRef = useRef(null);
  const mermaidRef = useRef(null);
  const mermaidId = useRef(`mermaid-${Math.random().toString(36).substr(2, 9)}`);

  // Render Mermaid diagrams
  useEffect(() => {
    if (diagramType === 'mermaid' && diagram && mermaidRef.current) {
      try {
        mermaid.render(mermaidId.current, diagram).then(({ svg }) => {
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = svg;
          }
        }).catch(error => {
          console.error('Error rendering Mermaid:', error);
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = '<p class="diagram-error">Failed to render diagram</p>';
          }
        });
      } catch (error) {
        console.error('Error rendering Mermaid:', error);
      }
    }
  }, [diagram, diagramType]);

  // Render Graphviz diagrams
  useEffect(() => {
    if (diagramType === 'graphviz' && diagram && graphvizRef.current) {
      try {
        graphviz(graphvizRef.current)
          .renderDot(diagram)
          .on('end', () => {
            console.log('Graphviz rendered successfully');
          });
      } catch (error) {
        console.error('Error rendering Graphviz:', error);
      }
    }
  }, [diagram, diagramType]);

  if (!diagram || !diagramType) {
    return null;
  }

  // Render Matplotlib/image diagrams (base64 or URL)
  if (diagramType === 'matplotlib' || diagramType === 'image') {
    // Check if it's a string (base64 image or URL)
    if (typeof diagram === 'string') {
      const imgSrc = diagram.startsWith('data:') ? diagram : `data:image/png;base64,${diagram}`;
      
      return (
        <div className="diagram-container image-container">
          <img 
            src={imgSrc} 
            alt={altText || 'Diagram visualization'}
            className="diagram-image"
          />
          {altText && <p className="diagram-alt-text">{altText}</p>}
        </div>
      );
    }
    
    // If diagram is an object (plot spec), show placeholder
    if (typeof diagram === 'object' && diagram.plot_type) {
      return (
        <div className="diagram-container placeholder-container">
          <div className="diagram-placeholder">
            <p>📊 Chart visualization</p>
            <p className="placeholder-note">Plot type: {diagram.plot_type}</p>
          </div>
          {altText && <p className="diagram-alt-text">{altText}</p>}
        </div>
      );
    }
    
    // Fallback: shouldn't reach here
    return null;
  }

  // Render Mermaid diagrams
  if (diagramType === 'mermaid') {
    return (
      <div className="diagram-container mermaid-container">
        <div 
          ref={mermaidRef}
          className="mermaid-render"
          role="img"
          aria-label={altText || 'Mermaid diagram'}
        />
        {altText && <p className="diagram-alt-text">{altText}</p>}
      </div>
    );
  }

  // Render Graphviz diagrams
  if (diagramType === 'graphviz') {
    return (
      <div className="diagram-container graphviz-container">
        <div 
          ref={graphvizRef}
          className="graphviz-render"
          role="img"
          aria-label={altText || 'Graphviz diagram'}
        />
        {altText && <p className="diagram-alt-text">{altText}</p>}
      </div>
    );
  }

  // Render Plotly interactive charts
  if (diagramType === 'plotly') {
    try {
      const plotData = typeof diagram === 'string' ? JSON.parse(diagram) : diagram;
      return (
        <div className="diagram-container plotly-container">
          <Plot
            data={plotData.data || []}
            layout={{
              ...plotData.layout,
              autosize: true,
              margin: { l: 50, r: 50, t: 50, b: 50 }
            }}
            config={{ 
              responsive: true, 
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
            }}
            style={{ width: '100%', height: '400px' }}
          />
          {altText && <p className="diagram-alt-text">{altText}</p>}
        </div>
      );
    } catch (error) {
      console.error('Error rendering Plotly:', error);
      return (
        <div className="diagram-error">
          Failed to render interactive chart
        </div>
      );
    }
  }

  // Render LaTeX formulas
  if (diagramType === 'latex') {
    try {
      const isBlockFormula = diagram.trim().startsWith('\\[') || 
                            diagram.includes('\\begin{');
      
      return (
        <div className="diagram-container latex-container">
          {isBlockFormula ? (
            <BlockMath math={diagram} />
          ) : (
            <InlineMath math={diagram} />
          )}
          {altText && <p className="diagram-alt-text">{altText}</p>}
        </div>
      );
    } catch (error) {
      console.error('Error rendering LaTeX:', error);
      return (
        <div className="diagram-error">
          Failed to render formula
        </div>
      );
    }
  }

  return null;
};

export default DiagramRenderer;

