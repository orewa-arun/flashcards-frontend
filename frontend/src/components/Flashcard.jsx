import { useState, useEffect, useMemo } from 'react'
import { FaLightbulb, FaStar, FaRegStar, FaThumbsUp, FaThumbsDown } from 'react-icons/fa'
import { addBookmark, removeBookmark, isBookmarked } from '../api/bookmarks'
import { submitFeedback, getFlashcardFeedback } from '../api/feedback'
import mermaid from 'mermaid'
import './Flashcard.css'

// Initialize Mermaid for light mode by default
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  securityLevel: 'loose',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif',
  themeVariables: {
    primaryColor: '#3B82F6',
    primaryTextColor: '#1F2937',
    primaryBorderColor: '#3B82F6',
    lineColor: '#9CA3AF',
    secondaryColor: '#E5E7EB',
    tertiaryColor: '#F3F4F6',
    background: '#FFFFFF',
    mainBkg: '#FFFFFF',
    secondBkg: '#F8FAFC',
    tertiaryBkg: '#F1F5F9',
    textColor: '#1F2937',
    fontSize: '14px'
  }
})

// Mermaid diagram cache for performance
const diagramCache = new Map()

const answerTypes = [
  { key: 'concise', label: 'Concise' },
  { key: 'analogy', label: 'Analogy' },
  { key: 'eli5', label: 'ELI5' },
  { key: 'real_world_use_case', label: 'Use Case' },
  { key: 'common_mistakes', label: 'Mistakes' },
  { key: 'example', label: 'Example' }
];

