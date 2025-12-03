import { useState, useEffect, useMemo } from 'react'
import Flashcard from './Flashcard'
import { FlashcardChatInput, FlashcardChatModal } from './FlashcardChat'
import './StudyDeck.css'

function StudyDeck({ flashcards, metadata, onStartQuiz, courseId, deckId, sessionId, initialCardId }) {
  const [currentIndex, setCurrentIndex] = useState(() => {
    if (initialCardId) {
      const index = flashcards.findIndex(card => card.flashcard_id === initialCardId)
      return index !== -1 ? index : 0
    }
    return 0
  })
  
  const [showChatModal, setShowChatModal] = useState(false)
  const [initialChatMessage, setInitialChatMessage] = useState('')

  const currentCard = flashcards[currentIndex]
  const progress = ((currentIndex + 1) / flashcards.length) * 100

  // Build flashcard context for chat (question + all answer modes, excluding diagrams)
  const flashcardContext = useMemo(() => {
    if (!currentCard) return null
    return {
      question: currentCard.question || '',
      concise: currentCard.answers?.concise || '',
      analogy: currentCard.answers?.analogy || '',
      eli5: currentCard.answers?.eli5 || '',
      real_world_use_case: currentCard.answers?.real_world_use_case || '',
      common_mistakes: currentCard.answers?.common_mistakes || '',
      example: currentCard.example || ''
    }
  }, [currentCard])

  // Handle opening chat modal with an initial message from the input
  const handleOpenChatModal = (initialMessage = '') => {
    setInitialChatMessage(initialMessage)
    setShowChatModal(true)
  }

  // Close chat modal
  const handleCloseChatModal = () => {
    setShowChatModal(false)
    setInitialChatMessage('')
  }

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
      </div>

      {/* Main Study Area */}
      <div className="study-main">
        <Flashcard 
          card={currentCard} 
          courseId={courseId}
          deckId={deckId}
          index={currentIndex}
          sessionId={sessionId}
        />
        
        {/* Navigation Below Card */}
        <div className="card-navigation">
          <button 
            className="nav-arrow left"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            title="Previous (←)"
          >
            ← Previous
          </button>
          <span className="nav-hint">Think first, then tap to reveal</span>
          <button 
            className="nav-arrow right"
            onClick={handleNext}
            disabled={currentIndex === flashcards.length - 1}
            title="Next (→)"
          >
            Next →
          </button>
        </div>
        
        {/* Enhanced Keyboard Shortcuts Hint */}
        <div className="keyboard-hints">
          <span>← → Navigate</span>
          <span>Space Flip</span>
          <span>1-6 Switch Answers</span>
          <span>Tab Cycle Tabs</span>
        </div>
        
        {/* Flashcard Chat Input */}
        {currentCard && (
          <FlashcardChatInput
            flashcardId={currentCard.flashcard_id || `${deckId}_${currentIndex}`}
            courseId={courseId}
            lectureId={deckId}
            flashcardContext={flashcardContext}
            onOpenModal={handleOpenChatModal}
          />
        )}
      </div>

      {/* Flashcard Chat Modal */}
      <FlashcardChatModal
        isOpen={showChatModal}
        onClose={handleCloseChatModal}
        flashcardId={currentCard?.flashcard_id || `${deckId}_${currentIndex}`}
        courseId={courseId}
        lectureId={deckId}
        flashcardContext={flashcardContext}
        initialMessage={initialChatMessage}
      />

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