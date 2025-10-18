import { useState } from 'react'
import Flashcard from './Flashcard'
import DifficultyRating from './DifficultyRating'
import './StudyDeck.css'

function StudyDeck({ flashcards, metadata, onStartQuiz }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showRating, setShowRating] = useState(false)

  const currentCard = flashcards[currentIndex]
  const progress = ((currentIndex + 1) / flashcards.length) * 100

  const handleNext = () => {
    setShowRating(true)
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      setShowRating(false)
    }
  }

  const handleRating = () => {
    // Rating is recorded but not used for now
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setShowRating(false)
    }
  }

  return (
    <div className="study-deck">
      <div className="study-header">
        <h1>📚 {metadata.course_name}</h1>
        <p className="flashcard-intro">Interactive Flashcards - They help you remember better!</p>
        <div className="progress-info">
          <span className="card-counter">
            Card {currentIndex + 1} of {flashcards.length}
          </span>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      {!showRating ? (
        <div className="flashcard-container">
          <Flashcard card={currentCard} />
          
          <div className="navigation-controls">
            <button 
              className="nav-btn prev-btn"
              onClick={handlePrevious}
              disabled={currentIndex === 0}
            >
              ← Previous
            </button>
            <button 
              className="nav-btn next-btn"
              onClick={handleNext}
            >
              Next →
            </button>
          </div>
        </div>
      ) : (
        <DifficultyRating onRate={handleRating} />
      )}

      {currentCard.tags && (
        <div className="card-tags">
          {currentCard.tags.map((tag, index) => (
            <span key={index} className="tag">{tag}</span>
          ))}
        </div>
      )}

      {onStartQuiz && (
        <div className="quiz-section">
          <div className="quiz-prompt">
            <h3>📝 Ready to Test Your Knowledge?</h3>
            <p>Take a quiz with 10 intelligently selected questions based on relevance scores</p>
          </div>
          <button className="start-quiz-btn" onClick={onStartQuiz}>
            Start Quiz →
          </button>
        </div>
      )}
    </div>
  )
}

export default StudyDeck

