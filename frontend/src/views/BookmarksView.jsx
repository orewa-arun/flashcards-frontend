import { useState, useEffect } from 'react'
import { FaStar, FaArrowLeft, FaBook, FaChevronDown, FaChevronUp, FaExternalLinkAlt } from 'react-icons/fa'
import { useNavigate } from 'react-router-dom'
import { getUserBookmarks, removeBookmark } from '../api/bookmarks'
import Flashcard from '../components/Flashcard'
import './BookmarksView.css'

function BookmarksView() {
  const [bookmarks, setBookmarks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedBookmark, setSelectedBookmark] = useState(null)
  const [removeLoading, setRemoveLoading] = useState({})
  const [expandedCards, setExpandedCards] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    loadBookmarks()
  }, [])

  const loadBookmarks = async () => {
    try {
      setLoading(true)
      const bookmarkData = await getUserBookmarks()
      setBookmarks(bookmarkData)
      setError(null)
    } catch (err) {
      setError('Failed to load bookmarks')
      console.error('Error loading bookmarks:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveBookmark = async (courseId, deckId, index, e) => {
    e.stopPropagation()
    const bookmarkKey = `${courseId}:${deckId}:${index}`
    
    try {
      setRemoveLoading(prev => ({ ...prev, [bookmarkKey]: true }))
      
      await removeBookmark({ courseId, deckId, index })
      
      // Remove from local state
      setBookmarks(prev => prev.filter(bookmark => 
        !(bookmark.course_id === courseId && 
          bookmark.deck_id === deckId && 
          bookmark.flashcard_index === index)
      ))
      
      // Close detailed view if this bookmark was selected
      if (selectedBookmark && 
          selectedBookmark.course_id === courseId && 
          selectedBookmark.deck_id === deckId && 
          selectedBookmark.flashcard_index === index) {
        setSelectedBookmark(null)
      }
      
    } catch (err) {
      console.error('Error removing bookmark:', err)
    } finally {
      setRemoveLoading(prev => ({ ...prev, [bookmarkKey]: false }))
    }
  }

  const groupBookmarksByCourse = () => {
    const grouped = {}
    
    bookmarks.forEach(bookmark => {
      const courseKey = bookmark.course_id
      if (!grouped[courseKey]) {
        grouped[courseKey] = []
      }
      grouped[courseKey].push(bookmark)
    })
    
    return grouped
  }

  const toggleCardExpanded = (bookmarkKey, e) => {
    e.stopPropagation()
    setExpandedCards(prev => ({
      ...prev,
      [bookmarkKey]: !prev[bookmarkKey]
    }))
  }

  const handleGoToDeck = (courseId, deckId, index, e) => {
    e.stopPropagation()
    navigate(`/courses/${courseId}/${deckId}/flashcards?card=${index}`)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="bookmarks-view">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading your bookmarks...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bookmarks-view">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={loadBookmarks} className="retry-btn">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  // Detailed flashcard view
  if (selectedBookmark) {
    return (
      <div className="bookmarks-view">
        <div className="bookmark-detail-header">
          <button onClick={() => setSelectedBookmark(null)} className="back-btn">
            <FaArrowLeft />
            Back to Bookmarks
          </button>
          <div className="bookmark-detail-info">
            <span className="course-badge">{selectedBookmark.course_id}</span>
            <span className="deck-name">{selectedBookmark.deck_id}</span>
          </div>
        </div>
        
        <div className="bookmark-detail-content">
          {selectedBookmark.flashcard_data ? (
            <Flashcard 
              card={selectedBookmark.flashcard_data}
              courseId={selectedBookmark.course_id}
              deckId={selectedBookmark.deck_id}
              index={selectedBookmark.flashcard_index}
              sessionId="bookmark-view"
            />
          ) : (
            <div className="flashcard-unavailable">
              <p>⚠️ Flashcard content is not available</p>
              <p>This may happen if the original flashcard file has been moved or modified.</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Main bookmarks list view - The Study Sheet
  const groupedBookmarks = groupBookmarksByCourse()
  const courseKeys = Object.keys(groupedBookmarks)

  return (
    <div className="bookmarks-view">
      <div className="bookmarks-header" style={{ animation: 'none', transform: 'none' }}>
        <div className="header-content" style={{ animation: 'none', transform: 'none' }}>
          <h1 className="page-title" style={{ animation: 'none', transform: 'none' }}>
            <FaStar className="title-icon" style={{ animation: 'none', transform: 'none' }} />
            The Study Sheet
          </h1>
          <p className="page-subtitle" style={{ animation: 'none', transform: 'none' }}>
            {bookmarks.length} flashcard{bookmarks.length !== 1 ? 's' : ''} bookmarked
          </p>
        </div>
      </div>

      {bookmarks.length === 0 ? (
        <div className="empty-state" style={{ animation: 'none', transform: 'none' }}>
          <FaStar className="empty-icon" style={{ animation: 'none', transform: 'none' }} />
          <h2 style={{ animation: 'none', transform: 'none' }}>No bookmarks yet</h2>
          <p style={{ animation: 'none', transform: 'none' }}>Start bookmarking flashcards you want to review later by clicking the star icon.</p>
        </div>
      ) : (
        <div className="bookmarks-content">
          {courseKeys.map(courseKey => {
            const courseBookmarks = groupedBookmarks[courseKey]
            return (
              <div key={courseKey} className="course-section">
                <div className="course-section-header">
                  <span className="course-badge-large">{courseKey}</span>
                  <span className="bookmark-count">
                    {courseBookmarks.length} bookmark{courseBookmarks.length !== 1 ? 's' : ''}
                  </span>
                </div>
                
                <div className="bookmarks-masonry">
                  {courseBookmarks.map(bookmark => {
                    const bookmarkKey = `${bookmark.course_id}:${bookmark.deck_id}:${bookmark.flashcard_index}`
                    const isExpanded = expandedCards[bookmarkKey]
                    const isRemoving = removeLoading[bookmarkKey]
                    
                    return (
                      <div key={bookmarkKey} className="bookmark-mini-card">
                        <div className="bookmark-card-header">
                          <div className="bookmark-source">
                            {bookmark.course_id} / {bookmark.deck_id}
                          </div>
                          <button
                            className="remove-bookmark-btn"
                            onClick={(e) => handleRemoveBookmark(
                              bookmark.course_id, 
                              bookmark.deck_id, 
                              bookmark.flashcard_index,
                              e
                            )}
                            disabled={isRemoving}
                            title="Remove bookmark"
                          >
                            {isRemoving ? (
                              <div className="btn-spinner"></div>
                            ) : (
                              <FaStar />
                            )}
                          </button>
                        </div>
                        
                        <div className="bookmark-card-body">
                          <div className="bookmark-question">
                            {bookmark.flashcard_data?.question || 'Question not available'}
                          </div>
                          
                          {isExpanded && bookmark.flashcard_data?.answers && (
                            <div className="bookmark-answer">
                              <div className="answer-label">Answer:</div>
                              <div className="answer-text">
                                {bookmark.flashcard_data.answers.concise || 
                                 bookmark.flashcard_data.answers.detailed || 
                                 'Answer not available'}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <div className="bookmark-card-footer">
                          <div className="bookmark-meta">
                            <span className="bookmark-date">
                              Saved {formatDate(bookmark.created_at)}
                            </span>
                          </div>
                          <div className="bookmark-actions">
                            <button
                              className="expand-btn"
                              onClick={(e) => toggleCardExpanded(bookmarkKey, e)}
                              title={isExpanded ? "Hide answer" : "Show answer"}
                            >
                              {isExpanded ? <FaChevronUp /> : <FaChevronDown />}
                            </button>
                            <button
                              className="goto-deck-btn"
                              onClick={(e) => handleGoToDeck(
                                bookmark.course_id,
                                bookmark.deck_id,
                                bookmark.flashcard_index,
                                e
                              )}
                              title="Go to deck"
                            >
                              <FaExternalLinkAlt />
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default BookmarksView
