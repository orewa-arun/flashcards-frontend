/**
 * MixSessionView - Main view for Mix Mode sessions
 * 
 * Orchestrates the entire Mix Mode experience:
 * - Starting sessions
 * - Displaying questions and flashcards
 * - Handling answers and navigation
 * - Managing remediation flow
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaSpinner, FaCheckCircle, FaTimes } from 'react-icons/fa';
import { trackEvent } from '../utils/amplitude';
import { useMixSession } from '../hooks/useMixSession';
import ExamReadinessBar from '../components/MixMode/ExamReadinessBar';
import QuestionCard from '../components/MixMode/QuestionCard';
import FlashcardView from '../components/MixMode/FlashcardView';
import Flashcard from '../components/Flashcard';
import { EnhancedExplanation } from '../components/quiz/ExplanationStep';
import './MixSessionView.css';

const MixSessionView = () => {
  const { courseId, lectureId } = useParams();
  const navigate = useNavigate();
  
  const {
    sessionId,
    status,
    error,
    currentActivity,
    activityType,
    progress,
    answerFeedback,
    showFeedback,
    revealedAnswer,
    isRevealed,
    examReadiness,
    readinessLoading,
    isReferralModalOpen,
    referralFlashcardContent,
    isFetchingReferralFlashcard,
    startSession,
    resumeSession,
    fetchNextActivity,
    submitAnswer,
    revealAnswer,
    resetSession,
    hideFeedback,
    hideRevealed,
    referFlashcard,
    closeReferralModal,
    isLoading,
    isActive,
    isCompleted,
    hasError,
    isQuestion,
    isFlashcard,
  } = useMixSession();
  
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRevealing, setIsRevealing] = useState(false);
  const initializedRef = useRef(false);
  
  // Memoized initialization function
  const initializeSession = useCallback(async () => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    
    try {
      // First, try to resume an existing session
      const resumedSession = await resumeSession();
      
      if (resumedSession) {
        // Check if the resumed session matches the current URL
        const expectedDeckId = `deck_${lectureId}`;
        const sessionDeckIds = resumedSession.deck_ids || [];
        
        if (!sessionDeckIds.includes(expectedDeckId)) {
          console.log(`⚠️ Resumed session deck_ids (${sessionDeckIds}) don't match current URL (${expectedDeckId}), starting new session`);
          // Clear the mismatched session
          localStorage.removeItem('mix_mode_session_id');
          resetSession();
          // Start a new session for the current deck
          console.log('🆕 Starting new session for current deck');
          trackEvent('Mix Mode Started', { courseId, lectureId });
          const sessionData = await startSession(courseId, [lectureId]);
          await fetchNextActivity(sessionData.session_id);
        } else {
          console.log('✅ Resumed existing session');
          trackEvent('Mix Mode Resumed', { 
            courseId: resumedSession.course_id, 
            sessionId: resumedSession.session_id 
          });
          // Fetch the next activity for the resumed session
          await fetchNextActivity(resumedSession.session_id);
        }
      } else {
        // No existing session, start a new one
        console.log('🆕 Starting new session');
        trackEvent('Mix Mode Started', { courseId, lectureId });
        const sessionData = await startSession(courseId, [lectureId]);
        // Pass the session_id explicitly to fetchNextActivity
        await fetchNextActivity(sessionData.session_id);
      }
    } catch (err) {
      console.error('Failed to initialize session:', err);
      initializedRef.current = false; // Reset on error to allow retry
    }
  }, [courseId, lectureId, startSession, resumeSession, fetchNextActivity, resetSession]);
  
  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);
  
  const handleAnswerChange = (answer) => {
    if (showFeedback) return;
    setSelectedAnswer(answer);
  };
  
  const handleSubmitAnswer = async () => {
    if (!selectedAnswer || isSubmitting) return;
    
    try {
      setIsSubmitting(true);
      trackEvent('Mix Answer Submitted', { 
        courseId, 
        lectureId, 
        level: currentActivity?.level 
      });
      
      await submitAnswer(selectedAnswer);
      setIsSubmitting(false);
    } catch (err) {
      console.error('Failed to submit answer:', err);
      setIsSubmitting(false);
    }
  };
  
  const handleRevealAnswer = async () => {
    if (isRevealing || isRevealed) return;
    
    try {
      setIsRevealing(true);
      trackEvent('Mix Answer Revealed', { 
        courseId, 
        lectureId, 
        level: currentActivity?.level,
        isFollowUp: currentActivity?.is_follow_up || false
      });
      
      await revealAnswer();
      setIsRevealing(false);
    } catch (err) {
      console.error('Failed to reveal answer:', err);
      setIsRevealing(false);
    }
  };
  
  const handleNextActivity = async () => {
    hideFeedback();
    hideRevealed();
    setSelectedAnswer(null);
    
    try {
      await fetchNextActivity();
    } catch (err) {
      console.error('Failed to fetch next activity:', err);
    }
  };
  
  const handleFlashcardContinue = async () => {
    await handleNextActivity();
  };
  
  const handleComplete = () => {
    trackEvent('Mix Session Completed', { courseId, lectureId });
    resetSession();
    navigate(`/courses/${courseId}/${lectureId}`);
  };
  
  const handleExit = () => {
    if (window.confirm('Are you sure you want to exit? Your progress will be saved.')) {
      trackEvent('Mix Session Exited', { courseId, lectureId });
      resetSession();
      navigate(`/courses/${courseId}/${lectureId}`);
    }
  };
  
  // Reset selected answer when question changes
  useEffect(() => {
    if (currentActivity?.activity_type === 'question') {
      const questionType = currentActivity?.question?.type;
      if (questionType === 'mca') {
        setSelectedAnswer([]);
      } else {
        setSelectedAnswer(null);
      }
    }
  }, [currentActivity]);
  
  // Loading state
  if (isLoading && !currentActivity) {
    return (
      <div className="mix-session-view">
        <div className="mix-loading-container">
          <FaSpinner className="spinner-icon" />
          <p className="loading-text">Preparing your adaptive session...</p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (hasError) {
    return (
      <div className="mix-session-view">
        <div className="mix-error-container">
          <h2>Something went wrong</h2>
          <p>{error}</p>
          <button className="retry-button" onClick={initializeSession}>
            Try Again
          </button>
          <button className="exit-button" onClick={() => navigate(-1)}>
            Go Back
          </button>
        </div>
      </div>
    );
  }
  
  // Completion state
  if (isCompleted) {
    return (
      <div className="mix-session-view">
        <div className="mix-complete-container">
          <FaCheckCircle className="complete-icon" />
          <h2 className="complete-title">Session Complete!</h2>
          <p className="complete-message">
            Great work! You've completed all activities in this Mix session.
          </p>
          <div className="complete-stats">
            <div className="stat-item">
              <span className="stat-value">{progress.totalFlashcards}</span>
              <span className="stat-label">Concepts Reviewed</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{progress.currentRound}</span>
              <span className="stat-label">Rounds Completed</span>
            </div>
          </div>
          <button className="complete-button" onClick={handleComplete}>
            Return to Lecture
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="mix-session-view">
      <div className="mix-session-container">
        {/* Header with Exit Button */}
        <div className="mix-session-header">
          <button className="exit-button-small" onClick={handleExit}>
            ← Exit
          </button>
        </div>
        
        {/* Exam Readiness Bar */}
        <ExamReadinessBar 
          readinessData={examReadiness}
          isLoading={readinessLoading}
          showBreakdown={false}
        />
        
        {/* Content Area */}
        {isFlashcard && currentActivity?.flashcard_content && (
          <FlashcardView
            flashcard={currentActivity.flashcard_content}
            onContinue={handleFlashcardContinue}
          />
        )}
        
        {isQuestion && currentActivity?.question && (
          <div className="question-activity-container">
            {/* Action Buttons - Above Question */}
            {!showFeedback && !isRevealed && (
              <div className="question-action-buttons">
                <button
                  className="refer-flashcard-button"
                  onClick={referFlashcard}
                  disabled={isFetchingReferralFlashcard || isSubmitting}
                >
                  {isFetchingReferralFlashcard ? (
                    <>
                      <FaSpinner className="spinner-icon-small" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <span className="refer-icon">📚</span>
                      Refer Flashcard
                    </>
                  )}
                </button>
                
                <button
                  className="reveal-answer-link"
                  onClick={handleRevealAnswer}
                  disabled={isRevealing || isSubmitting}
                >
                  {isRevealing ? (
                    <>
                      <FaSpinner className="spinner-icon-small" />
                      Revealing...
                    </>
                  ) : (
                    <>
                      <span className="reveal-icon">👁️</span>
                      Reveal Answer
                    </>
                  )}
                </button>
              </div>
            )}
            
            <QuestionCard
              question={currentActivity.question}
              level={currentActivity.level}
              isFollowUp={currentActivity.is_follow_up}
              isPreviouslyIncorrect={currentActivity.isPreviouslyIncorrect}
              userAnswer={selectedAnswer}
              onAnswerChange={handleAnswerChange}
              showFeedback={showFeedback}
              disabled={showFeedback || isSubmitting || isRevealed}
            />
            
            {/* Answer Feedback */}
            {showFeedback && answerFeedback && (
              <div className={`answer-feedback ${answerFeedback.isCorrect ? 'correct' : 'incorrect'}`}>
                <div className="feedback-header">
                  <span className="feedback-icon">
                    {answerFeedback.isCorrect ? '✓' : '✗'}
                  </span>
                  <span className="feedback-title">
                    {answerFeedback.isCorrect ? 'Correct!' : 'Incorrect'}
                  </span>
                  <span className="feedback-points">
                    {answerFeedback.pointsEarned > 0 ? '+' : ''}{answerFeedback.pointsEarned} points
                  </span>
                </div>
                
                {/* Explanation - Always show */}
                {answerFeedback.explanation && (
                  <div className="feedback-explanation">
                    <h4 className="explanation-title">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="explanation-icon">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                        <path d="M12 16v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <circle cx="12" cy="8" r="1" fill="currentColor"/>
                      </svg>
                      Explanation
                    </h4>
                    {typeof answerFeedback.explanation === 'string' ? (
                      <p className="explanation-text">{answerFeedback.explanation}</p>
                    ) : (
                      <EnhancedExplanation explanation={answerFeedback.explanation} />
                    )}
                  </div>
                )}
                
                {!answerFeedback.isCorrect && (
                  <div className="feedback-content">
                    <p className="feedback-label">Correct Answer:</p>
                    <p className="feedback-answer">
                      {Array.isArray(answerFeedback.correctAnswer) 
                        ? answerFeedback.correctAnswer.join(', ') 
                        : answerFeedback.correctAnswer}
                    </p>
                  </div>
                )}
                
                <button className="next-activity-button" onClick={handleNextActivity}>
                  Continue →
                </button>
              </div>
            )}
            
            {/* Revealed Answer Display */}
            {isRevealed && revealedAnswer && (
              <div className="answer-revealed-container">
                <div className="revealed-header">
                  <span className="revealed-icon">👁️</span>
                  <span className="revealed-title">Answer Revealed</span>
                </div>
                
                <div className="revealed-content">
                  <p className="revealed-label">Correct Answer:</p>
                  <p className="revealed-answer">
                    {Array.isArray(revealedAnswer.correctAnswer) 
                      ? revealedAnswer.correctAnswer.join(', ') 
                      : revealedAnswer.correctAnswer}
                  </p>
                </div>
                
                {/* Explanation */}
                {revealedAnswer.explanation && (
                  <div className="revealed-explanation">
                    <h4 className="explanation-title">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="explanation-icon">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                        <path d="M12 16v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        <circle cx="12" cy="8" r="1" fill="currentColor"/>
                      </svg>
                      Explanation
                    </h4>
                    {typeof revealedAnswer.explanation === 'string' ? (
                      <p className="explanation-text">{revealedAnswer.explanation}</p>
                    ) : (
                      <EnhancedExplanation explanation={revealedAnswer.explanation} />
                    )}
                  </div>
                )}
                
                {/* Remediation message */}
                {revealedAnswer.remediationInjected && (
                  <div className="remediation-message">
                    <span className="remediation-icon">📚</span>
                    <span className="remediation-text">Reviewing flashcard next...</span>
                  </div>
                )}
                
                <button className="next-activity-button" onClick={handleNextActivity}>
                  Continue →
                </button>
              </div>
            )}
            
            {/* Submit Button */}
            {!showFeedback && !isRevealed && (
              <div className="submit-container">
                <button
                  className="submit-answer-button"
                  onClick={handleSubmitAnswer}
                  disabled={!selectedAnswer || isSubmitting || 
                    (Array.isArray(selectedAnswer) && selectedAnswer.length === 0)}
                >
                  {isSubmitting ? (
                    <>
                      <FaSpinner className="spinner-icon-small" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Answer'
                  )}
                </button>
              </div>
            )}
          </div>
        )}
        
        {/* Flashcard Reference Modal */}
        {isReferralModalOpen && referralFlashcardContent && (
          <div className="flashcard-modal-overlay" onClick={closeReferralModal}>
            <div className="flashcard-modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="flashcard-modal-header">
                <h3 className="flashcard-modal-title">Reference: Flashcard</h3>
                <button 
                  className="flashcard-modal-close"
                  onClick={closeReferralModal}
                  aria-label="Close modal"
                >
                  <FaTimes />
                </button>
              </div>
              
              <div className="flashcard-modal-body">
                <div className="flashcard-reference-note">
                  💡 <strong>Tip:</strong> Click the card to flip between question and answer
                </div>
                <Flashcard
                  card={referralFlashcardContent}
                  courseId={courseId}
                  deckId={lectureId}
                  index={0}
                  sessionId={null}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MixSessionView;

