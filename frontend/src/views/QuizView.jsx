/**
 * QuizView - Main adaptive quiz interface
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startQuizSession, submitQuizAnswer } from '../api/adaptiveQuiz';
import VisualRenderer from '../components/VisualRenderer';
import './QuizView.css';

const QuizView = () => {
  const { courseId, lectureId, level } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [userAnswers, setUserAnswers] = useState([]);
  const [score, setScore] = useState(0);
  const [startTime, setStartTime] = useState(null);

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

  const handleAnswerSelect = (option) => {
    if (!showFeedback) {
      setSelectedAnswer(option);
    }
  };

  const handleCheckAnswer = async () => {
    if (!selectedAnswer) return;

    const isCorrect = selectedAnswer === currentQuestion.correct_answer;
    setShowFeedback(true);

    // Update score
    if (isCorrect) {
      setScore(score + 1);
      }

    // Record answer in userAnswers
    const answerRecord = {
      question: currentQuestion,
      userAnswer: selectedAnswer,
      isCorrect: isCorrect
    };
    setUserAnswers([...userAnswers, answerRecord]);

    // Submit to backend
    try {
      await submitQuizAnswer(
        courseId,
        lectureId,
        currentQuestion.question_hash,
        currentQuestion.source_flashcard_id,
        isCorrect,
        parseInt(level)
      );
    } catch (error) {
      console.error('Error submitting answer:', error);
    }
  };

  const handleNextQuestion = () => {
    if (isLastQuestion) {
      // Navigate to results
      navigate(`/courses/${courseId}/${lectureId}/quiz/${level}/results`, {
        state: {
          questions: questions,
          userAnswers: [...userAnswers, {
            question: currentQuestion,
            userAnswer: selectedAnswer,
            isCorrect: selectedAnswer === currentQuestion.correct_answer
          }],
          score: selectedAnswer === currentQuestion.correct_answer ? score + 1 : score,
          totalQuestions: questions.length,
          startTime: startTime // Pass start time for duration calculation
        }
      });
    } else {
      setCurrentIndex(currentIndex + 1);
      setSelectedAnswer(null);
      setShowFeedback(false);
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

  const getOptionClass = (option) => {
    if (!showFeedback) {
      return selectedAnswer === option ? 'selected' : '';
  }

    if (option === currentQuestion.correct_answer) {
      return 'correct';
  }

    if (option === selectedAnswer && option !== currentQuestion.correct_answer) {
      return 'incorrect';
    }

    return 'disabled';
  };

  return (
    <div className="quiz-view-wrapper">
    <div className="quiz-view">
      {/* Question Card */}
      <div className="question-card">
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
              <button
                key={key}
                className={`option-button ${getOptionClass(value)}`}
                onClick={() => handleAnswerSelect(value)}
                disabled={showFeedback}
              >
                <span className="option-label">{key}</span>
                <span className="option-text">{value}</span>
              </button>
            ))}
          </div>

          {/* Explanation (shown after feedback) */}
        {showFeedback && (
            <div className="explanation-box">
              <h3>
                {selectedAnswer === currentQuestion.correct_answer ? '✅ Correct!' : '❌ Incorrect'}
              </h3>
              <p><strong>Explanation:</strong> {currentQuestion.explanation}</p>
              {selectedAnswer !== currentQuestion.correct_answer && (
                <p className="correct-answer-note">
                  <strong>Correct answer:</strong> {currentQuestion.correct_answer}
                </p>
              )}
            </div>
          )}
          </div>

        {/* Action Button */}
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
        </div>
      </div>
    </div>
  );
};

export default QuizView;
