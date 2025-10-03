import { useState, useEffect } from 'react'
import './App.css'
import StudyDeck from './components/StudyDeck'
import Quiz from './components/Quiz'
import Scorecard from './components/Scorecard'

function App() {
  const [flashcardsData, setFlashcardsData] = useState(null)
  const [stage, setStage] = useState('loading') // loading, study, quiz, results
  const [quizResults, setQuizResults] = useState([])

  useEffect(() => {
    // Load the flashcards JSON
    fetch('/MIS_lec_1-3_cognitive_flashcards.json')
      .then(response => response.json())
      .then(data => {
        setFlashcardsData(data)
        setStage('study')
      })
      .catch(error => {
        console.error('Error loading flashcards:', error)
      })
  }, [])

  const handleStudyComplete = () => {
    setStage('quiz')
  }

  const handleQuizComplete = (results) => {
    setQuizResults(results)
    setStage('results')
  }

  if (stage === 'loading') {
    return (
      <div className="app-container loading">
        <div className="loading-spinner"></div>
        <p>Loading your study session...</p>
      </div>
    )
  }

  return (
    <div className="app-container">
      {stage === 'study' && (
        <StudyDeck 
          flashcards={flashcardsData.flashcards} 
          metadata={flashcardsData.metadata}
          onComplete={handleStudyComplete}
        />
      )}
      {stage === 'quiz' && (
        <Quiz 
          flashcards={flashcardsData.flashcards}
          onComplete={handleQuizComplete}
        />
      )}
      {stage === 'results' && (
        <Scorecard 
          results={quizResults}
          flashcards={flashcardsData.flashcards}
        />
      )}
    </div>
  )
}

export default App
