/**
 * NumericalInput - Component for numerical answer questions
 * Supports single values and ranges with tolerance checking
 */

import React, { useState } from 'react';
import { EnhancedExplanation } from './ExplanationStep';
import './NumericalInput.css';

const NumericalInput = ({ question, onSubmit, showAnswer, userAnswer, isCorrect }) => {
  const [value, setValue] = useState('');
  const [hasSubmitted, setHasSubmitted] = useState(false);

  if (!question) return null;

  const {
    question_text: questionText,
    scenario,
    answer,
    explanation
  } = question;

  const handleSubmit = () => {
    const numericValue = parseFloat(value);
    
    if (isNaN(numericValue)) {
      alert('Please enter a valid number');
      return;
    }

    setHasSubmitted(true);
    onSubmit(numericValue);
  };

  const checkAnswer = (userValue) => {
    if (!answer) return false;

    const tolerance = answer.tolerance || 0.01;
    const correctValue = Array.isArray(answer.value) ? answer.value : [answer.value];

    // For single value
    if (correctValue.length === 1) {
      const diff = Math.abs(userValue - correctValue[0]);
      return diff <= tolerance;
    }

    // For range [lower, upper]
    if (correctValue.length === 2) {
      const [lower, upper] = correctValue;
      return userValue >= (lower - tolerance) && userValue <= (upper + tolerance);
    }

    return false;
  };

  const formatCorrectAnswer = () => {
    if (!answer) return '';
    
    const correctValue = Array.isArray(answer.value) ? answer.value : [answer.value];
    const units = answer.units ? ` ${answer.units}` : '';

    if (correctValue.length === 1) {
      return `${correctValue[0]}${units}`;
    }

    if (correctValue.length === 2) {
      return `${correctValue[0]} to ${correctValue[1]}${units}`;
    }

    return '';
  };

  return (
    <div className="numerical-question">
      <div className="question-content">
        <h3 className="question-text">{questionText}</h3>

        {scenario && (
          <div className="question-scenario">
            {scenario.context && (
              <div className="scenario-context">
                <h4>Scenario:</h4>
                <p>{scenario.context}</p>
              </div>
            )}

            {scenario.given_data && (
              <div className="scenario-data">
                <h4>Given Data:</h4>
                <ul className="data-list">
                  {Object.entries(scenario.given_data).map(([key, value]) => (
                    <li key={key}>
                      <span className="data-label">{key}:</span>
                      <span className="data-value">{value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="answer-input-section">
          <label htmlFor="numerical-input" className="input-label">
            Your Answer{answer?.units && ` (in ${answer.units})`}:
          </label>
          <div className="input-group">
            <input
              id="numerical-input"
              type="number"
              step="0.001"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              disabled={hasSubmitted || showAnswer}
              className="numerical-input"
              placeholder={`Enter answer${answer?.units ? ` in ${answer.units}` : ''}`}
            />
            {!hasSubmitted && !showAnswer && (
              <button
                onClick={handleSubmit}
                disabled={!value}
                className="submit-button"
              >
                Submit Answer
              </button>
            )}
          </div>
        </div>

        {(hasSubmitted || showAnswer) && (
          <div className={`answer-feedback ${isCorrect ? 'correct' : 'incorrect'}`}>
            <div className="feedback-header">
              {isCorrect ? (
                <>
                  <span className="feedback-icon">✓</span>
                  <span className="feedback-text">Correct!</span>
                </>
              ) : (
                <>
                  <span className="feedback-icon">✗</span>
                  <span className="feedback-text">Incorrect</span>
                </>
              )}
            </div>

            <div className="feedback-details">
              <p>
                <strong>Your answer:</strong> {userAnswer || value}
                {answer?.units && ` ${answer.units}`}
              </p>
              <p>
                <strong>Correct answer:</strong> {formatCorrectAnswer()}
              </p>
              {answer?.tolerance && (
                <p className="tolerance-note">
                  (Tolerance: ±{answer.tolerance})
                </p>
              )}
            </div>

            {explanation && (
              <div className="explanation-section">
                <h4 className="explanation-heading">Explanation:</h4>
                {typeof explanation === 'string' ? (
                  <p>{explanation}</p>
                ) : (
                  <EnhancedExplanation explanation={explanation} />
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default NumericalInput;

