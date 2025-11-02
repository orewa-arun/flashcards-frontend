import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trackEvent } from '../utils/amplitude';
import './LectureDetailView.css';

function LectureDetailView() {
  const { courseId, lectureId } = useParams();
  const navigate = useNavigate();

  const handleStudyClick = () => {
    trackEvent('Selected Study Mode', { courseId, lectureId });
    navigate(`/courses/${courseId}/${lectureId}/flashcards`);
  };

  const handleQuizClick = () => {
    trackEvent('Selected Quiz Mode', { courseId, lectureId });
    navigate(`/courses/${courseId}/${lectureId}/quiz`);
  };

  // Format lecture ID for display (e.g., "DAA_lec_1" -> "DAA Lecture 1")
  const formatLectureTitle = (id) => {
    return id
      .replace(/_/g, ' ')
      .replace(/lec/i, 'Lecture')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="lecture-detail-view">
      <div className="lecture-detail-container">
        <div className="lecture-header">
          <button 
            className="back-button"
            onClick={() => navigate(`/courses/${courseId}`)}
          >
            ← Back to Course
          </button>
          <h1 className="lecture-title">{formatLectureTitle(lectureId)}</h1>
          <p className="lecture-subtitle">Choose how you want to learn</p>
        </div>

        <div className="learning-modes">
          <div className="mode-card study-card" onClick={handleStudyClick}>
            <div className="mode-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h2 className="mode-title">Study Flashcards</h2>
            <p className="mode-description">
              Review concepts with interactive flashcards. Perfect for learning and memorization.
            </p>
            <div className="mode-features">
              <span className="feature-tag">📚 Interactive</span>
              <span className="feature-tag">🔖 Bookmarkable</span>
              <span className="feature-tag">⏱️ Self-paced</span>
            </div>
            <button className="mode-button study-button">
              Start Studying →
            </button>
          </div>

          <div className="mode-card quiz-card" onClick={handleQuizClick}>
            <div className="mode-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <path d="M9 11L12 14L22 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h2 className="mode-title">Take Quiz</h2>
            <p className="mode-description">
              Test your knowledge with adaptive quizzes. Get instant feedback and track your progress.
            </p>
            <div className="mode-features">
              <span className="feature-tag">🎯 Adaptive</span>
              <span className="feature-tag">📊 Scored</span>
              <span className="feature-tag">📈 Tracked</span>
            </div>
            <button className="mode-button quiz-button">
              Start Quiz →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LectureDetailView;

