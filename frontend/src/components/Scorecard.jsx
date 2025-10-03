import { useMemo } from 'react'
import './Scorecard.css'

function Scorecard({ results, flashcards }) {
  const stats = useMemo(() => {
    const totalQuestions = results.length
    const correctAnswers = results.filter(r => r.isCorrect).length
    const percentage = ((correctAnswers / totalQuestions) * 100).toFixed(1)

    // Group by context to show performance breakdown
    const contextPerformance = {}
    results.forEach(result => {
      const context = result.context || 'General'
      if (!contextPerformance[context]) {
        contextPerformance[context] = {
          correct: 0,
          total: 0
        }
      }
      contextPerformance[context].total++
      if (result.isCorrect) {
        contextPerformance[context].correct++
      }
    })

    // Calculate percentage for each context
    const contextStats = Object.entries(contextPerformance).map(([context, stats]) => ({
      context,
      correct: stats.correct,
      total: stats.total,
      percentage: ((stats.correct / stats.total) * 100).toFixed(1)
    })).sort((a, b) => b.percentage - a.percentage)

    return {
      totalQuestions,
      correctAnswers,
      percentage,
      contextStats
    }
  }, [results])

  const getPerformanceEmoji = (percentage) => {
    if (percentage >= 90) return '🌟'
    if (percentage >= 75) return '🎉'
    if (percentage >= 60) return '👍'
    if (percentage >= 50) return '💪'
    return '📚'
  }

  const getPerformanceMessage = (percentage) => {
    if (percentage >= 90) return 'Outstanding!'
    if (percentage >= 75) return 'Great job!'
    if (percentage >= 60) return 'Good work!'
    if (percentage >= 50) return 'Keep practicing!'
    return 'Review and try again!'
  }

  return (
    <div className="scorecard">
      <div className="scorecard-header">
        <h1>📊 Your Results</h1>
      </div>

      <div className="overall-score">
        <div className="score-circle">
          <span className="score-emoji">{getPerformanceEmoji(stats.percentage)}</span>
          <span className="score-number">{stats.percentage}%</span>
          <span className="score-detail">
            {stats.correctAnswers} / {stats.totalQuestions} correct
          </span>
        </div>
        <h2 className="performance-message">{getPerformanceMessage(stats.percentage)}</h2>
      </div>

      <div className="context-breakdown">
        <h3>Performance by Topic</h3>
        <div className="context-list">
          {stats.contextStats.map((contextStat, index) => (
            <div key={index} className="context-item">
              <div className="context-header">
                <span className="context-name">{contextStat.context}</span>
                <span className="context-score">
                  {contextStat.correct}/{contextStat.total}
                </span>
              </div>
              <div className="context-bar">
                <div 
                  className="context-fill"
                  style={{ 
                    width: `${contextStat.percentage}%`,
                    backgroundColor: contextStat.percentage >= 75 ? '#4caf50' : 
                                    contextStat.percentage >= 50 ? '#ff9800' : '#f44336'
                  }}
                >
                  <span className="context-percentage">{contextStat.percentage}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="strong-areas">
        <h3>Your Strengths</h3>
        <div className="areas-list">
          {stats.contextStats
            .filter(cs => cs.percentage >= 75)
            .map((cs, index) => (
              <span key={index} className="strength-badge">
                ✅ {cs.context}
              </span>
            ))}
          {stats.contextStats.filter(cs => cs.percentage >= 75).length === 0 && (
            <p className="no-strengths">Keep studying to build your strengths!</p>
          )}
        </div>
      </div>

      <div className="completion-message">
        <h1 className="yay-message">🎊 Yay!, you have completed the study session! 🎊</h1>
      </div>

      <button 
        className="restart-btn"
        onClick={() => window.location.reload()}
      >
        Start New Session
      </button>
    </div>
  )
}

export default Scorecard

