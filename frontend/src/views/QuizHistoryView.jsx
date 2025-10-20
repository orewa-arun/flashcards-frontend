import { useState, useEffect } from 'react'
import { FaHistory, FaArrowLeft, FaTrophy, FaClock, FaCheck, FaTimes, FaBook } from 'react-icons/fa'
import { getQuizHistory, getQuizHistoryByDeck, getQuizAttemptDetails } from '../api/quizHistory'
import './QuizHistoryView.css'

function QuizHistoryView() {
  const [view, setView] = useState('summary') // 'summary', 'deck', 'attempt'
  const [quizHistory, setQuizHistory] = useState([])
  const [selectedDeck, setSelectedDeck] = useState(null)
  const [deckAttempts, setDeckAttempts] = useState([])
  const [selectedAttempt, setSelectedAttempt] = useState(null)
  const [attemptDetails, setAttemptDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadQuizHistory()
  }, [])

  const loadQuizHistory = async () => {
    try {
      setLoading(true)
      const history = await getQuizHistory()
      setQuizHistory(history)
      setError(null)
    } catch (err) {
      setError('Failed to load quiz history')
      console.error('Error loading quiz history:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDeckClick = async (deck) => {
    try {
      setLoading(true)
      setSelectedDeck(deck)
      const attempts = await getQuizHistoryByDeck(deck.deck_id)
      setDeckAttempts(attempts)
      setView('deck')
      setError(null)
    } catch (err) {
      setError('Failed to load deck attempts')
      console.error('Error loading deck attempts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAttemptClick = async (attempt) => {
    try {
      setLoading(true)
      setSelectedAttempt(attempt)
      const details = await getQuizAttemptDetails(attempt.result_id)
      setAttemptDetails(details)
      // console.log("attempt details", details);
      setView('attempt')
      setError(null)
    } catch (err) {
      setError('Failed to load attempt details')
      console.error('Error loading attempt details:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleBackToSummary = () => {
    setView('summary')
    setSelectedDeck(null)
    setDeckAttempts([])
  }

  const handleBackToDeck = () => {
    setView('deck')
    setSelectedAttempt(null)
    setAttemptDetails(null)
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getScoreColor = (percentage) => {
    if (percentage >= 90) return 'excellent'
    if (percentage >= 80) return 'good'
    if (percentage >= 70) return 'fair'
    return 'poor'
  }

  if (loading) {
    return (
      <div className="quiz-history-view">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading quiz history...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="quiz-history-view">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={loadQuizHistory} className="retry-btn">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // Attempt Details View
  if (view === 'attempt' && attemptDetails) {
    return (
      <div className="quiz-history-view">
        <div className="quiz-detail-header">
          <button onClick={handleBackToDeck} className="back-btn">
            <FaArrowLeft />
            Back to {selectedDeck?.deck_id}
          </button>
          <div className="attempt-summary">
            <div className="attempt-score">
              <span className={`score-badge ${getScoreColor(attemptDetails.percentage)}`}>
                {attemptDetails.score}/{attemptDetails.total_questions}
              </span>
              <span className="score-percentage">{attemptDetails.percentage.toFixed(1)}%</span>
            </div>
            <div className="attempt-meta">
              <span><FaClock /> {formatTime(attemptDetails.time_taken)}</span>
              <span>{formatDate(attemptDetails.completed_at)}</span>
            </div>
          </div>
        </div>

        <div className="attempt-details">
          <h2>Question Results</h2>
          <div className="questions-list">
            {attemptDetails.question_results.map((question, index) => (
              <div key={index} className={`question-result ${question.is_correct ? 'correct' : 'incorrect'}`}>
                <div className="question-header">
                  <div className="question-number">
                    Question {question.question_number}
                    {question.is_correct ? (
                      <FaCheck className="result-icon correct" />
                    ) : (
                      <FaTimes className="result-icon incorrect" />
                    )}
                  </div>
                  {question.time_taken && (
                    <span className="question-time">{formatTime(question.time_taken)}</span>
                  )}
                </div>
                
                <div className="question-content">
                  <div className="question-type-badge">{question.question_type}</div>
                  <div className="result-question">{question.question.question}</div>

                  <div className="answer-section">
                    <div className="user-answer">
                      <strong>Your Answer:</strong>
                      <div className="answer-content">
                        {typeof question.user_answer === 'object' 
                          ? JSON.stringify(question.user_answer, null, 2)
                          : question.user_answer}
                      </div>
                    </div>
                    
                    {!question.is_correct && (
                      <div className="correct-answer">
                        <strong>Correct Answer:</strong>
                        <div className="answer-content">
                          {typeof question.correct_answer === 'object'
                            ? JSON.stringify(question.correct_answer, null, 2)
                            : question.correct_answer}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Deck Attempts View
  if (view === 'deck' && selectedDeck) {
    return (
      <div className="quiz-history-view">
        <div className="deck-header">
          <button onClick={handleBackToSummary} className="back-btn">
            <FaArrowLeft />
            Back to History
          </button>
          <div className="deck-info">
            <h1>{selectedDeck.deck_id}</h1>
            <span className="course-badge">{selectedDeck.course_id}</span>
            <div className="deck-stats">
              <span><FaTrophy /> Best: {selectedDeck.highest_percentage.toFixed(1)}%</span>
              <span>Total Attempts: {selectedDeck.attempt_count}</span>
            </div>
          </div>
        </div>

        <div className="attempts-list">
          <h2>All Attempts</h2>
          {deckAttempts.length === 0 ? (
            <div className="empty-attempts">
              <p>No quiz attempts found for this deck.</p>
            </div>
          ) : (
            <div className="attempts-grid">
              {deckAttempts.map((attempt, index) => (
                <div
                  key={attempt.result_id}
                  className="attempt-card"
                  onClick={() => handleAttemptClick(attempt)}
                >
                  <div className="attempt-number">Attempt #{deckAttempts.length - index}</div>
                  <div className="attempt-score">
                    <span className={`score-badge ${getScoreColor(attempt.percentage)}`}>
                      {attempt.score}/{attempt.total_questions}
                    </span>
                    <span className="score-percentage">{attempt.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="attempt-details-summary">
                    <span><FaClock /> {formatTime(attempt.time_taken)}</span>
                    <span className="attempt-date">{formatDate(attempt.completed_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Main Summary View
  return (
    <div className="quiz-history-view">
      <div className="history-header">
        <div className="header-content">
          <h1 className="page-title">
            <FaHistory className="title-icon" />
            Quiz History
          </h1>
          <p className="page-subtitle">
            {quizHistory.length} deck{quizHistory.length !== 1 ? 's' : ''} attempted
          </p>
        </div>
      </div>

      {quizHistory.length === 0 ? (
        <div className="empty-state">
          <FaHistory className="empty-icon" />
          <h2>No quiz history yet</h2>
          <p>Complete some quizzes to see your performance history here.</p>
        </div>
      ) : (
        <div className="history-content">
          <div className="decks-grid">
            {quizHistory.map(deck => (
              <div
                key={`${deck.course_id}:${deck.deck_id}`}
                className="deck-card"
                onClick={() => handleDeckClick(deck)}
              >
                <div className="deck-card-header">
                  <div className="deck-title">
                    <FaBook className="deck-icon" />
                    <span>{deck.deck_id}</span>
                  </div>
                  <span className="course-badge">{deck.course_id}</span>
                </div>
                
                <div className="deck-stats">
                  <div className="stat-item">
                    <span className="stat-label">Best Score</span>
                    <span className={`stat-value ${getScoreColor(deck.highest_percentage)}`}>
                      {deck.highest_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Attempts</span>
                    <span className="stat-value">{deck.attempt_count}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Last Attempt</span>
                    <span className="stat-value">
                      {formatDate(deck.latest_attempt_date)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default QuizHistoryView