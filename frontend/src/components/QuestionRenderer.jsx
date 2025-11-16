import { useState } from 'react'
import DiagramRenderer from './quiz/DiagramRenderer'
import './QuestionRenderer.css'

function QuestionRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  if (!question) return null

  switch (question.type) {
    case 'mcq':
    case 'scenario_mcq':
      return (
        <MCQRenderer 
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'mca':
      return (
        <MCARenderer 
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'sequencing':
      return (
        <SequencingRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'categorization':
      return (
        <CategorizationRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'matching':
      return (
        <MatchingRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'fill_in_the_blank':
      return (
        <FillInTheBlankRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'true_false':
      return (
        <TrueFalseRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    default:
      return <div>Unknown question type: {question.type}</div>
  }
}

// MCQ and Scenario MCQ Renderer
function MCQRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  // correct_answer is now always an array; for MCQ it has 1 element (the option KEY like "A")
  const correctAnswerKey = Array.isArray(question.answer) ? question.answer[0] : question.answer
  
  // Options can be either an array or an object {A: "text", B: "text", ...}
  const optionsArray = Array.isArray(question.options) 
    ? question.options 
    : Object.entries(question.options || {})
  
  const isObjectOptions = !Array.isArray(question.options)
  
  return (
    <div className="question-container mcq-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      {question.scenario && (
        <div className="scenario-box">
          <strong>Scenario:</strong>
          <p>{question.scenario}</p>
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
        <p className="question-type-indicator mcq-indicator">Single Choice - Select one answer</p>
      </div>
      
      <div className="options-list">
        {optionsArray.map((option, index) => {
          // If options is an object, option is [key, value] tuple; otherwise it's just the text
          const optionKey = isObjectOptions ? option[0] : option
          const optionText = isObjectOptions ? option[1] : option
          const optionValue = isObjectOptions ? optionKey : optionText
          const isSelected = userAnswer === optionValue
          const isCorrect = isObjectOptions ? optionKey === correctAnswerKey : optionText === correctAnswerKey
          
          return (
            <label 
            key={index}
              className={`option-item radio-option ${isSelected && !showFeedback ? 'selected' : ''} ${
                showFeedback && isCorrect ? 'correct' : ''
              } ${showFeedback && isSelected && !isCorrect ? 'incorrect' : ''}`}
            >
              <div className="radio-wrapper">
                <input
                  type="radio"
                  name={`question-${question.question_id || index}`}
                  value={optionValue}
                  checked={isSelected}
                  onChange={() => !disabled && onAnswerChange(optionValue)}
                  disabled={disabled}
                  className="option-radio"
                />
                <span className="radio-custom"></span>
              </div>
            <div className="option-content">
                {isObjectOptions && <span className="option-letter">{optionKey}. </span>}
                {optionText}
            </div>
            </label>
          )
        })}
      </div>
    </div>
  )
}

// MCA (Multiple Correct Answers) Renderer
function MCARenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  
  // Ensure userAnswer is always an array (of option KEYS like ["A", "C"])
  const selectedAnswers = Array.isArray(userAnswer) ? userAnswer : []
  
  // correct_answer is now always an array of option KEYS (e.g., ["A", "C"])
  const correctAnswers = Array.isArray(question.answer) ? question.answer : []
  
  // Options can be either an array or an object {A: "text", B: "text", ...}
  const optionsArray = Array.isArray(question.options) 
    ? question.options 
    : Object.entries(question.options || {})
  
  const isObjectOptions = !Array.isArray(question.options)
  
  console.log("🟣 MCA isObjectOptions:", isObjectOptions);
  console.log("🟣 MCA optionsArray:", optionsArray);
  console.log("🟣 MCA selectedAnswers:", selectedAnswers)
  
  const toggleOption = (optionKey) => {
    if (disabled) return
    
    const newAnswers = selectedAnswers.includes(optionKey)
      ? selectedAnswers.filter(ans => ans !== optionKey)
      : [...selectedAnswers, optionKey]
    
    onAnswerChange(newAnswers)
  }
  
  const isCorrectAnswer = (optionKey) => {
    return correctAnswers.includes(optionKey)
  }
  
  return (
    <div className="question-container mca-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      {question.scenario && (
        <div className="scenario-box">
          <strong>Scenario:</strong>
          <p>{question.scenario}</p>
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
        <p className="question-type-indicator mca-indicator">Multiple Choice - Select all that apply</p>
      </div>
      
      <div className="options-list">
        {optionsArray.map((option, index) => {
          // If options is an object, option is [key, value] tuple; otherwise it's just the text
          const optionKey = isObjectOptions ? option[0] : option
          const optionText = isObjectOptions ? option[1] : option
          const isSelected = selectedAnswers.includes(optionKey)
          const isCorrect = isCorrectAnswer(optionKey)
          
          return (
            <label 
              key={index}
              className={`option-item checkbox-option ${isSelected ? 'selected' : ''} ${
                showFeedback && isCorrect && isSelected ? 'correct' : ''
              } ${showFeedback && isSelected && !isCorrect ? 'incorrect' : ''} ${
                showFeedback && !isSelected && isCorrect ? 'missed' : ''
              }`}
            >
              <div className="checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={(e) => {
                    e.stopPropagation()
                    toggleOption(optionKey)
                  }}
                  disabled={disabled}
                  className="option-checkbox"
                />
                <span className="checkbox-custom"></span>
              </div>
              <div className="option-content">
                {isObjectOptions && <span className="option-letter">{optionKey}. </span>}
                {optionText}
              </div>
            </label>
          )
        })}
      </div>
      
      {showFeedback && (
        <div className="mca-feedback">
          <p className="selected-count">
            You selected {selectedAnswers.length} option(s). 
            {Array.isArray(question.answer) && ` Correct answer has ${question.answer.length} option(s).`}
          </p>
        </div>
      )}
    </div>
  )
}

// Sequencing Renderer
// eslint-disable-next-line no-unused-vars
function SequencingRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const [items, setItems] = useState(userAnswer || [...(question.items || [])])
  const [draggedIndex, setDraggedIndex] = useState(null)
  
  const moveItem = (fromIndex, toIndex) => {
    if (disabled) return
    const newItems = [...items]
    const [removed] = newItems.splice(fromIndex, 1)
    newItems.splice(toIndex, 0, removed)
    setItems(newItems)
    onAnswerChange(newItems)
  }

  const handleDragStart = (e, index) => {
    if (disabled) return
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/html', e.target)
  }

  const handleDragOver = (e) => {
    if (disabled) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e, dropIndex) => {
    if (disabled) return
    e.preventDefault()
    
    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      moveItem(draggedIndex, dropIndex)
    }
    setDraggedIndex(null)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
  }

  return (
    <div className="question-container sequencing-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
        <p className="instruction">Drag to reorder or use arrows to arrange in correct sequence</p>
      </div>
      
      <div className="sequencing-list">
        {items.map((item, index) => (
          <div 
            key={index} 
            className={`sequence-item ${draggedIndex === index ? 'dragging' : ''}`}
            draggable={!disabled}
            onDragStart={(e) => handleDragStart(e, index)}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, index)}
            onDragEnd={handleDragEnd}
          >
            <span className="sequence-handle">⋮⋮</span>
            <span className="sequence-number">{index + 1}</span>
            <span className="sequence-content">{item}</span>
            <div className="sequence-controls">
              <button
                onClick={() => moveItem(index, Math.max(0, index - 1))}
                disabled={disabled || index === 0}
                className="move-btn"
              >
                ▲
              </button>
              <button
                onClick={() => moveItem(index, Math.min(items.length - 1, index + 1))}
                disabled={disabled || index === items.length - 1}
                className="move-btn"
              >
                ▼
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Categorization Renderer
// eslint-disable-next-line no-unused-vars
function CategorizationRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const [categorization, setCategorization] = useState(userAnswer || {})
  
  const handleCategoryChange = (item, category) => {
    if (disabled) return
    const newCategorization = { ...categorization }
    
    // Remove item from all categories
    Object.keys(newCategorization).forEach(cat => {
      newCategorization[cat] = (newCategorization[cat] || []).filter(i => i !== item)
    })
    
    // Add to new category
    if (!newCategorization[category]) {
      newCategorization[category] = []
    }
    newCategorization[category].push(item)
    
    setCategorization(newCategorization)
    onAnswerChange(newCategorization)
  }

  const getItemCategory = (item) => {
    for (const cat of question.categories || []) {
      if ((categorization[cat] || []).includes(item)) {
        return cat
      }
    }
    return null
  }

  return (
    <div className="question-container categorization-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="categorization-grid">
        <div className="items-list">
          <h4>Items to Categorize:</h4>
          {question.items && question.items.map((item, index) => (
            <div key={index} className="cat-item">
              <span>{item}</span>
              <select
                value={getItemCategory(item) || ''}
                onChange={(e) => handleCategoryChange(item, e.target.value)}
                disabled={disabled}
                className="category-select"
              >
                <option value="">Select category...</option>
                {question.categories && question.categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
        
        <div className="categories-display">
          {question.categories && question.categories.map(category => (
            <div key={category} className="category-box">
              <h4>{category}</h4>
              <div className="category-items">
                {(categorization[category] || []).map((item, idx) => (
                  <div key={idx} className="categorized-item">{item}</div>
                ))}
                {(!categorization[category] || categorization[category].length === 0) && (
                  <div className="empty-category">No items yet</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Matching Renderer
// eslint-disable-next-line no-unused-vars
function MatchingRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const [matches, setMatches] = useState(userAnswer || [])
  
  const handleMatch = (premise, response) => {
    if (disabled) return
    const premiseNum = premise.split('.')[0]
    // The response is the full text, no need to split
    const matchPair = `${premiseNum}-${response.split('.')[0]}`
    
    // Remove any existing match for this premise
    const newMatches = matches.filter(m => !m.startsWith(premiseNum + '-'))
    newMatches.push(matchPair)
    
    setMatches(newMatches)
    // Pass up the full response text for checking
    const answerForCheck = newMatches.map(match => {
      const [pNum, rLetter] = match.split('-')
      return `${pNum}-${rLetter}`
    }).sort()

    onAnswerChange(answerForCheck)
  }

  const getMatchForPremise = (premise) => {
    const premiseNum = premise.split('.')[0]
    const match = matches.find(m => m.startsWith(premiseNum + '-'))
    if (!match) return null
    
    const responseLetter = match.split('-')[1]
    return question.responses.find(r => r.startsWith(responseLetter + '.'))
  }

  return (
    <div className="question-container matching-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="matching-grid">
        <div className="premises-column">
          <h4>Match these:</h4>
          {question.premises && question.premises.map((premise, index) => (
            <div key={index} className="premise-item">
              <span className="premise-text">{premise}</span>
              <select
                value={getMatchForPremise(premise) || ''}
                onChange={(e) => handleMatch(premise, e.target.value)}
                disabled={disabled}
                className="match-select"
              >
                <option value="">Select match...</option>
                {question.responses && question.responses.map((response, idx) => (
                  <option key={idx} value={response}>{response}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </div>
      
      <div className="matches-summary">
        <h4>Your Matches:</h4>
        {matches.length > 0 ? (
          <div className="matches-list">
            {matches.map((match, idx) => (
              <span key={idx} className="match-pair">{match}</span>
            ))}
          </div>
        ) : (
          <p>No matches selected yet</p>
        )}
      </div>
    </div>
  )
}

// Fill in the Blank Renderer
function FillInTheBlankRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const parts = question.question.split('________')
  
  return (
    <div className="question-container fill-in-the-blank-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      <div className="question-text">
        <h3>
          {parts.map((part, index) => (
            <span key={index}>
              {part}
              {index < parts.length - 1 && (
                <input
                  type="text"
                  value={userAnswer || ''}
                  onChange={(e) => onAnswerChange(e.target.value)}
                  disabled={disabled}
                  className={`blank-input ${showFeedback ? (userAnswer?.trim().toLowerCase() === question.answer.trim().toLowerCase() ? 'correct' : 'incorrect') : ''}`}
                  placeholder="Type your answer"
                />
              )}
            </span>
          ))}
        </h3>
      </div>
      
      {showFeedback && userAnswer?.trim().toLowerCase() !== question.answer.trim().toLowerCase() && (
        <div className="correct-answer-hint">
          <strong>Correct Answer:</strong> {question.answer}
        </div>
      )}
    </div>
  )
}

// True/False Renderer
function TrueFalseRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const options = ['True', 'False']
  
  return (
    <div className="question-container true-false-question">
      {/* Question Visual */}
      {question.question_visual && question.question_visual_type && question.question_visual_type !== 'None' && (
        <div className="question-visual-container">
          <DiagramRenderer 
            diagram={question.question_visual}
            diagramType={question.question_visual_type}
            altText="Question diagram"
          />
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="true-false-options">
        {options.map((option) => (
          <button
            key={option}
            className={`true-false-btn ${userAnswer === option ? 'selected' : ''} ${
              showFeedback && option === question.answer ? 'correct' : ''
            } ${showFeedback && userAnswer === option && option !== question.answer ? 'incorrect' : ''}`}
            onClick={() => !disabled && onAnswerChange(option)}
            disabled={disabled}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  )
}

export default QuestionRenderer

