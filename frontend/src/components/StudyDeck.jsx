import { useState, useEffect } from 'react'
import Flashcard from './Flashcard'
import './StudyDeck.css'

function StudyDeck({ flashcards, metadata, onStartQuiz }) {
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentCard = flashcards[currentIndex]
  const progress = ((currentIndex + 1) / flashcards.length) * 100

  const handleNext = () => {
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  // Keyboard shortcuts for faster studying
  useEffect(() => {
    const handleKeyDown = (event) => {
      switch (event.code) {
        case 'ArrowRight':
          event.preventDefault()
          handleNext()
          break
        case 'ArrowLeft':
          event.preventDefault()
          handlePrevious()
          break
        default:
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, flashcards.length])

  return (
    <div className="study-deck">
      {/* Minimal Top Navigation */}
      <div className="top-nav">
        <div className="deck-title">
          {metadata.course_name}
        </div>
        <div className="progress-section">
          <span className="progress-counter">
            {currentIndex + 1} / {flashcards.length}
          </span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
        <div className="nav-actions">
          <button 
            className="nav-arrow left"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            title="Previous (←)"
          >
            ←
          </button>
          <button 
            className="nav-arrow right"
            onClick={handleNext}
            disabled={currentIndex === flashcards.length - 1}
            title="Next (→)"
          >
            →
          </button>
        </div>
      </div>

      {/* Main Study Area */}
      <div className="study-main">
        <Flashcard card={currentCard} />
        
        {/* Enhanced Keyboard Shortcuts Hint */}
        <div className="keyboard-hints">
          <span>← → Navigate</span>
          <span>Space Flip</span>
          <span>1-6 Switch Answers</span>
          <span>Tab Cycle Tabs</span>
        </div>
      </div>

      {/* Quiz Section */}
      {onStartQuiz && currentIndex === flashcards.length - 1 && (
        <div className="quiz-section">
          <div className="quiz-prompt">
            <h3>Ready for a Quiz?</h3>
            <p>Test your knowledge with 10 questions</p>
          </div>
          <button className="btn-primary" onClick={onStartQuiz}>
            Start Quiz
          </button>
        </div>
      )}
    </div>
  )
}

export default StudyDeck

