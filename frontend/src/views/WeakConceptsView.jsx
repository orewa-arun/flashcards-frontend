/**
 * WeakConceptsView - Deck-style view for reviewing weak concepts
 */

import React, { useState, useEffect } from 'react';
import { FaExclamationTriangle, FaFilter, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { getUserProfile } from '../api/profile';
import { getWeakConcepts } from '../api/weakConcepts';
import Flashcard from '../components/Flashcard';
import './WeakConceptsView.css';

const WeakConceptsView = () => {
  const [loading, setLoading] = useState(true);
  const [weakConceptsByCourse, setWeakConceptsByCourse] = useState({});
  const [selectedCourse, setSelectedCourse] = useState('all');
  const [enrolledCourses, setEnrolledCourses] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [filteredConcepts, setFilteredConcepts] = useState([]);

  useEffect(() => {
    loadAllWeakConcepts();
  }, []);

  useEffect(() => {
    // Update filtered concepts when course selection changes
    const concepts = getFilteredConceptsList();
    setFilteredConcepts(concepts);
    setCurrentIndex(0); // Reset to first card when filter changes
  }, [selectedCourse, weakConceptsByCourse]);

  const loadAllWeakConcepts = async () => {
    try {
      setLoading(true);
      
      // Get user's enrolled courses
      const profile = await getUserProfile();
      const courses = profile?.enrolled_courses || [];
      setEnrolledCourses(courses);
      
      // Fetch weak concepts for each course
      const conceptsPromises = courses.map(async (courseId) => {
        try {
          const data = await getWeakConcepts(courseId);
          return { courseId, data };
        } catch (error) {
          console.error(`Error loading weak concepts for ${courseId}:`, error);
          return { courseId, data: null };
        }
      });
      
      const results = await Promise.all(conceptsPromises);
      
      // Organize by course
      const conceptsByCourse = {};
      results.forEach(({ courseId, data }) => {
        if (data && data.has_attempts && data.weak_concepts.length > 0) {
          conceptsByCourse[courseId] = data;
        }
      });
      
      setWeakConceptsByCourse(conceptsByCourse);
    } catch (error) {
      console.error('Error loading weak concepts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredConceptsList = () => {
    if (selectedCourse === 'all') {
      // Combine all concepts from all courses
      const allConcepts = [];
      Object.entries(weakConceptsByCourse).forEach(([courseId, courseData]) => {
        courseData.weak_concepts.forEach(concept => {
          allConcepts.push({
            ...concept,
            courseId // Add courseId to each concept
          });
        });
      });
      return allConcepts;
    }
    
    if (weakConceptsByCourse[selectedCourse]) {
      return weakConceptsByCourse[selectedCourse].weak_concepts.map(concept => ({
        ...concept,
        courseId: selectedCourse
      }));
    }
    
    return [];
  };

  const getTotalWeakConcepts = () => {
    return Object.values(weakConceptsByCourse).reduce(
      (total, courseData) => total + (courseData.weak_concepts?.length || 0),
      0
    );
  };

  const handleNext = () => {
    if (currentIndex < filteredConcepts.length - 1) {
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
  }, [currentIndex, filteredConcepts.length]);

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

  const totalWeak = getTotalWeakConcepts();
  const currentConcept = filteredConcepts[currentIndex];
  const progress = filteredConcepts.length > 0 ? ((currentIndex + 1) / filteredConcepts.length) * 100 : 0;

  return (
    <div className="weak-concepts-view">
      {/* Header */}
      <div className="view-header">
        <div className="header-content">
          <div className="title-section">
            <FaExclamationTriangle className="header-icon" />
            <div>
              <h1>Concepts You Need to Review</h1>
              <p className="subtitle">
                Focus on these concepts to improve your exam readiness
              </p>
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
              {Object.keys(weakConceptsByCourse).map((courseId) => (
                <button
                  key={courseId}
                  className={`filter-btn ${selectedCourse === courseId ? 'active' : ''}`}
                  onClick={() => setSelectedCourse(courseId)}
                >
                  {courseId} ({weakConceptsByCourse[courseId].weak_concepts.length})
                </button>
              ))}
            </div>
          </div>

          {/* Deck View */}
          {filteredConcepts.length > 0 && currentConcept && (
            <div className="deck-container">
              {/* Progress Bar */}
              <div className="deck-progress">
                <span className="progress-counter">
                  {currentIndex + 1} / {filteredConcepts.length}
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
                  <span className="course-badge">{currentConcept.courseId}</span>
                  <span className="separator">•</span>
                  <span className="lecture-badge">{currentConcept.lecture_id}</span>
                </div>

                <Flashcard 
                  card={{
                    flashcard_id: currentConcept.flashcard_id,
                    question: currentConcept.question,
                    answers: currentConcept.answers,
                    example: currentConcept.example,
                    mermaid_diagrams: currentConcept.mermaid_diagrams,
                    math_visualizations: currentConcept.math_visualizations,
                  }}
                  courseId={currentConcept.courseId}
                  deckId={currentConcept.lecture_id}
                  index={currentIndex}
                  sessionId={null} // No session tracking for weak concepts review
                />

                {/* Performance Stats Below Card */}
                <div className="performance-stats">
                  <div className="stat-box accuracy">
                    <span className="stat-label">Accuracy</span>
                    <span className={`stat-value ${currentConcept.accuracy < 40 ? 'critical' : 'weak'}`}>
                      {currentConcept.accuracy}%
                    </span>
                  </div>
                  <div className="stat-box attempts">
                    <span className="stat-label">Total Attempts</span>
                    <span className="stat-value">{currentConcept.total_attempts}</span>
                  </div>
                  <div className="stat-box breakdown">
                    <span className="stat-label">Breakdown</span>
                    <span className="stat-value">
                      <span className="correct-count">{currentConcept.correct} ✓</span>
                      {' / '}
                      <span className="incorrect-count">{currentConcept.incorrect} ✗</span>
                    </span>
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
                  disabled={currentIndex === filteredConcepts.length - 1}
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
