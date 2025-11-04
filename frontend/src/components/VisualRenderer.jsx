/**
 * VisualRenderer - Renders Graphviz, Plotly, and LaTeX visualizations
 */

import React, { useEffect, useRef } from 'react';
import { graphviz } from 'd3-graphviz';
import Plot from 'react-plotly.js';
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import './VisualRenderer.css';

const VisualRenderer = ({ visualType, visualCode, altText }) => {
  const graphvizRef = useRef(null);

  useEffect(() => {
    if (visualType === 'Graphviz' && visualCode && graphvizRef.current) {
      try {
        graphviz(graphvizRef.current)
          .renderDot(visualCode)
          .on('end', () => {
            console.log('Graphviz rendered successfully');
          });
      } catch (error) {
        console.error('Error rendering Graphviz:', error);
      }
    }
  }, [visualType, visualCode]);

  if (!visualType || visualType === 'None' || !visualCode) {
    return null;
  }

  // Render Graphviz diagrams
  if (visualType === 'Graphviz') {
    return (
      <div className="visual-container graphviz-container">
        <div 
          ref={graphvizRef} 
          className="graphviz-render"
          role="img"
          aria-label={altText || 'Diagram visualization'}
        />
        {altText && <p className="visual-alt-text">{altText}</p>}
      </div>
    );
  }

  // Render Plotly charts
  if (visualType === 'Plotly') {
    try {
      const plotData = JSON.parse(visualCode);
      return (
        <div className="visual-container plotly-container">
          <Plot
            data={plotData.data || []}
            layout={plotData.layout || {}}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '400px' }}
          />
          {altText && <p className="visual-alt-text">{altText}</p>}
        </div>
      );
    } catch (error) {
      console.error('Error parsing Plotly data:', error);
      return (
        <div className="visual-error">
          Failed to render chart
        </div>
      );
    }
  }

  // Render LaTeX formulas
  if (visualType === 'LaTeX') {
    try {
      // Check if it's a block or inline formula
      const isBlockFormula = visualCode.trim().startsWith('\\[') || 
                            visualCode.includes('\\begin{');
      
      return (
        <div className="visual-container latex-container">
          {isBlockFormula ? (
            <BlockMath math={visualCode} />
          ) : (
            <InlineMath math={visualCode} />
          )}
          {altText && <p className="visual-alt-text">{altText}</p>}
        </div>
      );
    } catch (error) {
      console.error('Error rendering LaTeX:', error);
      return (
        <div className="visual-error">
          Failed to render formula
        </div>
      );
    }
  }

  return null;
};

export default VisualRenderer;


