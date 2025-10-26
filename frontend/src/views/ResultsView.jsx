import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import { calculateScore } from '../utils/quizUtils'
import { trackQuizResult } from '../api/analytics'
import './ResultsView.css'

function ResultsView() {
  const location = useLocation()
  const navigate = useNavigate()
  const { courseId, lectureId } = useParams()
  const { results, total, sessionId, quizTime } = location.state || { 
    results: [], 
    total: 0, 
    sessionId: null, 
    quizTime: 0 
  }

  // Save quiz result to the database for quiz history
  useEffect(() => {
    if (results && results.length > 0) {
      const correctCount = results.filter(r => r.isCorrect).length
      
      results.forEach(result => {
        result.questionResult.question = result.question;
      });

      const questionResultsForApi = results.map(r => r.questionResult).filter(Boolean)

      // console.log("location state", location.state);
      // console.log("results", results);
      // console.log("questionResultsForApi", questionResultsForApi);

      trackQuizResult({
        deckId: lectureId,
        courseId: courseId,
        score: correctCount,
        totalQuestions: total,
        timeTaken: quizTime || 0,
        questionResults: questionResultsForApi,
      }).catch(error => {
        console.error("Failed to submit quiz result:", error)
      })
    }
  }, [results, total, sessionId, lectureId, courseId, quizTime])

  if (!results || results.length === 0) {
    return (
      <div className="error-container">
        <h2>No results available</h2>
        <button onClick={() => navigate(`/courses/${courseId}/${lectureId}`)}>
          ← Back to Study
        </button>
      </div>
    )
  }

  const score = calculateScore(results)
  const correctCount = results.filter(r => r.isCorrect).length

  const getScoreColor = () => {
    if (score >= 80) return '#28a745'
    if (score >= 60) return '#ffc107'
    return '#dc3545'
  }

  const getScoreMessage = () => {
    if (score >= 90) return 'Excellent! 🎉'
    if (score >= 80) return 'Great job! 👏'
    if (score >= 70) return 'Good work! 👍'
    if (score >= 60) return 'Keep practicing! 📚'
    return 'Review the material and try again! 💪'
  }

  return (
    <div className="results-view">
      <div className="results-header">
        <h1>Quiz Results</h1>
      </div>

      <div className="score-card">
        <div className="score-circle" style={{ borderColor: getScoreColor() }}>
          <div className="score-value" style={{ color: getScoreColor() }}>
            {score}%
          </div>
          <div className="score-fraction">
            {correctCount} / {total}
          </div>
        </div>
        <div className="score-message">{getScoreMessage()}</div>
      </div>

      <div className="results-breakdown">
        <h2>Question Breakdown</h2>
        <div className="questions-list">
          {results.map((result, index) => (
            <div key={index} className={`result-item ${result.isCorrect ? 'correct' : 'incorrect'}`}>
              <div className="result-header">
                <span className="result-number">Question {index + 1}</span>
                <span className={`result-status ${result.isCorrect ? 'correct' : 'incorrect'}`}>
                  {result.isCorrect ? '✓ Correct' : '✗ Incorrect'}
                </span>
              </div>
              
              <div className="result-question">
                <strong>Q:</strong> {result.question.question}
              </div>
              
              <div className="result-answers">
                <div className="your-answer">
                  <strong>Your Answer:</strong>
                  <span className="answer-value">
                    {JSON.stringify(result.userAnswer).replace(/["{}\[\]]/g, '')}
                  </span>
                </div>
                <div className="correct-answer">
                  <strong>Correct Answer:</strong>
                  <span className="answer-value">
                    {JSON.stringify(result.question.answer).replace(/["{}\[\]]/g, '')}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="results-actions">
        <button 
          className="btn-secondary"
          onClick={() => navigate(`/courses/${courseId}/${lectureId}`)}
        >
          ← Back to Study
        </button>
        <button 
          className="btn-primary"
          onClick={() => navigate(`/courses/${courseId}/${lectureId}/quiz`)}
        >
          Retry Quiz
        </button>
      </div>
    </div>
  )
}

export default ResultsView

