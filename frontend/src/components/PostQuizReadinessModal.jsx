/**
 * PostQuizReadinessModal - Premium exam readiness update display
 * 
 * World-class, elegant design matching brand identity
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './PostQuizReadinessModal.css';

const PostQuizReadinessModal = ({ examReadinessData, courseId, onClose }) => {
  const navigate = useNavigate();
  const [animatedScores, setAnimatedScores] = useState({});
  const [animatedStats, setAnimatedStats] = useState({});

  // Animate scores and stats on mount
  useEffect(() => {
    if (!examReadinessData || examReadinessData.length === 0) return;

    const duration = 1500;
    const steps = 60;
    const interval = duration / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const progress = currentStep / steps;
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);

      const newScores = {};
      const newStats = {};
      
      examReadinessData.forEach((exam) => {
        newScores[exam.exam_id] = Math.round(exam.overall_readiness_score * easeOutQuart);
        newStats[exam.exam_id] = {
          coverage: Math.round(exam.coverage_factor * 100 * easeOutQuart),
          accuracy: Math.round(exam.accuracy_factor * 100 * easeOutQuart),
          momentum: Math.round(exam.momentum_factor * 100 * easeOutQuart),
          tested: Math.round(exam.flashcards_attempted * easeOutQuart),
          weak: Math.round((exam.weak_flashcards?.length || 0) * easeOutQuart)
        };
      });

      setAnimatedScores(newScores);
      setAnimatedStats(newStats);

      if (currentStep >= steps) {
        clearInterval(timer);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [examReadinessData]);

  if (!examReadinessData || examReadinessData.length === 0) {
    return null;
  }

  const getScoreColor = (score) => {
    if (score >= 75) return '#2d7a3e';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  const handleViewDetails = () => {
    // Navigate to the course's timetable page
    if (courseId) {
      navigate(`/courses/${courseId}/timetable`);
    } else {
      // Fallback: navigate to the first exam's course
      const firstExam = examReadinessData[0];
      if (firstExam && firstExam.course_id) {
        navigate(`/courses/${firstExam.course_id}/timetable`);
      }
    }
    onClose();
  };

  return (
    <div className="post-quiz-modal-overlay" onClick={onClose}>
      <div className="post-quiz-modal" onClick={(e) => e.stopPropagation()}>
        {/* Logo */}
        <div className="post-quiz-logo">
          <img src="/logo.png" alt="Logo" />
        </div>

        {/* Header */}
        <div className="post-quiz-header">
          <div className="success-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="22" stroke="#2d7a3e" strokeWidth="3" fill="#e8f5e9"/>
              <path d="M14 24L20 30L34 16" stroke="#2d7a3e" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h2 className="post-quiz-title">Exam Readiness Updated!</h2>
          <p className="post-quiz-subtitle">
            Your performance has been recorded and your exam readiness scores have been updated.
          </p>
        </div>

        {/* Exam Cards */}
        <div className="exam-readiness-cards">
          {examReadinessData.map((exam) => {
            const animatedScore = animatedScores[exam.exam_id] || 0;
            const stats = animatedStats[exam.exam_id] || { coverage: 0, accuracy: 0, momentum: 0, tested: 0, weak: 0 };
            const scoreColor = getScoreColor(exam.overall_readiness_score);

            return (
              <div key={exam.exam_id} className="exam-card-premium">
                {/* Exam Header */}
                <div className="exam-card-top">
                  <div className="exam-label">{exam.exam_name}</div>
                </div>
                
                {/* Centered Score */}
                <div className="exam-score-center">
                  <div className="exam-score-large" style={{ color: scoreColor }}>
                    {animatedScore}<span className="percent-sign">%</span>
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="stats-grid">
                  <div className="stat-box">
                    <div className="stat-label">Concepts Tested</div>
                    <div className="stat-value-large">
                      {stats.tested}<span className="stat-total">/{exam.total_flashcards_in_exam}</span>
                    </div>
                  </div>
                  
                  {exam.weak_flashcards && exam.weak_flashcards.length > 0 && (
                    <div className="stat-box weak-box">
                      <div className="stat-label">Weak Concepts</div>
                      <div className="stat-value-large weak-value">{stats.weak}</div>
                    </div>
                  )}
                </div>

                {/* Trinity Pills */}
                <div className="trinity-pills">
                  <div className="pill">
                    <span className="pill-label">Coverage</span>
                    <span className="pill-value">{stats.coverage}%</span>
                  </div>
                  <div className="pill">
                    <span className="pill-label">Accuracy</span>
                    <span className="pill-value">{stats.accuracy}%</span>
                  </div>
                  <div className="pill">
                    <span className="pill-label">Momentum</span>
                    <span className="pill-value">{stats.momentum}%</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Actions */}
        <div className="post-quiz-actions">
          <button className="btn-view-details" onClick={handleViewDetails}>
            View Full Breakdown
          </button>
          <button className="btn-continue" onClick={onClose}>
            Continue
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostQuizReadinessModal;

