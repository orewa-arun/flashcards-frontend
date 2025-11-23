import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaChevronRight, FaLayerGroup, FaClipboardCheck } from 'react-icons/fa';
import { trackEvent } from '../utils/amplitude';
import MixModeCard from '../components/MixMode/MixModeCard';
import TutorCard from '../components/Tutor/TutorCard';
import './LectureDetailView.css';

function LectureDetailView() {
  const { courseId, lectureId } = useParams();
  const navigate = useNavigate();
  const [courseData, setCourseData] = useState(null);
  const [lectureData, setLectureData] = useState(null);

  useEffect(() => {
    // Load course and lecture data
    fetch('/courses.json')
      .then(response => response.json())
      .then(data => {
        const course = data.find(c => c.course_id === courseId);
        if (course) {
          setCourseData(course);
          // Find the lecture by matching the lectureId with the pdf_path
          const lecture = course.lecture_slides?.find(slide => {
            const pdfFilename = slide.pdf_path.split('/').pop().replace('.pdf', '');
            return pdfFilename === lectureId;
          });
          setLectureData(lecture);
        }
      })
      .catch(error => console.error('Error loading course data:', error));
  }, [courseId, lectureId]);

  const handleStudyClick = () => {
    trackEvent('Selected Study Mode', { courseId, lectureId });
    navigate(`/courses/${courseId}/${lectureId}/flashcards`);
  };

  const handleQuizClick = () => {
    // Temporary frontend-only behavior for MS5031 (DAA):
    // Quizzes are not available yet for this course. Keep users focused
    // on flashcards and the AI Tutor.
    if (courseId === 'MS5031') {
      alert(
        'Quizzes are not available yet for this lecture in Data Analysis Applications (MS5031).\n\n' +
        'For now, please use the flashcards and your AI Tutor to study this lecture.'
      );
      return;
    }
    trackEvent('Selected Quiz Mode', { courseId, lectureId });
    navigate(`/courses/${courseId}/${lectureId}/quiz`);
  };

  const handleMixClick = () => {
    // Temporary frontend-only behavior for MS5031 (DAA):
    // Adaptive Mix Mode is not available yet for this course.
    if (courseId === 'MS5031') {
      alert(
        'Adaptive Mix Mode is not available yet for this lecture in Data Analysis Applications (MS5031).\n\n' +
        'For now, please use the flashcards and your AI Tutor to practice this lecture.'
      );
      return;
    }
    trackEvent('Selected Mix Mode', { courseId, lectureId });
    navigate(`/courses/${courseId}/${lectureId}/mix`);
  };

  const handleTutorClick = () => {
    trackEvent('Selected AI Tutor', { courseId, lectureId });
    navigate(`/courses/${courseId}/${lectureId}/tutor`);
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
        {/* Breadcrumb Navigation */}
        <nav className="breadcrumb-nav">
          <button onClick={() => navigate('/courses')} className="breadcrumb-link">
            Courses
          </button>
          <FaChevronRight className="breadcrumb-separator" />
          <button onClick={() => navigate(`/courses/${courseId}`)} className="breadcrumb-link">
            {courseData?.course_name || courseId}
          </button>
          <FaChevronRight className="breadcrumb-separator" />
          <span className="breadcrumb-current">
            {lectureData?.lecture_name || formatLectureTitle(lectureId)}
          </span>
        </nav>

        {/* Page Header */}
        <header className="page-header">
          <h1 className="page-title">
            {lectureData?.lecture_name || formatLectureTitle(lectureId)}
          </h1>
          <p className="page-subtitle">Choose how you want to learn</p>
        </header>

        {/* Action Panels */}
        <div className="action-panels">
          {/* Premium: Mix Mode (Recommended) */}
          <MixModeCard 
            onClick={handleMixClick}
            courseId={courseId}
            deckId={lectureId}
          />
          
          {/* AI Tutor Panel */}
          <TutorCard onClick={handleTutorClick} />
          
          {/* Primary Panel: Study Flashcards */}
          <div className="action-panel primary-panel" onClick={handleStudyClick}>
            <div className="panel-icon primary-icon">
              <FaLayerGroup />
            </div>
            <h2 className="panel-title">Study Flashcards</h2>
            <p className="panel-description">
              Review concepts with interactive flashcards. Perfect for learning and memorization.
            </p>
            <div className="panel-features">
              <span className="feature-badge">Interactive</span>
              <span className="feature-badge">Bookmarkable</span>
              <span className="feature-badge">Self-paced</span>
            </div>
            <button className="panel-button primary-button">
              Start Studying →
            </button>
          </div>

          {/* Secondary Panel: Take Quiz */}
          <div className="action-panel secondary-panel" onClick={handleQuizClick}>
            <div className="panel-icon secondary-icon">
              <FaClipboardCheck />
            </div>
            <h2 className="panel-title">Take Quiz</h2>
            <p className="panel-description">
              Test your knowledge with adaptive quizzes. Get instant feedback and track your progress.
            </p>
            <div className="panel-features">
              <span className="feature-badge">Adaptive</span>
              <span className="feature-badge">Scored</span>
              <span className="feature-badge">Tracked</span>
            </div>
            <button className="panel-button secondary-button">
              Start Quiz →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LectureDetailView;
