import { useState, useEffect } from 'react'
import { FaChartBar, FaUsers, FaClipboard, FaThumbsUp, FaThumbsDown, FaChevronDown, FaChevronUp, FaStar, FaHistory } from 'react-icons/fa'
import {
  getAnalyticsOverview,
  getAllSessions,
  getQuizPerformanceSummary,
  getFlashcardFeedbackSummary,
  getFlashcardFeedbackDetails,
  getAllUsersSummary
} from '../api/adminAnalytics'
import './AdminDashboardView.css'

function AdminDashboardView() {
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedSessions, setExpandedSessions] = useState(new Set())
  const [expandedFeedback, setExpandedFeedback] = useState(new Set())

  // Data states
  const [overview, setOverview] = useState({})
  const [sessions, setSessions] = useState([])
  const [quizPerformance, setQuizPerformance] = useState([])
  const [feedbackSummary, setFeedbackSummary] = useState([])
  const [feedbackDetails, setFeedbackDetails] = useState([])
  const [users, setUsers] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load all data in parallel
      const [
        overviewData,
        sessionsData,
        quizData,
        feedbackSummaryData,
        feedbackDetailsData,
        usersData
      ] = await Promise.all([
        getAnalyticsOverview(),
        getAllSessions(),
        getQuizPerformanceSummary(),
        getFlashcardFeedbackSummary(),
        getFlashcardFeedbackDetails(),
        getAllUsersSummary()
      ])

      setOverview(overviewData)
      setSessions(sessionsData)
      setQuizPerformance(quizData)
      setFeedbackSummary(feedbackSummaryData)
      setFeedbackDetails(feedbackDetailsData)
      setUsers(usersData)
      setError(null)
      
    } catch (err) {
      setError('Failed to load analytics data')
      console.error('Error loading analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds) => {
    if (!seconds) return 'N/A'
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

  const toggleSessionExpansion = (sessionId) => {
    const newExpanded = new Set(expandedSessions)
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId)
    } else {
      newExpanded.add(sessionId)
    }
    setExpandedSessions(newExpanded)
  }

  const toggleFeedbackExpansion = (flashcardId) => {
    const newExpanded = new Set(expandedFeedback)
    if (newExpanded.has(flashcardId)) {
      newExpanded.delete(flashcardId)
    } else {
      newExpanded.add(flashcardId)
    }
    setExpandedFeedback(newExpanded)
  }

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading analytics dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="admin-dashboard">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={loadData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1 className="dashboard-title">
          <FaChartBar className="title-icon" />
          Admin Analytics Dashboard
        </h1>
        <p className="dashboard-subtitle">
          Comprehensive analytics and user behavior insights
        </p>
      </div>

      <div className="dashboard-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <FaChartBar />
          Overview
        </button>
        <button
          className={`tab-btn ${activeTab === 'sessions' ? 'active' : ''}`}
          onClick={() => setActiveTab('sessions')}
        >
          <FaHistory />
          Sessions
        </button>
        <button
          className={`tab-btn ${activeTab === 'quiz' ? 'active' : ''}`}
          onClick={() => setActiveTab('quiz')}
        >
          <FaClipboard />
          Quiz Performance
        </button>
        <button
          className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('feedback')}
        >
          <FaThumbsUp />
          Feedback
        </button>
        <button
          className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <FaUsers />
          Users
        </button>
      </div>

      <div className="dashboard-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon users">
                  <FaUsers />
                </div>
                <div className="stat-info">
                  <div className="stat-number">{overview.total_users}</div>
                  <div className="stat-label">Total Users</div>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon sessions">
                  <FaHistory />
                </div>
                <div className="stat-info">
                  <div className="stat-number">{overview.total_sessions}</div>
                  <div className="stat-label">Study Sessions</div>
                  <div className="stat-detail">{overview.completed_sessions} completed</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon quizzes">
                  <FaClipboard />
                </div>
                <div className="stat-info">
                  <div className="stat-number">{overview.total_quiz_attempts}</div>
                  <div className="stat-label">Quiz Attempts</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon feedback">
                  <FaThumbsUp />
                </div>
                <div className="stat-info">
                  <div className="stat-number">{overview.total_feedback}</div>
                  <div className="stat-label">Feedback Given</div>
                  <div className="stat-detail">
                    {overview.feedback_likes} likes, {overview.feedback_dislikes} dislikes
                  </div>
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-icon bookmarks">
                  <FaStar />
                </div>
                <div className="stat-info">
                  <div className="stat-number">{overview.total_bookmarks}</div>
                  <div className="stat-label">Bookmarks</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Sessions Tab */}
        {activeTab === 'sessions' && (
          <div className="sessions-section">
            <h2>All Study Sessions ({sessions.length})</h2>
            <div className="sessions-list">
              {sessions.map(session => (
                <div key={session.session_id} className="session-card">
                  <div 
                    className="session-header"
                    onClick={() => toggleSessionExpansion(session.session_id)}
                  >
                    <div className="session-info">
                      <span className="session-user">User: {session.user_id.substring(0, 8)}...</span>
                      <span className="session-deck">{session.course_id} / {session.deck_id}</span>
                      <span className="session-date">{formatDate(session.session_start_time)}</span>
                    </div>
                    <div className="session-stats">
                      <span>Study: {formatTime(session.study_duration_seconds)}</span>
                      {session.quiz_score !== null && (
                        <span>Quiz: {session.quiz_score}/{session.quiz_total_questions}</span>
                      )}
                      <span className={`completion-badge ${session.is_completed ? 'completed' : 'incomplete'}`}>
                        {session.is_completed ? 'Complete' : 'Incomplete'}
                      </span>
                      {expandedSessions.has(session.session_id) ? <FaChevronUp /> : <FaChevronDown />}
                    </div>
                  </div>
                  
                  {expandedSessions.has(session.session_id) && (
                    <div className="session-details">
                      <div className="session-detail-grid">
                        <div className="detail-item">
                          <strong>Session ID:</strong> {session.session_id}
                        </div>
                        <div className="detail-item">
                          <strong>User ID:</strong> {session.user_id}
                        </div>
                        <div className="detail-item">
                          <strong>Study Duration:</strong> {formatTime(session.study_duration_seconds)}
                        </div>
                        <div className="detail-item">
                          <strong>Quiz Duration:</strong> {formatTime(session.quiz_duration_seconds)}
                        </div>
                        {session.quiz_percentage && (
                          <div className="detail-item">
                            <strong>Quiz Score:</strong> {session.quiz_percentage.toFixed(1)}%
                          </div>
                        )}
                        <div className="detail-item">
                          <strong>Completed:</strong> {session.completed_at ? formatDate(session.completed_at) : 'No'}
                        </div>
                      </div>
                      
                      {session.quiz_question_results && session.quiz_question_results.length > 0 && (
                        <div className="quiz-results">
                          <h4>Quiz Results:</h4>
                          <div className="question-results">
                            {session.quiz_question_results.map((result, index) => (
                              <div key={index} className={`question-result ${result.is_correct ? 'correct' : 'incorrect'}`}>
                                <span>Q{result.question_number}: </span>
                                <span>{result.is_correct ? '✓' : '✗'}</span>
                                <span className="question-type">({result.question_type})</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quiz Performance Tab */}
        {activeTab === 'quiz' && (
          <div className="quiz-section">
            <h2>Quiz Performance by Deck</h2>
            <div className="quiz-performance-list">
              {quizPerformance.map(deck => (
                <div key={`${deck.course_id}:${deck.deck_id}`} className="quiz-deck-card">
                  <div className="deck-header">
                    <h3>{deck.deck_id}</h3>
                    <span className="course-badge">{deck.course_id}</span>
                  </div>
                  <div className="performance-stats">
                    <div className="stat-row">
                      <span>Total Attempts:</span>
                      <strong>{deck.total_attempts}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Average Score:</span>
                      <strong>{deck.average_score_percentage.toFixed(1)}%</strong>
                    </div>
                    <div className="stat-row">
                      <span>Highest Score:</span>
                      <strong>{deck.highest_score_percentage.toFixed(1)}%</strong>
                    </div>
                    <div className="stat-row">
                      <span>Lowest Score:</span>
                      <strong>{deck.lowest_score_percentage.toFixed(1)}%</strong>
                    </div>
                    <div className="stat-row">
                      <span>Average Time:</span>
                      <strong>{formatTime(Math.round(deck.average_time_seconds))}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Feedback Tab */}
        {activeTab === 'feedback' && (
          <div className="feedback-section">
            <h2>Flashcard Feedback Analysis</h2>
            <div className="feedback-summary-list">
              {feedbackSummary.map(item => (
                <div key={item.flashcard_identifier} className="feedback-card">
                  <div 
                    className="feedback-header"
                    onClick={() => toggleFeedbackExpansion(item.flashcard_identifier)}
                  >
                    <div className="feedback-info">
                      <span className="flashcard-id">{item.flashcard_identifier}</span>
                      <span className="feedback-counts">
                        <FaThumbsUp className="like-icon" /> {item.likes}
                        <FaThumbsDown className="dislike-icon" /> {item.dislikes}
                      </span>
                    </div>
                    <div className="feedback-stats">
                      <span className={`net-score ${item.net_score >= 0 ? 'positive' : 'negative'}`}>
                        Net: {item.net_score > 0 ? '+' : ''}{item.net_score}
                      </span>
                      {expandedFeedback.has(item.flashcard_identifier) ? <FaChevronUp /> : <FaChevronDown />}
                    </div>
                  </div>
                  
                  {expandedFeedback.has(item.flashcard_identifier) && (
                    <div className="feedback-details">
                      <h4>Individual Feedback:</h4>
                      <div className="feedback-entries">
                        {feedbackDetails
                          .filter(detail => detail.flashcard_identifier === item.flashcard_identifier)
                          .map(detail => (
                            <div key={detail.feedback_id} className={`feedback-entry ${detail.rating_text}`}>
                              <span className="feedback-user">User: {detail.user_id.substring(0, 8)}...</span>
                              <span className="feedback-rating">
                                {detail.rating === 1 ? <FaThumbsUp className="like" /> : <FaThumbsDown className="dislike" />}
                                {detail.rating_text}
                              </span>
                              <span className="feedback-date">{formatDate(detail.created_at)}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="users-section">
            <h2>All Users ({users.length})</h2>
            <div className="users-list">
              {users.map(user => (
                <div key={user.user_id} className="user-card">
                  <div className="user-info">
                    <div className="user-id">User: {user.user_id}</div>
                    <div className="user-dates">
                      <span>Created: {formatDate(user.created_at)}</span>
                      <span>Last Active: {formatDate(user.last_active)}</span>
                    </div>
                  </div>
                  <div className="user-stats">
                    <div className="user-stat">
                      <span>Decks Studied:</span>
                      <strong>{user.total_decks_studied}</strong>
                    </div>
                    <div className="user-stat">
                      <span>Quiz Attempts:</span>
                      <strong>{user.total_quiz_attempts}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminDashboardView
