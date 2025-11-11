/**
 * QuestionCard - Main component for displaying questions in Mix Mode
 * 
 * Features:
 * - Question header with difficulty and type
 * - Contextual messages for review
 * - Integrated question renderer
 */

import React from 'react';
import QuestionRenderer from '../QuestionRenderer';
import DifficultyTag from './DifficultyTag';
import InformativeMessage from './InformativeMessage';
import './QuestionCard.css';

const QuestionCard = ({ 
  question, 
  level, 
  isFollowUp, 
  isPreviouslyIncorrect,
  userAnswer,
  onAnswerChange,
  showFeedback,
  disabled 
}) => {
  if (!question) return null;
  
  // Determine question type label
  const getQuestionTypeLabel = (type) => {
    if (type === 'mca') return 'Multiple Correct Answers';
    if (type === 'mcq' || type === 'scenario_mcq') return 'Single Correct Answer';
    return type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };
  
  const questionTypeLabel = getQuestionTypeLabel(question.type);
  const isMCA = question.type === 'mca';
  
  return (
    <div className="mix-question-card">
      {/* Question Header */}
      <div className="mix-question-header">
        <div className="question-meta">
          <DifficultyTag level={level} />
          <span className="question-type-indicator">
            {isMCA && <span className="mca-icon">✓✓</span>}
            {questionTypeLabel}
          </span>
        </div>
        
        {/* Contextual Messages */}
        {(isPreviouslyIncorrect && !isFollowUp) && (
          <InformativeMessage type="review" />
        )}
        {isFollowUp && (
          <InformativeMessage type="followUp" />
        )}
      </div>
      
      {/* Question Content */}
      <div className="mix-question-content">
        <QuestionRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      </div>
    </div>
  );
};

export default QuestionCard;

