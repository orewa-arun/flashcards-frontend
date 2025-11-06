import { useState, useEffect } from 'react'
import QuestionRenderer from './QuestionRenderer'
import './Quiz.css'

function Quiz({ flashcards, onComplete }) {
  const [allQuestions, setAllQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState(null)
  const [results, setResults] = useState([])
  const [showTransition, setShowTransition] = useState(true)
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false)
  const [isCorrect, setIsCorrect] = useState(false)

  useEffect(() => {
    console.log("🚀 QUIZ DIAGNOSTIC: Loading flashcards...");
    console.log("🚀 Flashcards count:", flashcards?.length);
    
    // Collect all recall questions from all flashcards
    const questions = []
    flashcards.forEach(card => {
      if (card.recall_questions && card.recall_questions.length > 0) {
        card.recall_questions.forEach(q => {
          console.log("📝 Found question - Type:", q.type, "Question:", q.question?.substring(0, 50));
          
          // Sanitize MCQ options to remove duplicates
          if (q.type === 'mcq' && q.options && Array.isArray(q.options)) {
            q.options = [...new Set(q.options)]
          }
          questions.push({
            ...q,
            cardContext: card.context,
            cardType: card.type
          })
        })
      }
    })
    
    console.log("📊 Total questions collected:", questions.length);
    
    // Shuffle all questions
    const shuffled = questions.sort(() => Math.random() - 0.5)
    
    // Select only 10 random questions to keep the quiz focused
    const selectedQuestions = shuffled.slice(0, 10)
    console.log("✅ Selected questions for quiz:", selectedQuestions.length);
    console.log("✅ First question:", JSON.stringify(selectedQuestions[0], null, 2));
    
    setAllQuestions(selectedQuestions)

    // Show transition for 2 seconds
    setTimeout(() => setShowTransition(false), 2000)
  }, [flashcards])

  const currentQuestion = allQuestions[currentQuestionIndex]
  
  console.log("🎯 CURRENT QUESTION:", currentQuestionIndex, currentQuestion);

  // Reset answer when question changes
  useEffect(() => {
    console.log("🔄 Question changed - Index:", currentQuestionIndex, "Type:", currentQuestion?.type);
    
    // Initialize userAnswer based on question type
    if (currentQuestion?.type === 'mca') {
      console.log("🟣 Initializing MCA question with empty array");
      setUserAnswer([])  // Empty array for multiple choice
    } else {
      console.log("🔵 Initializing MCQ question with null");
      setUserAnswer(null)  // null for single choice
    }
  }, [currentQuestionIndex, currentQuestion?.type])

  const handleSubmit = () => {
    // Check if user has provided an answer
    // For MCA questions, allow empty arrays but not null/undefined
    if (currentQuestion.type === 'mca') {
      if (!Array.isArray(userAnswer)) return
    } else {
    if (!userAnswer && userAnswer !== false && userAnswer !== 0) return
    }

    // Two-stage flow: Submit Answer → Show Feedback → Next Question
    if (!isAnswerSubmitted) {
      // Stage 1: Submit and check answer
      const correct = checkAnswer()
      setIsCorrect(correct)
      setIsAnswerSubmitted(true)
      
      // Save result
      const result = {
        question: currentQuestion,
        userAnswer: userAnswer,
        isCorrect: correct,
        context: currentQuestion.cardContext
      }
      setResults([...results, result])
    } else {
      // Stage 2: Move to next question
      if (currentQuestionIndex < allQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        // userAnswer will be reset by useEffect based on next question type
        setIsAnswerSubmitted(false)
        setIsCorrect(false)
      } else {
        onComplete([...results])
      }
    }
  }

  const checkAnswer = () => {
    const correctAnswer = currentQuestion.answer
    
    // Handle different question types
    switch (currentQuestion.type) {
      case 'mcq':
      case 'scenario_mcq':
        // correct_answer is now always an array; for MCQ it has 1 element
        const correctMCQ = Array.isArray(correctAnswer) ? correctAnswer[0] : correctAnswer
        return correctMCQ.toString().toLowerCase().trim() === userAnswer.toString().toLowerCase().trim()
      
      case 'mca':
        // correct_answer is an array with 2+ elements for MCA
        if (Array.isArray(userAnswer) && Array.isArray(correctAnswer)) {
          const sortedUser = [...userAnswer].sort()
          const sortedCorrect = [...correctAnswer].sort()
          return JSON.stringify(sortedUser) === JSON.stringify(sortedCorrect)
        }
        return false
      
      case 'sequencing':
        return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer)
      
      case 'categorization':
        return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer)
      
      case 'matching':
        // Matching answers are arrays of pairs
        if (Array.isArray(userAnswer) && Array.isArray(correctAnswer)) {
          const sortedUser = [...userAnswer].sort()
          const sortedCorrect = [...correctAnswer].sort()
          return JSON.stringify(sortedUser) === JSON.stringify(sortedCorrect)
        }
        return false
      
      case 'true_false':
        return correctAnswer.toString().toLowerCase() === userAnswer.toString().toLowerCase()
      
      case 'fill_in_the_blank':
        return correctAnswer.toString().toLowerCase().trim() === userAnswer.toString().toLowerCase().trim()
      
      default:
        return correctAnswer.toString().toLowerCase().trim() === userAnswer.toString().toLowerCase().trim()
    }
  }

  if (showTransition) {
    return (
      <div className="quiz-transition">
        <div className="transition-content">
          <h1>🎯 Quiz Time!</h1>
          <p>Get ready to test your knowledge</p>
          <div className="loading-spinner"></div>
        </div>
      </div>
    )
  }

  if (allQuestions.length === 0) {
    return <div className="quiz">No questions available</div>
  }

  return (
    <div className="quiz">
      <div className="quiz-header">
        <h1>📝 Quiz</h1>
        <div className="quiz-progress">
          Question {currentQuestionIndex + 1} of {allQuestions.length}
        </div>
      </div>

      <div className="question-card">
        <div className="question-type-badge">{currentQuestion.type.replace('_', ' ')}</div>
        
        <QuestionRenderer
          question={currentQuestion}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={isAnswerSubmitted}
          disabled={isAnswerSubmitted}
        />

        {isAnswerSubmitted && (
          <div className={`feedback-message ${isCorrect ? 'correct-feedback' : 'incorrect-feedback'}`}>
            {isCorrect ? (
              <span>✅ Correct!</span>
            ) : (
              <span>❌ Incorrect</span>
            )}
          </div>
        )}

        <button 
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!userAnswer && userAnswer !== false && userAnswer !== 0}
        >
          {isAnswerSubmitted 
            ? (currentQuestionIndex < allQuestions.length - 1 ? 'Next Question →' : 'Finish Quiz 🎉')
            : 'Submit Answer'
          }
        </button>
      </div>
    </div>
  )
}

export default Quiz

