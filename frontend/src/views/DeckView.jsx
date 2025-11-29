import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import StudyDeck from '../components/StudyDeck'
import { trackEvent } from '../utils/amplitude'
import './DeckView.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function DeckView() {
  const { courseId, lectureId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [flashcardsData, setFlashcardsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [initialCardId, setInitialCardId] = useState(null)
  
  // Track if session has been initialized for this specific deck
  const sessionInitialized = useRef(false)
  const studyStartTime = useRef(null)
  const currentDeckRef = useRef(null)

  // Finish study session
  const finishStudySession = useCallback(async () => {
    if (!studyStartTime.current) return
    
      const studyDurationSeconds = Math.round((Date.now() - studyStartTime.current) / 1000)
      
    // Track flashcard session end in Amplitude
    trackEvent('Flashcard Session Ended', {
      courseId,
      lectureId,
      durationSeconds: studyDurationSeconds
      })
      
      console.log(`Study session completed. Duration: ${studyDurationSeconds}s`)
  }, [courseId, lectureId])

  // Handle quiz start
  const handleStartQuiz = useCallback(async () => {
    await finishStudySession()
    
    navigate(`/courses/${courseId}/${lectureId}/quiz`, {
      state: { sessionId }
    })
  }, [finishStudySession, navigate, courseId, lectureId, sessionId])

  // Main effect: Load flashcards and initialize session
  useEffect(() => {
    const deckKey = `${courseId}-${lectureId}`
    
    // Reset state if we're viewing a different deck
    if (currentDeckRef.current !== deckKey) {
      currentDeckRef.current = deckKey
      sessionInitialized.current = false
      setSessionId(null)
      studyStartTime.current = null
      setFlashcardsData(null)
      setLoading(true)
      setError(null)
    }
    
    // Skip if already initialized for this deck
    if (sessionInitialized.current) return
    
    const initializeDeck = async () => {
      try {
        // Load flashcards from backend (PostgreSQL-backed lectures table)
        const flashcardsPath = `${API_BASE_URL}/api/v1/content/lectures/${lectureId}/flashcards`
        const response = await fetch(flashcardsPath)

        console.log('Fetching flashcards from:', flashcardsPath)
        
        if (!response.ok) {
          throw new Error('Flashcards not found')
        }
        
        const data = await response.json()
        setFlashcardsData(data)
        
        // Check for deep link to specific flashcard
        const cardIdParam = searchParams.get('card')
        if (cardIdParam && data.flashcards) {
          const cardIndex = data.flashcards.findIndex(card => card.flashcard_id === cardIdParam)
          if (cardIndex !== -1) {
            setInitialCardId(cardIdParam)
          }
        }
        
        // Track flashcard session start in Amplitude
        studyStartTime.current = Date.now()
        trackEvent('Flashcard Session Started', {
            courseId,
          lectureId,
          totalCards: data.flashcards?.length || 0
        })
        
        setLoading(false)
        sessionInitialized.current = true
      } catch (error) {
        console.error('Error loading flashcards:', error)
        setError(error.message)
        setLoading(false)
      }
    }
    
    initializeDeck()
  }, [courseId, lectureId])

  // Cleanup effect
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (sessionId && studyStartTime.current) {
        const studyDurationSeconds = Math.round((Date.now() - studyStartTime.current) / 1000)
        navigator.sendBeacon(
          `${API_BASE_URL}/api/v1/analytics/session/update`,
          JSON.stringify({
            session_id: sessionId,
            study_duration_seconds: studyDurationSeconds
          })
        )
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      finishStudySession()
    }
  }, [sessionId, finishStudySession])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading flashcards...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>❌ {error}</h2>
        <p>The flashcards for this lecture might not have been generated yet.</p>
        <button onClick={() => navigate(`/courses/${courseId}`)}>
          ← Back to Course
        </button>
      </div>
    )
  }

  return (
    <div className="deck-view">
      <button className="back-button" onClick={() => navigate(`/courses/${courseId}`)}>
        ← Back to Course
      </button>

      <StudyDeck 
        flashcards={flashcardsData.flashcards} 
        metadata={{
          course_name: flashcardsData.course_name,
          lecture_title: flashcardsData.lecture_title,
          total_flashcards: flashcardsData.total_flashcards,
        }}
        onStartQuiz={handleStartQuiz}
        courseId={courseId}
        deckId={lectureId}
        sessionId={sessionId}
        initialCardId={initialCardId}
      />
    </div>
  )
}

export default DeckView