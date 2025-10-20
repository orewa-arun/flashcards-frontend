import { useState, useEffect } from 'react'
import { FaStar, FaArrowLeft, FaBook, FaFolder } from 'react-icons/fa'
import { getUserBookmarks, removeBookmark } from '../api/bookmarks'
import Flashcard from '../components/Flashcard'
import './BookmarksView.css'

function BookmarksView() {
  const [bookmarks, setBookmarks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedBookmark, setSelectedBookmark] = useState(null)
  const [removeLoading, setRemoveLoading] = useState({})

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

  const handleRemoveBookmark = async (courseId, deckId, index) => {
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
      // Optionally show error toast
    } finally {
      setRemoveLoading(prev => ({ ...prev, [bookmarkKey]: false }))
    }
  }

  const groupBookmarksByDeck = () => {
    const grouped = {}
    
    bookmarks.forEach(bookmark => {
      const deckKey = `${bookmark.course_id}:${bookmark.deck_id}`
      if (!grouped[deckKey]) {
        grouped[deckKey] = {
          course_id: bookmark.course_id,
          deck_id: bookmark.deck_id,
          bookmarks: []
        }
      }
      grouped[deckKey].bookmarks.push(bookmark)
    })
    
    return grouped
  }

  const handleViewFlashcard = (bookmark) => {
    setSelectedBookmark(bookmark)
  }

  const handleBackToList = () => {
    setSelectedBookmark(null)
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
          <button onClick={handleBackToList} className="back-btn">
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
              sessionId="bookmark-view" // Special session ID for bookmark viewing
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

  // Main bookmarks list view
  const groupedBookmarks = groupBookmarksByDeck()
  const deckKeys = Object.keys(groupedBookmarks)

  return (
    <div className="bookmarks-view">
      <div className="bookmarks-header">
        <div className="header-content">
          <h1 className="page-title">
            <FaStar className="title-icon" />
            My Bookmarks
          </h1>
          <p className="page-subtitle">
            {bookmarks.length} flashcard{bookmarks.length !== 1 ? 's' : ''} bookmarked
          </p>
        </div>
      </div>

      {bookmarks.length === 0 ? (
        <div className="empty-state">
          <FaStar className="empty-icon" />
          <h2>No bookmarks yet</h2>
          <p>Start bookmarking flashcards you want to review later by clicking the star icon.</p>
        </div>
      ) : (
        <div className="bookmarks-content">
          {deckKeys.map(deckKey => {
            const deckData = groupedBookmarks[deckKey]
            return (
              <div key={deckKey} className="deck-group">
                <div className="deck-header">
                  <div className="deck-info">
                    <FaBook className="deck-icon" />
                    <div className="deck-details">
                      <h3 className="deck-title">{deckData.deck_id}</h3>
                      <span className="course-badge">{deckData.course_id}</span>
                    </div>
                  </div>
                  <span className="bookmark-count">
                    {deckData.bookmarks.length} bookmark{deckData.bookmarks.length !== 1 ? 's' : ''}
                  </span>
                </div>
                
                <div className="bookmarks-grid">
                  {deckData.bookmarks.map(bookmark => {
                    const bookmarkKey = `${bookmark.course_id}:${bookmark.deck_id}:${bookmark.flashcard_index}`
                    const isRemoving = removeLoading[bookmarkKey]
                    
                    return (
                      <div key={bookmarkKey} className="bookmark-card">
                        <div className="bookmark-content" onClick={() => handleViewFlashcard(bookmark)}>
                          <div className="bookmark-question">
                            {bookmark.flashcard_data?.question || 'Question not available'}
                          </div>
                          <div className="bookmark-meta">
                            <span className="flashcard-index">Card #{bookmark.flashcard_index + 1}</span>
                            <span className="bookmark-date">
                              Saved {new Date(bookmark.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        
                        <button
                          className="remove-bookmark-btn"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRemoveBookmark(
                              bookmark.course_id, 
                              bookmark.deck_id, 
                              bookmark.flashcard_index
                            )
                          }}
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
