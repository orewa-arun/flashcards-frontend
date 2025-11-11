/**
 * Custom hook for Mix Mode session state management
 * 
 * Manages the entire lifecycle of a Mix Mode session including:
 * - Starting sessions
 * - Fetching next activities
 * - Submitting answers
 * - Handling remediation flow
 */

import { useState, useCallback, useRef } from 'react';
import { 
  startMixSession, 
  getNextActivity, 
  submitMixAnswer,
  getMixSessionStatus 
} from '../api/mixMode';

export const useMixSession = () => {
  // Session state
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle', 'loading', 'active', 'completed', 'error'
  const [error, setError] = useState(null);
  
  // Current activity state
  const [currentActivity, setCurrentActivity] = useState(null);
  const [activityType, setActivityType] = useState(null); // 'question' or 'flashcard'
  
  // Progress tracking
  const [progress, setProgress] = useState({
    seenInRound: 0,
    totalFlashcards: 0,
    currentRound: 1,
  });
  
  // Answer feedback
  const [answerFeedback, setAnswerFeedback] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  
  // Tracking for previously incorrect questions
  const previouslyIncorrectRef = useRef(new Set());
  
  /**
   * Start a new Mix Mode session
   */
  const startSession = useCallback(async (courseId, deckIds) => {
    try {
      setStatus('loading');
      setError(null);
      
      const data = await startMixSession(courseId, deckIds);
      
      setSessionId(data.session_id);
      setProgress({
        seenInRound: 0,
        totalFlashcards: data.total_flashcards,
        currentRound: 1,
      });
      setStatus('active');
      
      // Return the session_id so it can be used immediately
      return { session_id: data.session_id, total_flashcards: data.total_flashcards };
    } catch (err) {
      console.error('Error starting mix session:', err);
      setError(err.message || 'Failed to start session');
      setStatus('error');
      throw err;
    }
  }, []);
  
  /**
   * Fetch the next activity in the session
   */
  const fetchNextActivity = useCallback(async (explicitSessionId = null) => {
    const activeSessionId = explicitSessionId || sessionId;
    
    if (!activeSessionId) {
      throw new Error('No active session');
    }
    
    try {
      setStatus('loading');
      setError(null);
      setShowFeedback(false);
      setAnswerFeedback(null);
      
      const data = await getNextActivity(activeSessionId);
      
      // Check if session is complete
      if (!data || data === null) {
        setStatus('completed');
        setCurrentActivity(null);
        return null;
      }
      
      setCurrentActivity(data);
      setActivityType(data.activity_type);
      setProgress({
        seenInRound: data.progress.seen_in_round,
        totalFlashcards: data.progress.total_flashcards,
        currentRound: data.progress.current_round,
      });
      setStatus('active');
      
      // Track if this question was previously answered incorrectly
      if (data.activity_type === 'question' && data.question) {
        const questionHash = data.question.question_hash;
        if (previouslyIncorrectRef.current.has(questionHash)) {
          // This question was answered incorrectly before in this session
          data.isPreviouslyIncorrect = true;
        }
        
        // Normalize question field names for QuestionRenderer compatibility
        // Backend sends: question_text, correct_answer
        // QuestionRenderer expects: question, answer
        if (data.question.question_text && !data.question.question) {
          data.question.question = data.question.question_text;
        }
        if (data.question.correct_answer && !data.question.answer) {
          data.question.answer = data.question.correct_answer;
        }
      }
      
      return data;
    } catch (err) {
      console.error('Error fetching next activity:', err);
      setError(err.message || 'Failed to fetch next activity');
      setStatus('error');
      throw err;
    }
  }, [sessionId]);
  
  /**
   * Submit an answer for the current question
   */
  const submitAnswer = useCallback(async (userAnswer) => {
    if (!sessionId || !currentActivity || activityType !== 'question') {
      throw new Error('No active question to answer');
    }
    
    try {
      const question = currentActivity.question;
      
      const answerData = {
        flashcard_id: currentActivity.flashcard_id,
        question_hash: question.question_hash,
        level: currentActivity.level,
        user_answer: userAnswer,
        is_follow_up: currentActivity.is_follow_up || false,
      };
      
      const result = await submitMixAnswer(sessionId, answerData);
      
      // Track if this answer was incorrect
      if (!result.is_correct) {
        previouslyIncorrectRef.current.add(question.question_hash);
      }
      
      setAnswerFeedback({
        isCorrect: result.is_correct,
        correctAnswer: result.correct_answer,
        explanation: result.explanation,
        pointsEarned: result.points_earned,
        userAnswer: userAnswer,
      });
      setShowFeedback(true);
      
      return result;
    } catch (err) {
      console.error('Error submitting answer:', err);
      setError(err.message || 'Failed to submit answer');
      throw err;
    }
  }, [sessionId, currentActivity, activityType]);
  
  /**
   * Get session status (for resuming)
   */
  const fetchSessionStatus = useCallback(async () => {
    if (!sessionId) {
      throw new Error('No active session');
    }
    
    try {
      const data = await getMixSessionStatus(sessionId);
      return data;
    } catch (err) {
      console.error('Error fetching session status:', err);
      throw err;
    }
  }, [sessionId]);
  
  /**
   * Reset the session state
   */
  const resetSession = useCallback(() => {
    setSessionId(null);
    setStatus('idle');
    setError(null);
    setCurrentActivity(null);
    setActivityType(null);
    setProgress({
      seenInRound: 0,
      totalFlashcards: 0,
      currentRound: 1,
    });
    setAnswerFeedback(null);
    setShowFeedback(false);
    previouslyIncorrectRef.current.clear();
  }, []);
  
  /**
   * Hide answer feedback and prepare for next activity
   */
  const hideFeedback = useCallback(() => {
    setShowFeedback(false);
    setAnswerFeedback(null);
  }, []);
  
  return {
    // State
    sessionId,
    status,
    error,
    currentActivity,
    activityType,
    progress,
    answerFeedback,
    showFeedback,
    
    // Actions
    startSession,
    fetchNextActivity,
    submitAnswer,
    fetchSessionStatus,
    resetSession,
    hideFeedback,
    
    // Computed values
    isLoading: status === 'loading',
    isActive: status === 'active',
    isCompleted: status === 'completed',
    hasError: status === 'error',
    isQuestion: activityType === 'question',
    isFlashcard: activityType === 'flashcard',
  };
};

export default useMixSession;

