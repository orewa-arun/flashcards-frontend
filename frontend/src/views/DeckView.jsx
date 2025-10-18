import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import StudyDeck from '../components/StudyDeck'
import './DeckView.css'

function DeckView() {
  const { courseId, lectureId } = useParams()
  const navigate = useNavigate()
  const [flashcardsData, setFlashcardsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Construct the path to the flashcards JSON file
    const flashcardsPath = `/courses/${courseId}/cognitive_flashcards/${lectureId}/${lectureId}_cognitive_flashcards.json`
    
    fetch(flashcardsPath)
      .then(response => {
        if (!response.ok) {
          throw new Error('Flashcards not found')
        }
        return response.json()
      })
      .then(data => {
        setFlashcardsData(data)
        setLoading(false)
      })
      .catch(error => {
        console.error('Error loading flashcards:', error)
        setError(error.message)
        setLoading(false)
      })
  }, [courseId, lectureId])

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

  const handleStartQuiz = () => {
    navigate(`/courses/${courseId}/${lectureId}/quiz`)
  }

  return (
    <div className="deck-view">
      <button className="back-button" onClick={() => navigate(`/courses/${courseId}`)}>
        ← Back to Course
      </button>

      <StudyDeck 
        flashcards={flashcardsData.flashcards} 
        metadata={flashcardsData.metadata}
        onStartQuiz={handleStartQuiz}
      />
    </div>
  )
}

export default DeckView

