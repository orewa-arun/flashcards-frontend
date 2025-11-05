/**
 * ReadinessBreakdownModal - The detailed Trinity view.
 * 
 * This modal transforms raw scores into actionable intelligence,
 * guiding users to their next strategic move.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ReadinessBreakdownModal.css';

const ReadinessBreakdownModal = ({ readiness, examName, courseId, onClose, onRefresh }) => {
  const navigate = useNavigate();

  const {
    overall_score,
    breakdown,
    recommendation,
    action_type,
    urgency_level,
    covered_lectures,
    uncovered_lectures,
    weak_lectures
  } = readiness;

  const getColorForScore = (score) => {
    if (score >= 75) return '#10b981'; // Green
    if (score >= 50) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
  };

  const getPillarIcon = (pillarName) => {
    const icons = {
      coverage: '📚',
      mastery: '🎯',
      momentum: '⚡'
    };
    return icons[pillarName] || '📊';
  };

  const getPillarTitle = (pillarName) => {
    const titles = {
      coverage: 'Coverage',
      mastery: 'Mastery',
      momentum: 'Momentum'
    };
    return titles[pillarName] || pillarName;
  };

  const handleAction = () => {
    // Navigate to appropriate quiz based on action_type
    if (action_type === 'coverage' && uncovered_lectures.length > 0) {
      // Navigate to first uncovered lecture's quiz
      const lectureId = uncovered_lectures[0];
      navigate(`/courses/${courseId}/${lectureId}/quiz`);
    } else if (action_type === 'mastery' && weak_lectures.length > 0) {
      // Navigate to first weak lecture's quiz
      const lectureId = weak_lectures[0];
      navigate(`/courses/${courseId}/${lectureId}/quiz`);
    } else if (action_type === 'momentum') {
      // Navigate to any recent lecture's quiz for quick review
      const lectureId = covered_lectures[0] || uncovered_lectures[0];
      if (lectureId) {
        navigate(`/courses/${courseId}/${lectureId}/quiz`);
      }
    }
    onClose();
  };

  const getActionButtonText = () => {
    if (action_type === 'coverage') return 'Start Quiz on Uncovered Topics';
    if (action_type === 'mastery') return 'Practice Weak Topics';
    if (action_type === 'momentum') return 'Start Quick Review';
    if (action_type === 'maintenance') return 'Continue Practicing';
    return 'Start Quiz';
  };

  const renderPillar = (pillarName, pillarData) => {
    const color = getColorForScore(pillarData.score);
    const percentage = pillarData.score;
    const barWidth = `${percentage}%`;

    return (
      <div className="pillar-card" key={pillarName}>
        <div className="pillar-header">
          <div className="pillar-icon">{getPillarIcon(pillarName)}</div>
          <div className="pillar-info">
            <h3 className="pillar-title">{getPillarTitle(pillarName)}</h3>
            <p className="pillar-details">{pillarData.details}</p>
          </div>
        </div>
        <div className="pillar-bar-container">
          <div 
            className="pillar-bar" 
            style={{ 
              width: barWidth, 
              backgroundColor: color 
            }}
          >
            <span className="pillar-score">{Math.round(percentage)}%</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="readiness-modal-overlay" onClick={onClose}>
      <div className="readiness-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-section">
            <h2 className="modal-title">Exam Readiness</h2>
            <p className="modal-subtitle">{examName}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Overall Score Badge */}
        <div className="modal-overall-section">
          <div 
            className="modal-score-badge"
            style={{ '--badge-color': getColorForScore(overall_score) }}
          >
            <div className="badge-ring">
              <svg viewBox="0 0 120 120">
                <circle
                  cx="60"
                  cy="60"
                  r="54"
                  fill="none"
                  stroke="rgba(255, 255, 255, 0.15)"
                  strokeWidth="8"
                />
                <circle
                  cx="60"
                  cy="60"
                  r="54"
                  fill="none"
                  stroke={getColorForScore(overall_score)}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * 54}
                  strokeDashoffset={(1 - overall_score / 100) * 2 * Math.PI * 54}
                  transform="rotate(-90 60 60)"
                  className="animated-ring"
                />
              </svg>
            </div>
            <div className="badge-score-content">
              <div className="badge-score-value">{Math.round(overall_score)}%</div>
              <div className="badge-score-label">Overall Readiness</div>
            </div>
          </div>
        </div>

        {/* Trinity Breakdown */}
        <div className="modal-pillars-section">
          <h3 className="section-title">The Trinity Breakdown</h3>
          {renderPillar('coverage', breakdown.coverage)}
          {renderPillar('mastery', breakdown.mastery)}
          {renderPillar('momentum', breakdown.momentum)}
        </div>

        {/* Recommendation */}
        <div className="modal-recommendation-section">
          <div className={`recommendation-card ${urgency_level}`}>
            <div className="recommendation-icon">
              {urgency_level === 'high' && '🚨'}
              {urgency_level === 'medium' && '💡'}
              {urgency_level === 'low' && '✅'}
            </div>
            <div className="recommendation-content">
              <h4 className="recommendation-title">Next Step</h4>
              <p className="recommendation-text">{recommendation}</p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="modal-actions">
          <button 
            className="action-btn primary"
            onClick={handleAction}
            disabled={action_type === 'configuration'}
          >
            {getActionButtonText()}
          </button>
          <button className="action-btn secondary" onClick={onRefresh}>
            Refresh Score
          </button>
        </div>

        {/* Metadata Footer */}
        <div className="modal-metadata">
          <div className="metadata-item">
            <span className="metadata-label">Covered Lectures:</span>
            <span className="metadata-value">{covered_lectures.length}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Uncovered:</span>
            <span className="metadata-value">{uncovered_lectures.length}</span>
          </div>
          {weak_lectures.length > 0 && (
            <div className="metadata-item weak">
              <span className="metadata-label">Weak Areas:</span>
              <span className="metadata-value">{weak_lectures.length}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReadinessBreakdownModal;

