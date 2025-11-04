/**
 * QuizResultsView - Display quiz results with flashcard links
 */

import React, { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { completeQuizSession } from '../api/adaptiveQuiz';
import './QuizResultsView.css';

const QuizResultsView = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { courseId, lectureId, level } = useParams();
  
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const hasSubmitted = useRef(false); // Prevent double submission

  const { userAnswers = [], score = 0, totalQuestions = 0, startTime } = location.state || {};

  useEffect(() => {
    // Save quiz session to history when results page loads
    const saveQuizToHistory = async () => {
      // Prevent double submission with ref
      if (hasSubmitted.current || userAnswers.length === 0 || saved || saving) return;
      
      hasSubmitted.current = true; // Mark as submitted immediately
      
      try {
        setSaving(true);
        
        // Calculate time taken (if startTime provided, otherwise default to 0)
        const timeTakenSeconds = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
        
        // Format question results for the backend
        const questionResults = userAnswers.map(answer => ({
          question_text: answer.question.question_text,
          user_answer: answer.userAnswer,
          correct_answer: answer.question.correct_answer,
          is_correct: answer.isCorrect,
          explanation: answer.question.explanation,
          source_flashcard_id: answer.question.source_flashcard_id || null
        }));
        
        // Save to backend
        await completeQuizSession(
          courseId,
          lectureId,
          parseInt(level),
          score,
          totalQuestions,
          timeTakenSeconds,
          questionResults
        );
        
        setSaved(true);
        console.log('✅ Quiz session saved to history');
      } catch (error) {
        console.error('Error saving quiz to history:', error);
        hasSubmitted.current = false; // Reset on error so user can retry
        // Don't block the user from seeing results even if save fails
      } finally {
        setSaving(false);
      }
    };
    
    saveQuizToHistory();
  }, []); // Run once on mount

  if (!userAnswers || userAnswers.length === 0) {
    return (
      <div className="quiz-results-error">
        <h2>No quiz data found</h2>
        <button onClick={() => navigate(-1)}>Go Back</button>
      </div>
    );
  }

  const percentage = Math.round((score / totalQuestions) * 100);
  const incorrectAnswers = userAnswers.filter(a => !a.isCorrect);

  const getPerformanceMessage = () => {
    if (percentage >= 90) return { text: '🎉 Outstanding!', color: '#4caf50' };
    if (percentage >= 80) return { text: '🌟 Excellent work!', color: '#8bc34a' };
    if (percentage >= 70) return { text: '👍 Good job!', color: '#2196f3' };
    if (percentage >= 60) return { text: '💪 Keep practicing!', color: '#ff9800' };
    return { text: '📚 Review recommended', color: '#f44336' };
  };

  const performanceMsg = getPerformanceMessage();

  const handleTryAgain = () => {
    navigate(`/courses/${courseId}/${lectureId}/quiz/${level}`);
  };

  const handleChooseLevel = () => {
    navigate(`/courses/${courseId}/${lectureId}/quiz`);
  };

  const handleBackToLecture = () => {
    navigate(`/courses/${courseId}/${lectureId}`);
  };

  const handleReviewFlashcard = (flashcardId) => {
    navigate(`/courses/${courseId}/${lectureId}/flashcards?card=${flashcardId}`);
  };

  return (
    <div className="quiz-results-view">
      {/* Hero Section */}
      <div className="results-hero">
        <div className="score-circle">
          <svg width="200" height="200" viewBox="0 0 200 200">
            <circle
              cx="100"
              cy="100"
              r="90"
              fill="none"
              stroke="#e0e0e0"
              strokeWidth="12"
            />
            <circle
              cx="100"
              cy="100"
              r="90"
              fill="none"
              stroke={performanceMsg.color}
              strokeWidth="12"
              strokeDasharray={`${2 * Math.PI * 90 * (percentage / 100)} ${2 * Math.PI * 90}`}
              strokeDashoffset={2 * Math.PI * 90 * 0.25}
              transform="rotate(-90 100 100)"
              strokeLinecap="round"
            />
            <text
              x="100"
              y="95"
              textAnchor="middle"
              fontSize="48"
              fontWeight="bold"
              fill="#333"
            >
              {percentage}%
            </text>
            <text
              x="100"
              y="120"
              textAnchor="middle"
              fontSize="16"
              fill="#666"
            >
              {score}/{totalQuestions}
            </text>
          </svg>
        </div>
        <h1 style={{ color: performanceMsg.color }}>{performanceMsg.text}</h1>
        <p className="results-subtitle">
          You answered {score} out of {totalQuestions} questions correctly
        </p>

        {/* Action Buttons */}
        <div className="results-actions">
          <button className="btn-primary" onClick={handleTryAgain}>
            🔄 Try Again
          </button>
          <button className="btn-secondary" onClick={handleChooseLevel}>
            📊 Choose Another Level
          </button>
          <button className="btn-secondary" onClick={handleBackToLecture}>
            ← Back to Lecture
          </button>
        </div>
      </div>

      {/* Review Section */}
      <div className="results-review">
        <h2>📝 Review Your Answers</h2>
        
        {userAnswers.map((answer, index) => (
          <div 
            key={index} 
            className={`review-item ${answer.isCorrect ? 'correct' : 'incorrect'}`}
          >
            <div className="review-header">
              <span className="review-number">Question {index + 1}</span>
              <span className={`review-badge ${answer.isCorrect ? 'correct' : 'incorrect'}`}>
                {answer.isCorrect ? '✅ Correct' : '❌ Incorrect'}
              </span>
            </div>

            <div className="review-content">
              <p className="review-question">{answer.question.question_text}</p>

              <div className="review-answers">
                <div className="answer-row">
                  <span className="answer-label">Your answer:</span>
                  <span className={`answer-text ${answer.isCorrect ? 'correct' : 'incorrect'}`}>
                    {answer.userAnswer}
                  </span>
                </div>

                {!answer.isCorrect && (
                  <div className="answer-row">
                    <span className="answer-label">Correct answer:</span>
                    <span className="answer-text correct">
                      {answer.question.correct_answer}
                    </span>
                  </div>
                )}
              </div>

              <div className="review-explanation">
                <strong>Explanation:</strong> {answer.question.explanation}
              </div>

              {/* Flashcard Link for Incorrect Answers */}
              {!answer.isCorrect && answer.question.source_flashcard_id && (
                <button 
                  className="flashcard-link-button"
                  onClick={() => handleReviewFlashcard(answer.question.source_flashcard_id)}
                >
                  📖 Review the Flashcard: {answer.question.source_flashcard_id}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Encouragement Box */}
      {incorrectAnswers.length > 0 && (
        <div className="encouragement-box">
          <h3>💡 Keep Learning!</h3>
          <p>
            You missed {incorrectAnswers.length} question{incorrectAnswers.length > 1 ? 's' : ''}. 
            Review the linked flashcards above to strengthen your understanding. 
            The adaptive quiz will focus more on these concepts in your next session!
          </p>
        </div>
      )}
    </div>
  );
};

export default QuizResultsView;


