import { useState, useEffect } from 'react'
import { FaHistory, FaArrowLeft, FaTrophy, FaClock, FaCheck, FaTimes, FaBook, FaFire, FaExclamationTriangle } from 'react-icons/fa'
import { useNavigate } from 'react-router-dom'
import { getQuizHistory, getQuizHistoryByDeck, getQuizAttemptDetails } from '../api/quizHistory'
import ScoreRing from '../components/ScoreRing'
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
  const navigate = useNavigate()

  // Helper function to format difficulty level for display
  const formatDifficulty = (difficulty) => {
    if (!difficulty) return { emoji: '📚', label: 'Medium', class: 'medium' };
    
    const difficultyMap = {
      'level_1': { emoji: '🟢', label: 'Easy', class: 'easy' },
      'level_2': { emoji: '🟡', label: 'Medium', class: 'medium' },
      'level_3': { emoji: '🔴', label: 'Hard', class: 'hard' },
      'level_4': { emoji: '💀', label: 'Boss Level', class: 'boss' },
      'easy': { emoji: '🟢', label: 'Easy', class: 'easy' },
      'medium': { emoji: '🟡', label: 'Medium', class: 'medium' },
      'hard': { emoji: '🔴', label: 'Hard', class: 'hard' }
    };
    
    return difficultyMap[difficulty] || { emoji: '📚', label: difficulty, class: 'medium' };
  }

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

  const handleTackleWeakConcepts = (courseId, deckId) => {
    navigate(`/weak-concepts?course=${courseId}&deck=${deckId}`)
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
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

  // Calculate study streak and stats
  const calculateStats = () => {
    if (quizHistory.length === 0) return { totalQuizzes: 0, averageScore: 0, studyStreak: 0 }
    
    const totalQuizzes = quizHistory.reduce((sum, deck) => sum + deck.attempt_count, 0)
    const averageScore = quizHistory.reduce((sum, deck) => sum + deck.highest_percentage, 0) / quizHistory.length
    
    // Simple streak calculation (consecutive days with quiz attempts)
    const dates = quizHistory.map(deck => new Date(deck.latest_attempt_date).toDateString())
    const uniqueDates = [...new Set(dates)].sort((a, b) => new Date(b) - new Date(a))
    
    let streak = 0
    const today = new Date().toDateString()
    
    if (uniqueDates.length > 0 && (uniqueDates[0] === today || uniqueDates[0] === new Date(Date.now() - 86400000).toDateString())) {
      streak = 1
      for (let i = 1; i < uniqueDates.length; i++) {
        const prevDate = new Date(uniqueDates[i - 1])
        const currDate = new Date(uniqueDates[i])
        const diffDays = Math.floor((prevDate - currDate) / 86400000)
        
        if (diffDays === 1) {
          streak++
        } else {
          break
        }
      }
    }
    
    return { totalQuizzes, averageScore, studyStreak: streak }
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
              <span className={`difficulty-badge ${formatDifficulty(attemptDetails.difficulty).class}`}>
                {formatDifficulty(attemptDetails.difficulty).emoji} {formatDifficulty(attemptDetails.difficulty).label}
              </span>
            </div>
            <div className="attempt-meta">
              <span><FaClock /> {formatTime(attemptDetails.time_taken)}</span>
              <span>{formatDateTime(attemptDetails.completed_at)}</span>
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
                  <div className="result-question">{question.question}</div>

                  <div className="answer-section">
                    <div className="user-answer">
                      <strong>Your Answer:</strong>
                      <div className="answer-content">
                        {typeof question.user_answer === 'object' 
                          ? JSON.stringify(question.user_answer, null, 2)
                          : question.user_answer}
                      </div>
                    </div>
                    
                    <div className="correct-answer">
                      <strong>Correct Answer:</strong>
                      <div className="answer-content">
                        {typeof question.correct_answer === 'object'
                          ? JSON.stringify(question.correct_answer, null, 2)
                          : question.correct_answer}
                      </div>
                    </div>
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
                  <div className="attempt-header-row">
                    <div className="attempt-number">Attempt #{deckAttempts.length - index}</div>
                    <span className={`difficulty-badge ${formatDifficulty(attempt.difficulty).class}`}>
                      {formatDifficulty(attempt.difficulty).emoji} {formatDifficulty(attempt.difficulty).label}
                    </span>
                  </div>
                  <div className="attempt-score">
                    <span className={`score-badge ${getScoreColor(attempt.percentage)}`}>
                      {attempt.score}/{attempt.total_questions}
                    </span>
                    <span className="score-percentage">{attempt.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="attempt-details-summary">
                    <span><FaClock /> {formatTime(attempt.time_taken)}</span>
                    <span className="attempt-date">{formatDateTime(attempt.completed_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Main Timeline View - The Living Academic Journal
  const stats = calculateStats()
  const sortedHistory = [...quizHistory].sort((a, b) => new Date(b.latest_attempt_date) - new Date(a.latest_attempt_date))

  return (
    <div className="quiz-history-view">
      <div className="history-header">
        <div className="header-content">
          <h1 className="page-title">
            <FaHistory className="title-icon" />
            Performance Timeline
          </h1>
          <div className="stats-dashboard">
            {stats.studyStreak > 0 && (
              <div className="stat-card streak-card">
                <FaFire className="stat-icon fire-icon" />
                <div className="stat-content">
                  <div className="stat-value">{stats.studyStreak}-Day</div>
                  <div className="stat-label">Study Streak</div>
                </div>
              </div>
            )}
            <div className="stat-card">
              <div className="stat-content">
                <div className="stat-value">{stats.totalQuizzes}</div>
                <div className="stat-label">Total Quizzes</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-content">
                <div className="stat-value">{Math.round(stats.averageScore)}%</div>
                <div className="stat-label">Average Score</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {quizHistory.length === 0 ? (
        <div className="empty-state">
          <FaHistory className="empty-icon" />
          <h2>No quiz history yet</h2>
          <p>Complete some quizzes to see your performance timeline here.</p>
        </div>
      ) : (
        <div className="history-content">
          <div className="timeline">
            <div className="timeline-spine"></div>
            {sortedHistory.map((deck, index) => (
              <div
                key={`${deck.course_id}:${deck.deck_id}`}
                className={`timeline-entry ${index % 2 === 0 ? 'timeline-entry-left' : 'timeline-entry-right'}`}
                onClick={() => handleDeckClick(deck)}
              >
                <div className="timeline-connector"></div>
                <div className="timeline-node">
                  <ScoreRing 
                    score={deck.highest_percentage} 
                    size="md"
                  />
                </div>
                <div className="timeline-card">
                  <h3 className="timeline-title">{deck.deck_id}</h3>
                  <span className="timeline-course-tag">{deck.course_id}</span>
                  <div className="timeline-meta">
                    <span className="timeline-datetime">{formatDateTime(deck.latest_attempt_date)}</span>
                    <span className="timeline-attempts">{deck.attempt_count} Attempt{deck.attempt_count !== 1 ? 's' : ''}</span>
                  </div>
                  {deck.highest_percentage < 60 ? (
                    <button 
                      className="timeline-cta timeline-cta-warning"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleTackleWeakConcepts(deck.course_id, deck.deck_id)
                      }}
                    >
                      <FaExclamationTriangle /> Tackle Weak Concepts
                    </button>
                  ) : (
                    <button className="timeline-cta timeline-cta-secondary">
                      Review Attempt →
                    </button>
                  )}
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
