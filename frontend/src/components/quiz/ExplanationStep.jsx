/**
 * ExplanationStep - Renders a single step in a step-by-step explanation
 * Supports text, LaTeX formulas, and diagrams
 */

import React from 'react';
import { InlineMath, BlockMath } from 'react-katex';
import DiagramRenderer from './DiagramRenderer';
import 'katex/dist/katex.min.css';
import './ExplanationStep.css';

const ExplanationStep = ({ step, index, total }) => {
  if (!step) return null;

  const {
    title,
    content,
    latex,
    diagram,
    diagram_type: diagramType,
    diagram_image: diagramImage
  } = step;

  return (
    <div className="explanation-step">
      <div className="step-header">
        <span className="step-number">Step {index + 1}{total ? ` of ${total}` : ''}</span>
        {title && <h4 className="step-title">{title}</h4>}
      </div>

      <div className="step-content">
        {content && <p className="step-text">{content}</p>}

        {latex && (
          <div className="step-latex">
            {latex.includes('\\\\') || latex.includes('\\begin{') ? (
              <BlockMath math={latex} />
            ) : (
              <div className="latex-block">
                <InlineMath math={latex} />
              </div>
            )}
          </div>
        )}

        {(diagram || diagramImage) && (
          <DiagramRenderer
            diagram={diagramImage || diagram}
            diagramType={diagramType}
            altText={`Diagram for ${title || `step ${index + 1}`}`}
          />
        )}
      </div>
    </div>
  );
};

/**
 * EnhancedExplanation - Renders a complete explanation with multiple steps
 */
export const EnhancedExplanation = ({ explanation }) => {
  if (!explanation) return null;

  const {
    text,
    step_by_step: steps,
    interpretation,
    business_context: businessContext,
    diagrams
  } = explanation;

  return (
    <div className="enhanced-explanation">
      {text && (
        <div className="explanation-summary">
          <p>{text}</p>
        </div>
      )}

      {steps && steps.length > 0 && (
        <div className="explanation-steps">
          <h4 className="steps-heading">Step-by-Step Solution:</h4>
          {steps.map((step, index) => (
            <ExplanationStep
              key={index}
              step={step}
              index={index}
              total={steps.length}
            />
          ))}
        </div>
      )}

      {interpretation && (
        <div className="explanation-interpretation">
          <h4 className="interpretation-heading">Interpretation:</h4>
          <p>{interpretation}</p>
        </div>
      )}

      {businessContext && (
        <div className="explanation-business-context">
          <h4 className="context-heading">Business Context:</h4>
          <p>{businessContext}</p>
        </div>
      )}

      {diagrams && Object.keys(diagrams).length > 0 && (
        <div className="explanation-additional-diagrams">
          {Object.entries(diagrams).map(([diagramType, diagramData]) => (
            <DiagramRenderer
              key={diagramType}
              diagram={diagramData}
              diagramType={diagramType}
              altText={`${diagramType} diagram`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ExplanationStep;

