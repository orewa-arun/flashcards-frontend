/**
 * ReadinessBreakdownModal - The detailed Trinity view.
 * 
 * This modal transforms raw scores into actionable intelligence,
 * guiding users to their next strategic move.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './ReadinessBreakdownModal.css';

const ReadinessBreakdownModal = ({ readiness, examName, courseId, onClose, onRefresh }) => {
  const navigate = useNavigate();
  const [animatedScore, setAnimatedScore] = useState(0);
  const [animatedBreakdown, setAnimatedBreakdown] = useState({
    coverage: 0,
    mastery: 0,
    momentum: 0
  });

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

  // Animate numbers on mount
  useEffect(() => {
    const duration = 1500;
    const steps = 60;
    const interval = duration / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const progress = currentStep / steps;
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);

      setAnimatedScore(Math.round(overall_score * easeOutQuart));
      setAnimatedBreakdown({
        coverage: Math.round(breakdown.coverage.score * easeOutQuart),
        mastery: Math.round(breakdown.mastery.score * easeOutQuart),
        momentum: Math.round(breakdown.momentum.score * easeOutQuart)
      });

      if (currentStep >= steps) {
        clearInterval(timer);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [overall_score, breakdown]);

  const getColorForScore = (score) => {
    if (score >= 75) return '#10b981'; // Green
    if (score >= 50) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
  };

  const getPillarIcon = (pillarName) => {
    const icons = {
      coverage: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 19.5C4 18.837 4.26339 18.2011 4.73223 17.7322C5.20107 17.2634 5.83696 17 6.5 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M6.5 2H20V22H6.5C5.83696 22 5.20107 21.7366 4.73223 21.2678C4.26339 20.7989 4 20.163 4 19.5V4.5C4 3.83696 4.26339 3.20107 4.73223 2.73223C5.20107 2.26339 5.83696 2 6.5 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      ),
      mastery: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
          <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="2"/>
          <circle cx="12" cy="12" r="2" fill="currentColor"/>
        </svg>
      ),
      momentum: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )
    };
    return icons[pillarName] || (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2"/>
        <rect x="14" y="3" width="7" height="7" stroke="currentColor" strokeWidth="2"/>
        <rect x="3" y="14" width="7" height="7" stroke="currentColor" strokeWidth="2"/>
        <rect x="14" y="14" width="7" height="7" stroke="currentColor" strokeWidth="2"/>
      </svg>
    );
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
    const percentage = animatedBreakdown[pillarName];
    const barWidth = `${percentage}%`;

    return (
      <div className="pillar-card" key={pillarName}>
        <div className="pillar-header">
          <div className="pillar-icon-wrapper">
            {getPillarIcon(pillarName)}
          </div>
          <div className="pillar-info">
            <h3 className="pillar-title">{getPillarTitle(pillarName)}</h3>
            <p className="pillar-details">{pillarData.details}</p>
          </div>
          <div className="pillar-percentage">{percentage}%</div>
        </div>
        <div className="pillar-bar-container">
          <div 
            className="pillar-bar" 
            style={{ 
              width: barWidth
            }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="readiness-modal-overlay" onClick={onClose}>
      <div className="readiness-modal" onClick={(e) => e.stopPropagation()}>
        {/* Logo */}
        <div className="modal-logo">
          <img src="/logo.png" alt="Logo" />
        </div>

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

        {/* Overall Score Gauge */}
        <div className="modal-overall-section">
          <div className="gauge-container">
            <svg viewBox="0 0 200 120" className="gauge-svg">
              {/* Background arc */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                stroke="rgba(255, 255, 255, 0.1)"
                strokeWidth="20"
                strokeLinecap="round"
                />
              {/* Animated progress arc */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                  fill="none"
                stroke="url(#gaugeGradient)"
                strokeWidth="20"
                  strokeLinecap="round"
                strokeDasharray={`${(animatedScore / 100) * 251.2} 251.2`}
                className="gauge-progress"
                />
              {/* Gradient definition */}
              <defs>
                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#007CF0" />
                  <stop offset="100%" stopColor="#00DFD8" />
                </linearGradient>
              </defs>
              </svg>
            <div className="gauge-content">
              <div className="gauge-score">{animatedScore}%</div>
              <div className="gauge-label">Overall Readiness</div>
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
              {urgency_level === 'high' && (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10.29 3.86L1.82 18C1.64537 18.3024 1.55296 18.6453 1.55199 18.9945C1.55101 19.3437 1.64151 19.6871 1.81445 19.9905C1.98738 20.2939 2.23675 20.5467 2.53773 20.7239C2.83871 20.901 3.18082 20.9962 3.53 21H20.47C20.8192 20.9962 21.1613 20.901 21.4623 20.7239C21.7633 20.5467 22.0126 20.2939 22.1856 19.9905C22.3585 19.6871 22.449 19.3437 22.448 18.9945C22.447 18.6453 22.3546 18.3024 22.18 18L13.71 3.86C13.5317 3.56611 13.2807 3.32312 12.9812 3.15448C12.6817 2.98585 12.3437 2.89725 12 2.89725C11.6563 2.89725 11.3183 2.98585 11.0188 3.15448C10.7193 3.32312 10.4683 3.56611 10.29 3.86Z" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                  <path d="M12 9V13" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="12" cy="17" r="1" fill="#ef4444"/>
                </svg>
              )}
              {urgency_level === 'medium' && (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2V6" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 18V22" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4.93 4.93L7.76 7.76" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16.24 16.24L19.07 19.07" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 12H6" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M18 12H22" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4.93 19.07L7.76 16.24" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M16.24 7.76L19.07 4.93" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="#f59e0b" strokeWidth="2" fill="none"/>
                </svg>
              )}
              {urgency_level === 'low' && (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 11.08V12C21.9988 14.1564 21.3005 16.2547 20.0093 17.9818C18.7182 19.709 16.9033 20.9725 14.8354 21.5839C12.7674 22.1953 10.5573 22.1219 8.53447 21.3746C6.51168 20.6273 4.78465 19.2461 3.61096 17.4371C2.43727 15.628 1.87979 13.4881 2.02168 11.3363C2.16356 9.18455 2.99721 7.13631 4.39828 5.49706C5.79935 3.85781 7.69279 2.71537 9.79619 2.24013C11.8996 1.7649 14.1003 1.98232 16.07 2.85999" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M22 4L12 14.01L9 11.01" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
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

