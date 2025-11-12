/**
 * Custom hook for Mix Mode session state management
 * 
 * Manages the entire lifecycle of a Mix Mode session including:
 * - Starting sessions
 * - Fetching next activities
 * - Submitting answers
 * - Handling remediation flow
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  startMixSession,
  getMixSession,
  getNextActivity, 
  submitMixAnswer,
  revealMixAnswer,
  getMixSessionStatus,
  getDeckExamReadiness
} from '../api/mixMode';

// LocalStorage key for persisting session ID
const MIX_SESSION_STORAGE_KEY = 'mix_mode_session_id';

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
  
  // Reveal answer state
  const [revealedAnswer, setRevealedAnswer] = useState(null);
  const [isRevealed, setIsRevealed] = useState(false);
  
  // Exam readiness state
  const [examReadiness, setExamReadiness] = useState(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  
  // Store courseId and deckIds for readiness fetching
  const sessionMetadataRef = useRef({ courseId: null, deckIds: [] });
  
  // Tracking for previously incorrect questions
  const previouslyIncorrectRef = useRef(new Set());
  
  /**
   * Fetch exam readiness score
   */
  const fetchExamReadiness = useCallback(async (forceRefresh = false) => {
    const { courseId, deckIds } = sessionMetadataRef.current;
    
    if (!courseId || !deckIds || deckIds.length === 0) {
      console.warn('Cannot fetch readiness: missing courseId or deckIds');
      return;
    }
    
    setReadinessLoading(true);
    try {
      const data = await getDeckExamReadiness(courseId, deckIds, forceRefresh);
      setExamReadiness(data);
      console.log('✅ Exam readiness updated:', data.overall_readiness_score);
    } catch (error) {
      console.error('Failed to fetch exam readiness:', error);
      // Don't throw - readiness is supplementary, not critical
    } finally {
      setReadinessLoading(false);
    }
  }, []);
  
  /**
   * Start a new Mix Mode session
   */
  const startSession = useCallback(async (courseId, deckIds) => {
    try {
      setStatus('loading');
      setError(null);
      
      // Store metadata for readiness fetching
      sessionMetadataRef.current = { courseId, deckIds };
      
      const data = await startMixSession(courseId, deckIds);
      
      setSessionId(data.session_id);
      setProgress({
        seenInRound: 0,
        totalFlashcards: data.total_flashcards,
        currentRound: 1,
      });
      setStatus('active');
      
      // Persist session ID to localStorage for refresh recovery
      localStorage.setItem(MIX_SESSION_STORAGE_KEY, data.session_id);
      console.log('💾 Session ID saved to localStorage:', data.session_id);
      
      // Fetch initial exam readiness
      await fetchExamReadiness(false);
      
      // Return the session_id so it can be used immediately
      return { session_id: data.session_id, total_flashcards: data.total_flashcards };
    } catch (err) {
      console.error('Error starting mix session:', err);
      setError(err.message || 'Failed to start session');
      setStatus('error');
      throw err;
    }
  }, [fetchExamReadiness]);
  
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
      setIsRevealed(false);
      setRevealedAnswer(null);
      
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
      
      // Refresh exam readiness after answer submission (force refresh to get latest)
      await fetchExamReadiness(true);
      
      return result;
    } catch (err) {
      console.error('Error submitting answer:', err);
      setError(err.message || 'Failed to submit answer');
      throw err;
    }
  }, [sessionId, currentActivity, activityType, fetchExamReadiness]);
  
  /**
   * Reveal answer without recording performance
   */
  const revealAnswer = useCallback(async () => {
    if (!sessionId || !currentActivity || activityType !== 'question') {
      throw new Error('No active question to reveal');
    }
    
    try {
      const question = currentActivity.question;
      
      const revealData = {
        flashcard_id: currentActivity.flashcard_id,
        question_hash: question.question_hash,
        level: currentActivity.level,
        is_follow_up: currentActivity.is_follow_up || false,
      };
      
      const result = await revealMixAnswer(sessionId, revealData);
      
      setRevealedAnswer({
        correctAnswer: result.correct_answer,
        explanation: result.explanation,
        remediationInjected: result.remediation_injected,
      });
      setIsRevealed(true);
      
      return result;
    } catch (err) {
      console.error('Error revealing answer:', err);
      setError(err.message || 'Failed to reveal answer');
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
   * Resume an existing session from localStorage
   */
  const resumeSession = useCallback(async () => {
    const savedSessionId = localStorage.getItem(MIX_SESSION_STORAGE_KEY);
    
    if (!savedSessionId) {
      console.log('No saved session found in localStorage');
      return null;
    }
    
    try {
      setStatus('loading');
      setError(null);
      
      console.log('🔄 Attempting to resume session:', savedSessionId);
      
      // Fetch session from backend
      const sessionData = await getMixSession(savedSessionId);
      
      if (!sessionData || sessionData.status === 'completed') {
        console.log('Session completed or invalid, clearing localStorage');
        localStorage.removeItem(MIX_SESSION_STORAGE_KEY);
        setStatus('idle');
        return null;
      }
      
      // Restore session state
      setSessionId(sessionData.session_id);
      setProgress({
        seenInRound: sessionData.seen_in_current_round,
        totalFlashcards: sessionData.total_flashcards,
        currentRound: sessionData.current_round,
      });
      setStatus('active');
      
      // Store metadata for readiness fetching
      sessionMetadataRef.current = {
        courseId: sessionData.course_id,
        deckIds: sessionData.deck_ids,
      };
      
      // Fetch exam readiness
      await fetchExamReadiness(false);
      
      console.log('✅ Session resumed successfully');
      return sessionData;
    } catch (err) {
      console.error('Failed to resume session:', err);
      // Clear invalid session from localStorage
      localStorage.removeItem(MIX_SESSION_STORAGE_KEY);
      setStatus('idle');
      setError(null); // Don't show error for failed resume
      return null;
    }
  }, [fetchExamReadiness]);
  
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
    setIsRevealed(false);
    setRevealedAnswer(null);
    previouslyIncorrectRef.current.clear();
    
    // Clear localStorage
    localStorage.removeItem(MIX_SESSION_STORAGE_KEY);
    console.log('🗑️ Session cleared from localStorage');
  }, []);
  
  /**
   * Hide answer feedback and prepare for next activity
   */
  const hideFeedback = useCallback(() => {
    setShowFeedback(false);
    setAnswerFeedback(null);
    setIsRevealed(false);
    setRevealedAnswer(null);
  }, []);
  
  /**
   * Hide revealed answer and prepare for next activity
   */
  const hideRevealed = useCallback(() => {
    setIsRevealed(false);
    setRevealedAnswer(null);
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
    revealedAnswer,
    isRevealed,
    examReadiness,
    readinessLoading,
    
    // Actions
    startSession,
    resumeSession,
    fetchNextActivity,
    submitAnswer,
    revealAnswer,
    fetchSessionStatus,
    fetchExamReadiness,
    resetSession,
    hideFeedback,
    hideRevealed,
    
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

