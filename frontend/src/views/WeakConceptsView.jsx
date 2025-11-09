/**
 * WeakConceptsView - Deck-style view for reviewing weak concepts
 */

import React, { useState, useEffect } from 'react';
import { FaExclamationTriangle, FaFilter, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { getWeakFlashcards } from '../api/performance';
import { getUserProfile } from '../api/profile'; // To get enrolled courses for filter
import Flashcard from '../components/Flashcard';
import './WeakConceptsView.css';

const WeakConceptsView = () => {
  const [loading, setLoading] = useState(true);
  const [allWeakFlashcards, setAllWeakFlashcards] = useState([]);
  const [filteredFlashcards, setFilteredFlashcards] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('all');
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [profile, weakFlashcards] = await Promise.all([
          getUserProfile(),
          getWeakFlashcards()
        ]);

        setEnrolledCourses(profile?.enrolled_courses || []);
        setAllWeakFlashcards(weakFlashcards || []);
      } catch (error) {
        console.error('Error loading weak concepts data:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    // Update filtered flashcards when course selection or the main list changes
    let concepts = [];
    if (selectedCourse === 'all') {
      concepts = allWeakFlashcards;
    } else {
      concepts = allWeakFlashcards.filter(fc => fc.course_id === selectedCourse);
    }
    setFilteredFlashcards(concepts);
    setCurrentIndex(0); // Reset to first card when filter changes
  }, [selectedCourse, allWeakFlashcards]);

  const handleNext = () => {
    if (currentIndex < filteredFlashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event) => {
      switch (event.code) {
        case 'ArrowRight':
          event.preventDefault();
          handleNext();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          handlePrevious();
          break;
        default:
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, filteredFlashcards.length]);

  if (loading) {
    return (
      <div className="weak-concepts-view">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading weak concepts...</p>
        </div>
      </div>
    );
  }

  const totalWeak = allWeakFlashcards.length;
  const currentFlashcard = filteredFlashcards[currentIndex];
  const progress = filteredFlashcards.length > 0 ? ((currentIndex + 1) / filteredFlashcards.length) * 100 : 0;
  
  const getAccuracy = (flashcard) => {
      const { easy, medium, hard, boss } = flashcard.performance_by_level || {};
      const totalCorrect = (easy?.correct || 0) + (medium?.correct || 0) + (hard?.correct || 0) + (boss?.correct || 0);
      const totalAttempts = (easy?.attempts || 0) + (medium?.attempts || 0) + (hard?.attempts || 0) + (boss?.attempts || 0);
      return totalAttempts > 0 ? Math.round((totalCorrect / totalAttempts) * 100) : 0;
  };

  const getTotalAttempts = (flashcard) => {
      const { easy, medium, hard, boss } = flashcard.performance_by_level || {};
      return (easy?.attempts || 0) + (medium?.attempts || 0) + (hard?.attempts || 0) + (boss?.attempts || 0);
  };
  
  return (
    <div className="weak-concepts-view">
      {/* Header */}
      <div className="view-header">
        <div className="header-content">
          <div className="title-section">
            <FaExclamationTriangle className="header-icon" />
            <div>
              <h1>Concepts You Need to Review</h1>
              <p className="subtitle">Focus on these concepts to improve your exam readiness</p>
            </div>
          </div>
          
          {totalWeak > 0 && (
            <div className="stats-badge">
              <span className="total-count">{totalWeak}</span>
              <span className="label">Total Weak Concepts</span>
            </div>
          )}
        </div>
      </div>

      {totalWeak === 0 ? (
        <div className="no-weak-concepts-message">
          <div className="message-content">
            <h2>🎉 Excellent Work!</h2>
            <p>You don't have any weak concepts across your enrolled courses.</p>
            <p className="hint">Keep practicing to maintain your strong performance!</p>
          </div>
        </div>
      ) : (
        <>
          {/* Filter by Course */}
          <div className="filter-section">
            <div className="filter-label">
              <FaFilter />
              <span>Filter by Course:</span>
            </div>
            <div className="course-filter-buttons">
              <button
                className={`filter-btn ${selectedCourse === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedCourse('all')}
              >
                All Courses ({totalWeak})
              </button>
              {enrolledCourses.map((courseId) => {
                  const count = allWeakFlashcards.filter(fc => fc.course_id === courseId).length;
                  if (count === 0) return null;
                  return (
                    <button
                      key={courseId}
                      className={`filter-btn ${selectedCourse === courseId ? 'active' : ''}`}
                      onClick={() => setSelectedCourse(courseId)}
                    >
                      {courseId} ({count})
                    </button>
                  )
              })}
            </div>
          </div>

          {/* Deck View */}
          {filteredFlashcards.length > 0 && currentFlashcard && (
            <div className="deck-container">
              {/* Progress Bar */}
              <div className="deck-progress">
                <span className="progress-counter">
                  {currentIndex + 1} / {filteredFlashcards.length}
                </span>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Flashcard */}
              <div className="flashcard-wrapper">
                <div className="course-lecture-badge">
                  <span className="course-badge">{currentFlashcard.course_id}</span>
                  <span className="separator">•</span>
                  <span className="lecture-badge">{currentFlashcard.lecture_id}</span>
                </div>

                {currentFlashcard.is_missing_data ? (
                  <div className="missing-flashcard-notice">
                    <div className="notice-icon">⚠️</div>
                    <h3>Flashcard Data Unavailable</h3>
                    <p className="notice-message">
                      This flashcard may have been updated or removed since you last studied it.
                    </p>
                  </div>
                ) : (
                <Flashcard 
                  card={currentFlashcard}
                  courseId={currentFlashcard.course_id}
                  deckId={currentFlashcard.lecture_id}
                  index={currentIndex}
                  sessionId={null}
                />
                )}

                {/* Performance Stats Below Card */}
                <div className="performance-stats">
                  <div className="stat-box accuracy">
                    <span className="stat-label">Accuracy</span>
                    <span className={`stat-value ${getAccuracy(currentFlashcard) < 40 ? 'critical' : 'weak'}`}>
                      {getAccuracy(currentFlashcard)}%
                    </span>
                  </div>
                  <div className="stat-box attempts">
                    <span className="stat-label">Total Attempts</span>
                    <span className="stat-value">{getTotalAttempts(currentFlashcard)}</span>
                  </div>
                </div>
              </div>

              {/* Navigation */}
              <div className="deck-navigation">
                <button 
                  className="nav-btn prev"
                  onClick={handlePrevious}
                  disabled={currentIndex === 0}
                  title="Previous (←)"
                >
                  <FaChevronLeft />
                  <span>Previous</span>
                </button>
                
                <div className="nav-hint">
                  <span>← → Navigate</span>
                  <span className="separator">•</span>
                  <span>Space to Flip</span>
                </div>
                
                <button 
                  className="nav-btn next"
                  onClick={handleNext}
                  disabled={currentIndex === filteredFlashcards.length - 1}
                  title="Next (→)"
                >
                  <span>Next</span>
                  <FaChevronRight />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default WeakConceptsView;
