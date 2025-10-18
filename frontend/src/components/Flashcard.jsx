import { useState, useEffect, useMemo } from 'react'
import { FaLightbulb } from 'react-icons/fa'
import mermaid from 'mermaid'
import './Flashcard.css'

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
})

const answerTypes = [
  { key: 'concise', label: 'Concise' },
  { key: 'analogy', label: 'Analogy' },
  { key: 'eli5', label: 'ELI5' },
  { key: 'real_world_use_case', label: 'Use Case' },
  { key: 'common_mistakes', label: 'Mistakes' }
];

function Flashcard({ card }) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [showExample, setShowExample] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState('concise');
  
  // Generate a stable unique ID for this card's mermaid diagram using useMemo
  const uniqueDiagramId = useMemo(() => {
    return `mermaid-diagram-${card.question.substring(0, 20).replace(/[^a-zA-Z0-9]/g, '')}-${Math.random().toString(36).substr(2, 9)}`
  }, [card.question])

  // Effect to reset state when card changes
  useEffect(() => {
    setIsFlipped(false);
    setShowExample(false);
    setSelectedAnswer('concise');
  }, [card]);

  useEffect(() => {
    // Render mermaid diagram when card is flipped to answer side and has diagram code
    if (isFlipped && card.mermaid_code && card.mermaid_code.trim() !== '') {
      const renderDiagram = async () => {
        try {
          const mermaidContainer = document.getElementById(uniqueDiagramId)
          if (mermaidContainer) {
            // Clear previous content
            mermaidContainer.innerHTML = ''
            // Generate unique ID for this render
            const renderId = `mermaid-svg-${Date.now()}`
            const { svg } = await mermaid.render(renderId, card.mermaid_code)
            mermaidContainer.innerHTML = svg
            console.log('Mermaid diagram rendered successfully for:', card.question.substring(0, 30))
          } else {
            console.warn('Mermaid container not found:', uniqueDiagramId)
          }
        } catch (e) {
          console.error('Mermaid rendering error:', e)
          console.error('Failed diagram code:', card.mermaid_code)
        }
      }
      
      // Small delay to ensure DOM is ready
      setTimeout(renderDiagram, 150)
    }
  }, [isFlipped, card.mermaid_code, uniqueDiagramId, card.question])

  const handleCardClick = (e) => {
    // Don't flip if clicking on buttons or diagram
    if (e.target.closest('.example-button') || e.target.closest('.mermaid-diagram-container') || e.target.closest('.answer-selector')) {
      return
    }
    setIsFlipped(!isFlipped)
  }

  const handleExampleClick = (e) => {
    e.stopPropagation()
    setShowExample(!showExample)
  }

  return (
    <div className="flashcard-wrapper">
      <div 
        className={`flashcard ${isFlipped ? 'flipped' : ''}`}
        onClick={handleCardClick}
      >
        <div className="flashcard-front">
          <div className="card-content">
            <div className="card-type-badge">{card.type}</div>
            <h2>Question</h2>
            <p className="card-text">{card.question}</p>
          </div>
        </div>
        
        <div className="flashcard-back">
          <div className="card-content">
            <div className="card-type-badge">{card.type}</div>
            <h2>Answer</h2>
            <div className="answer-selector">
              {answerTypes.map(type => (
                <button
                  key={type.key}
                  className={`answer-type-btn ${selectedAnswer === type.key ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAnswer(type.key);
                  }}
                >
                  {type.label}
                </button>
              ))}
            </div>
            <p className="card-text answer-text">
              {card.answers && card.answers[selectedAnswer]}
            </p>
            
            {/* Mermaid Diagram Container */}
            {card.mermaid_code && card.mermaid_code.trim() !== '' && (
              <div id={uniqueDiagramId} className="mermaid-diagram-container">
                {/* Mermaid will render the SVG diagram here */}
              </div>
            )}

            {/* Example Button - only on the back */}
            {card.example && (
              <button 
                className="example-button"
                onClick={handleExampleClick}
                title="View example"
              >
                <FaLightbulb /> View Example
              </button>
            )}
          </div>
        </div>
      </div>

      {showExample && (
        <div className="example-modal" onClick={() => setShowExample(false)}>
          <div className="example-content" onClick={(e) => e.stopPropagation()}>
            <h3>Example</h3>
            <p>{card.example}</p>
            <button onClick={() => setShowExample(false)}>Close</button>
          </div>
        </div>
      )}

      <p className="flip-hint">💡 Click the card to flip</p>
    </div>
  )
}

export default Flashcard

