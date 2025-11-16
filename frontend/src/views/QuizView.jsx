/**
 * QuizView - Main adaptive quiz interface
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startQuizSession, submitQuizAnswer } from '../api/adaptiveQuiz';
import VisualRenderer from '../components/VisualRenderer';
import { EnhancedExplanation } from '../components/quiz/ExplanationStep';
import './QuizView.css';

const QuizView = () => {
  const { courseId, lectureId, level } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null); // For MCQ: single value, For MCA: array
  const [showFeedback, setShowFeedback] = useState(false);
  const [userAnswers, setUserAnswers] = useState([]);
  const [score, setScore] = useState(0);
  const [startTime, setStartTime] = useState(null);
  
  // Use ref to track the latest answers (to avoid stale state in navigation)
  const userAnswersRef = useRef([]);

  useEffect(() => {
    loadQuizSession();
  }, [courseId, lectureId, level]);

  const loadQuizSession = async () => {
    try {
      setLoading(true);
      const data = await startQuizSession(courseId, lectureId, parseInt(level));
      setQuestions(data.questions);
      setStartTime(Date.now()); // Record start time
      setLoading(false);
    } catch (error) {
      console.error('Error loading quiz:', error);
      alert('Failed to load quiz. Please try again.');
      navigate(-1);
    }
  };

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  // Get correct answer keys (backend now guarantees these are option keys)
  const getCorrectAnswerKeys = (question) => {
    if (!question) return [];
    const raw = question.correct_answer;
    // Backend always returns an array of option keys now
    return Array.isArray(raw) ? raw : [raw];
  };

  // Reset selectedAnswer when question changes
  useEffect(() => {
    if (currentQuestion?.type === 'mca') {
      setSelectedAnswer([]); // Array for MCA
    } else {
      setSelectedAnswer(null); // Single value for MCQ
    }
  }, [currentIndex, currentQuestion?.type]);

  const handleAnswerSelect = (optionKey) => {
    if (showFeedback) return;

    if (currentQuestion.type === 'mca') {
      // Multiple correct answers - toggle selection
      setSelectedAnswer(prev => {
        const current = Array.isArray(prev) ? prev : [];
        return current.includes(optionKey)
          ? current.filter(k => k !== optionKey)
          : [...current, optionKey];
      });
    } else {
      // Single answer - replace selection
      setSelectedAnswer(optionKey);
    }
  };

  const handleCheckAnswer = async () => {
    // Validate answer exists
    if (!selectedAnswer || (Array.isArray(selectedAnswer) && selectedAnswer.length === 0)) {
      return;
    }

    // Calculate correctness based on question type
    let isCorrect = false;
    let earnedPoints = 0;

    // Normalize to option keys where possible
    const correctAnswers = getCorrectAnswerKeys(currentQuestion);

    if (currentQuestion.type === 'mca') {
      // MCA: Strict partial credit scoring
      const userAnswers = selectedAnswer; // Array like ["A", "B"]
      
      const incorrectSelections = userAnswers.filter(ans => !correctAnswers.includes(ans)).length;
      
      // If user selected ANY wrong option, they get ZERO credit
      if (incorrectSelections > 0) {
        earnedPoints = 0;
        isCorrect = false;
      } else {
        // No wrong selections - give partial credit based on how many correct ones they got
        const correctSelections = userAnswers.filter(ans => correctAnswers.includes(ans)).length;
        earnedPoints = correctSelections / correctAnswers.length;
        isCorrect = earnedPoints === 1; // Full credit only if all correct answers selected
      }
    } else {
      // MCQ: Binary scoring (prefer key comparison; fallback to text)
      const options = currentQuestion.options || {};
      const first = correctAnswers[0];
      if (first && options[first] !== undefined) {
        isCorrect = selectedAnswer === first;
      } else {
        const selectedText = String(options[selectedAnswer] ?? '').trim();
        const norm = (s) => s.replace(/\.$/, '').replace(/\s+/g, ' ').toLowerCase();
        isCorrect = norm(selectedText) === norm(String(first ?? ''));
      }
      earnedPoints = isCorrect ? 1 : 0;
    }

    setShowFeedback(true);

    // Update score
    const newScore = score + earnedPoints;
    setScore(newScore);

    // Record answer in userAnswers
    const answerRecord = {
      question: currentQuestion,
      userAnswer: selectedAnswer,
      isCorrect: isCorrect,
      earnedPoints: earnedPoints
    };
    const updatedAnswers = [...userAnswers, answerRecord];
    setUserAnswers(updatedAnswers);
    userAnswersRef.current = updatedAnswers; // Keep ref in sync

    // Submit to backend with question snapshot
    try {
      await submitQuizAnswer(
        courseId,
        lectureId,
        currentQuestion.question_hash,
        currentQuestion.source_flashcard_id,
        isCorrect,
        parseInt(level),
        currentQuestion.question_text,
        currentQuestion.options
      );
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  const handleNextQuestion = () => {
    if (isLastQuestion) {
      // Navigate to results using ref to get the latest answers
      // (state updates are async, so userAnswers might be stale)
      navigate(`/courses/${courseId}/${lectureId}/quiz/${level}/results`, {
        state: {
          questions: questions,
          userAnswers: userAnswersRef.current, // Use ref for latest value
          score: score,
          totalQuestions: questions.length,
          startTime: startTime
        }
      });
    } else {
      // Move to next question - useEffect will handle resetting selectedAnswer
      setShowFeedback(false);
      setCurrentIndex(currentIndex + 1);
    }
  };
  
  if (loading) {
    return (
      <div className="quiz-loading">
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <p>Loading your personalized quiz...</p>
      </div>
    );
  }

  if (!currentQuestion) {
    return <div className="quiz-error">No questions available</div>;
  }

  const getOptionClass = (optionKey) => {
    const isMCA = currentQuestion.type === 'mca';
    
    // Normalize to option keys where possible
    const correctAnswers = getCorrectAnswerKeys(currentQuestion);

    if (!showFeedback) {
      // Before feedback - show selection state
      if (isMCA) {
        return Array.isArray(selectedAnswer) && selectedAnswer.includes(optionKey) ? 'selected' : '';
      } else {
        return selectedAnswer === optionKey ? 'selected' : '';
      }
    }

    // After feedback - show correctness
    const isCorrectOption = correctAnswers.includes(optionKey);
    
    if (isMCA) {
      const userSelected = Array.isArray(selectedAnswer) && selectedAnswer.includes(optionKey);
      if (isCorrectOption && userSelected) return 'correct';
      if (isCorrectOption && !userSelected) return 'missed';
      if (!isCorrectOption && userSelected) return 'incorrect';
      return 'disabled';
    } else {
      if (isCorrectOption) return 'correct';
      if (optionKey === selectedAnswer && !isCorrectOption) return 'incorrect';
      return 'disabled';
    }
  };

  const isOptionSelected = (optionKey) => {
    const isMCA = currentQuestion.type === 'mca';
    return isMCA
      ? Array.isArray(selectedAnswer) && selectedAnswer.includes(optionKey)
      : selectedAnswer === optionKey;
  };

  return (
    <div className="quiz-view-wrapper">
    <div className="quiz-view">
      {/* Question Card - key forces remount on question change */}
      <div className="question-card" key={currentQuestion?.question_hash || currentIndex}>
        {/* Progress Bar (embedded in card header) */}
        <div className="progress-container in-card">
          <div className="progress-info">
            <span className="progress-text">Question {currentIndex + 1} of {questions.length}</span>
            <span className="progress-score">{score} correct</span>
          </div>
          <div className="progress-track">
            <div
              className="progress-indicator"
              style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
            >
              <span className="progress-percentage">{Math.round(((currentIndex + 1) / questions.length) * 100)}%</span>
        </div>
      </div>
        </div>
        <div className="question-content">
          {/* Question Type Indicator */}
          {currentQuestion.type === 'mca' ? (
            <div className="question-type-badge mca-badge">
              ✓✓ Multiple Correct - Select all that apply
            </div>
          ) : (
            <div className="question-type-badge mcq-badge">
              ○ Single Choice - Select one answer
            </div>
          )}

          <h2 className="question-text">{currentQuestion.question_text}</h2>

          {/* Visual Rendering */}
          <VisualRenderer 
            visualType={currentQuestion.visual_type}
            visualCode={currentQuestion.visual_code}
            altText={currentQuestion.alt_text}
          />

          {/* Options */}
          <div className="options-container">
            {Object.entries(currentQuestion.options).map(([key, value]) => (
              <label
                key={`${currentQuestion.question_hash || currentIndex}-${key}`}
                className={`option-button ${getOptionClass(key)}`}
              >
                <input
                  type={currentQuestion.type === 'mca' ? 'checkbox' : 'radio'}
                  name={`quiz-option-${currentQuestion.question_hash || currentIndex}`}
                  value={key}
                  checked={isOptionSelected(key)}
                  onChange={() => handleAnswerSelect(key)}
                disabled={showFeedback}
                  className="option-input"
                />
                <span className="option-label">{key}</span>
                <span className="option-text">{value}</span>
              </label>
            ))}
          </div>

          {/* Action Button - Positioned after options */}
          <div className="action-container">
            {!showFeedback ? (
              <button
                className="action-button primary"
                onClick={handleCheckAnswer}
                disabled={!selectedAnswer}
              >
                Check Answer
              </button>
            ) : (
              <button
                className="action-button primary"
                onClick={handleNextQuestion}
              >
                {isLastQuestion ? 'Finish Quiz' : 'Next Question →'}
              </button>
            )}
          </div>

          {/* Explanation (shown after feedback) */}
        {showFeedback && (
            <div className={`explanation-box ${(() => {
              const correctAnswers = getCorrectAnswerKeys(currentQuestion);
              if (currentQuestion.type === 'mca') {
                const userAnswers = selectedAnswer;
                const incorrectSelections = userAnswers.filter(ans => !correctAnswers.includes(ans)).length;
                if (incorrectSelections > 0) return 'incorrect';
                const correctSelections = userAnswers.filter(ans => correctAnswers.includes(ans)).length;
                const earnedPoints = correctSelections / correctAnswers.length;
                return earnedPoints === 1 ? 'correct' : (earnedPoints > 0 ? 'partial' : 'incorrect');
              } else {
                const options = currentQuestion.options || {};
                const first = correctAnswers[0];
                if (first && options[first] !== undefined) {
                  return selectedAnswer === first ? 'correct' : 'incorrect';
                }
                const selectedText = String(options[selectedAnswer] ?? '').trim();
                const norm = (s) => s.replace(/\.$/, '').replace(/\s+/g, ' ').toLowerCase();
                return norm(selectedText) === norm(String(first ?? '')) ? 'correct' : 'incorrect';
              }
            })()}`}>
              <h3>
                {(() => {
                  const correctAnswers = getCorrectAnswerKeys(currentQuestion);

                  if (currentQuestion.type === 'mca') {
                    const userAnswers = selectedAnswer;
                    const incorrectSelections = userAnswers.filter(ans => !correctAnswers.includes(ans)).length;
                    
                    // If user selected ANY wrong option, they get ZERO credit
                    if (incorrectSelections > 0) {
                      return 'Incorrect - Wrong option selected';
                    }
                    
                    // No wrong selections - calculate partial credit
                    const correctSelections = userAnswers.filter(ans => correctAnswers.includes(ans)).length;
                    const earnedPoints = correctSelections / correctAnswers.length;
                    
                    if (earnedPoints === 1) return 'Perfect!';
                    if (earnedPoints > 0) return `Partial Credit (${Math.round(earnedPoints * 100)}%)`;
                    return 'Incorrect';
                  } else {
                    const options = currentQuestion.options || {};
                    const first = correctAnswers[0];
                    if (first && options[first] !== undefined) {
                      return selectedAnswer === first ? 'Correct!' : 'Incorrect';
                    }
                    const selectedText = String(options[selectedAnswer] ?? '').trim();
                    const norm = (s) => s.replace(/\.$/, '').replace(/\s+/g, ' ').toLowerCase();
                    return norm(selectedText) === norm(String(first ?? '')) ? 'Correct!' : 'Incorrect';
                  }
                })()}
              </h3>
              {/* Handle both string and enhanced explanations */}
              {typeof currentQuestion.explanation === 'string' ? (
                <p><strong>Explanation:</strong> {currentQuestion.explanation}</p>
              ) : (
                <EnhancedExplanation explanation={currentQuestion.explanation} />
              )}
              {(() => {
                const correctAnswers = getCorrectAnswerKeys(currentQuestion);
                
                const options = currentQuestion.options || {};
                const isFullyCorrect = currentQuestion.type === 'mca' 
                  ? JSON.stringify([...selectedAnswer].sort()) === JSON.stringify([...correctAnswers].sort())
                  : (correctAnswers[0] && options[correctAnswers[0]] !== undefined
                      ? selectedAnswer === correctAnswers[0]
                      : (() => {
                          const selectedText = String(options[selectedAnswer] ?? '').trim();
                          const norm = (s) => s.replace(/\.$/, '').replace(/\s+/g, ' ').toLowerCase();
                          return norm(selectedText) === norm(String(correctAnswers[0] ?? ''));
                        })());
                
                if (!isFullyCorrect) {
                  return (
                <p className="correct-answer-note">
                      <strong>Correct answer{correctAnswers.length > 1 ? 's' : ''}:</strong>{' '}
                      {correctAnswers.map(key => {
                        const optText = currentQuestion.options?.[key];
                        return optText !== undefined ? `${key}: ${optText}` : String(key);
                      }).join(', ')}
                </p>
                  );
                }
              })()}
            </div>
          )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizView;