function Flashcard({ card, courseId, deckId, index, sessionId }) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState('concise');
  const [mermaidLoading, setMermaidLoading] = useState(false)
  const [mermaidError, setMermaidError] = useState(null)
  
  // Bookmark and feedback state
  const [isCardBookmarked, setIsCardBookmarked] = useState(false)
  const [feedbackRating, setFeedbackRating] = useState(null) // null, 1 (like), -1 (dislike)
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [bookmarkLoading, setBookmarkLoading] = useState(false)
  
  // Generate a stable unique ID for this card's mermaid diagram using useMemo
  const uniqueDiagramId = useMemo(() => {
    return `mermaid-diagram-${card.question.substring(0, 20).replace(/[^a-zA-Z0-9]/g, '')}-${Math.random().toString(36).substr(2, 9)}`
  }, [card.question])

  // Create cache key for mermaid diagram
  const diagramCacheKey = useMemo(() => {
    if (!card.mermaid_code) return null
    return `mermaid-${card.mermaid_code.replace(/\s+/g, '').substring(0, 50)}`
  }, [card.mermaid_code])

  // Effect to reset state when card changes
  useEffect(() => {
    setIsFlipped(false);
    setSelectedAnswer('concise');
    setMermaidLoading(false);
    setMermaidError(null);
    setIsCardBookmarked(false);
    setFeedbackRating(null);
  }, [card]);

  // Load bookmark and feedback state when card changes
  useEffect(() => {
    const loadCardState = async () => {
      if (!courseId || !deckId || index === undefined) return;
      
      try {
        // Load bookmark status
        const bookmarked = await isBookmarked(courseId, deckId, index);
        setIsCardBookmarked(bookmarked);
        
        // Load feedback status  
        const rating = await getFlashcardFeedback(courseId, deckId, index);
        setFeedbackRating(rating);
      } catch (error) {
        console.error('Error loading card state:', error);
      }
    };

    loadCardState();
  }, [courseId, deckId, index]);

  // Bookmark handlers
  const handleBookmarkToggle = async (e) => {
    e.stopPropagation();
    if (bookmarkLoading) return;
    
    setBookmarkLoading(true);
    try {
      if (isCardBookmarked) {
        await removeBookmark({ courseId, deckId, index });
        setIsCardBookmarked(false);
      } else {
        await addBookmark({ courseId, deckId, index });
        setIsCardBookmarked(true);
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error);
    } finally {
      setBookmarkLoading(false);
    }
  };

  // Feedback handlers
  const handleLike = async (e) => {
    e.stopPropagation();
    if (feedbackLoading || !sessionId) return;
    
    setFeedbackLoading(true);
    try {
      const newRating = feedbackRating === 1 ? null : 1;
      
      if (newRating === null) {
        // Clear feedback logic would go here if we implement it
        setFeedbackRating(null);
      } else {
        await submitFeedback({
          sessionId,
          courseId,
          deckId,
          index,
          rating: newRating
        });
        setFeedbackRating(newRating);
      }
    } catch (error) {
      console.error('Error submitting like:', error);
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleDislike = async (e) => {
    e.stopPropagation();
    if (feedbackLoading || !sessionId) return;
    
    setFeedbackLoading(true);
    try {
      const newRating = feedbackRating === -1 ? null : -1;
      
      if (newRating === null) {
        // Clear feedback logic would go here if we implement it
        setFeedbackRating(null);
      } else {
        await submitFeedback({
          sessionId,
          courseId,
          deckId,
          index,
          rating: newRating
        });
        setFeedbackRating(newRating);
      }
    } catch (error) {
      console.error('Error submitting dislike:', error);
    } finally {
      setFeedbackLoading(false);
    }
  };

  // Enhanced Mermaid rendering with caching, loading states, and error handling
  useEffect(() => {
    if (!isFlipped || !card.mermaid_code || !card.mermaid_code.trim()) {
      return;
    }

    const renderDiagram = async () => {
      const mermaidContainer = document.getElementById(uniqueDiagramId);
      if (!mermaidContainer) return;

      try {
        setMermaidLoading(true);
        setMermaidError(null);

        // Check cache first
        if (diagramCacheKey && diagramCache.has(diagramCacheKey)) {
          const cachedSvg = diagramCache.get(diagramCacheKey);
          mermaidContainer.innerHTML = cachedSvg;
          setMermaidLoading(false);
          return;
        }

        // Clear previous content
        mermaidContainer.innerHTML = '';
        
        // Generate unique ID for this render
        const renderId = `mermaid-svg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Render with timeout to prevent hanging
        const renderPromise = mermaid.render(renderId, card.mermaid_code);
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Mermaid render timeout')), 5000)
        );
        
        const { svg } = await Promise.race([renderPromise, timeoutPromise]);
        
        // Cache the result for future use
        if (diagramCacheKey) {
          diagramCache.set(diagramCacheKey, svg);
        }
        
        mermaidContainer.innerHTML = svg;
        setMermaidLoading(false);
        
      } catch (e) {
        console.error('Mermaid rendering error:', e);
        setMermaidError('Failed to render diagram');
        setMermaidLoading(false);
        
        // Show fallback message
        mermaidContainer.innerHTML = `
          <div class="mermaid-error">
            <p>⚠️ Diagram could not be rendered</p>
            <details>
              <summary>View diagram code</summary>
              <pre><code>${card.mermaid_code}</code></pre>
            </details>
          </div>
        `;
      }
    };

    // Lazy loading: small delay to ensure DOM is ready and smooth UX
    const timeoutId = setTimeout(renderDiagram, 100);
    return () => clearTimeout(timeoutId);
    
  }, [isFlipped, card.mermaid_code, uniqueDiagramId, diagramCacheKey])

  const handleCardClick = (e) => {
    // Don't flip if clicking on buttons or diagram
    if (e.target.closest('.mermaid-diagram-container') || 
        e.target.closest('.answer-selector') ||
        e.target.closest('.bookmark-btn') ||
        e.target.closest('.feedback-buttons')) {
      return
    }
    setIsFlipped(!isFlipped)
  }

  // Enhanced keyboard shortcuts for flipping cards and switching answer types
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Space for flipping cards
      if (event.code === 'Space') {
        event.preventDefault()
        setIsFlipped(!isFlipped)
      }
      
      // Number keys (1-6) for switching answer types when card is flipped
      if (isFlipped && event.key >= '1' && event.key <= '6') {
        event.preventDefault()
        const answerIndex = parseInt(event.key) - 1
        if (answerIndex < answerTypes.length) {
          setSelectedAnswer(answerTypes[answerIndex].key)
        }
      }

      // Tab key to cycle through answer types
      if (isFlipped && event.key === 'Tab') {
        event.preventDefault()
        const currentIndex = answerTypes.findIndex(type => type.key === selectedAnswer)
        const nextIndex = (currentIndex + 1) % answerTypes.length
        setSelectedAnswer(answerTypes[nextIndex].key)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isFlipped, selectedAnswer])

  const getAnswerContent = () => {
    if (selectedAnswer === 'example') {
      return card.example || 'No example available for this card.'
    }
    return card.answers && card.answers[selectedAnswer]
  }

  return (
    <div className="flashcard-wrapper">
      <div 
        className={`flashcard ${isFlipped ? 'flipped' : ''}`}
        onClick={handleCardClick}
      >
        {/* Front of Card - Clean Question Display */}
        <div className="flashcard-front">
          {/* Bookmark button in top-right corner */}
          <button
            className={`bookmark-btn ${isCardBookmarked ? 'bookmarked' : ''}`}
            onClick={handleBookmarkToggle}
            disabled={bookmarkLoading}
            title={isCardBookmarked ? 'Remove bookmark' : 'Add bookmark'}
          >
            {bookmarkLoading ? (
              <div className="btn-spinner"></div>
            ) : (
              isCardBookmarked ? <FaStar /> : <FaRegStar />
            )}
          </button>
          
          <div className="card-content">
            <div className="question-text">
              {card.question}
            </div>
          </div>
        </div>
        
        {/* Back of Card - Answer with Type Selector */}
        <div className="flashcard-back">
          {/* Bookmark button in top-right corner */}
          <button
            className={`bookmark-btn ${isCardBookmarked ? 'bookmarked' : ''}`}
            onClick={handleBookmarkToggle}
            disabled={bookmarkLoading}
            title={isCardBookmarked ? 'Remove bookmark' : 'Add bookmark'}
          >
            {bookmarkLoading ? (
              <div className="btn-spinner"></div>
            ) : (
              isCardBookmarked ? <FaStar /> : <FaRegStar />
            )}
          </button>
          
          <div className="card-content">
            <div className="answer-selector">
              {answerTypes.map((type, index) => (
                <button
                  key={type.key}
                  className={`answer-type-btn ${selectedAnswer === type.key ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedAnswer(type.key);
                  }}
                  title={`${type.label} (${index + 1})`}
                >
                  <span className="shortcut-key">{index + 1}</span>
                  <span className="tab-label">{type.label}</span>
                </button>
              ))}
            </div>
            
            <div className="answer-content">
              <div className="answer-text">
                {getAnswerContent()}
              </div>
              
              {/* Mermaid Diagram Container with Loading States */}
              {card.mermaid_code && card.mermaid_code.trim() !== '' && (
                <div className="mermaid-diagram-wrapper">
                  {mermaidLoading && (
                    <div className="mermaid-loading">
                      <div className="mermaid-spinner"></div>
                      <p>Rendering diagram...</p>
                    </div>
                  )}
                  <div 
                    id={uniqueDiagramId} 
                    className={`mermaid-diagram-container ${mermaidLoading ? 'loading' : ''}`}
                  >
                    {/* Mermaid will render the SVG diagram here */}
                  </div>
                </div>
              )}
            </div>
            
            {/* Feedback buttons at bottom of card */}
            <div className="feedback-buttons">
              <button
                className={`feedback-btn like-btn ${feedbackRating === 1 ? 'active' : ''}`}
                onClick={handleLike}
                disabled={feedbackLoading}
                title="Like this flashcard"
              >
                {feedbackLoading && feedbackRating !== -1 ? (
                  <div className="btn-spinner"></div>
                ) : (
                  <FaThumbsUp />
                )}
              </button>
              
              <button
                className={`feedback-btn dislike-btn ${feedbackRating === -1 ? 'active' : ''}`}
                onClick={handleDislike}
                disabled={feedbackLoading}
                title="Dislike this flashcard"
              >
                {feedbackLoading && feedbackRating !== 1 ? (
                  <div className="btn-spinner"></div>
                ) : (
                  <FaThumbsDown />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Flashcard

