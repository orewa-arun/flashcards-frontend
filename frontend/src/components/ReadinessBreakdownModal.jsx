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
    accuracy: 0,
    momentum: 0
  });

  const {
    overall_readiness_score,
    coverage_factor,
    accuracy_factor,
    momentum_factor,
    recommendation,
    action_type,
    urgency_level,
    total_flashcards_in_exam,
    flashcards_attempted,
    weak_flashcards
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

      setAnimatedScore(Math.round(overall_readiness_score * easeOutQuart));
      setAnimatedBreakdown({
        coverage: Math.round((coverage_factor * 100) * easeOutQuart),
        accuracy: Math.round((accuracy_factor * 100) * easeOutQuart),
        momentum: Math.round((momentum_factor * 100) * easeOutQuart)
      });

      if (currentStep >= steps) {
        clearInterval(timer);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [overall_readiness_score, coverage_factor, accuracy_factor, momentum_factor]);

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
      accuracy: (
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
      accuracy: 'Accuracy',
      momentum: 'Momentum'
    };
    return titles[pillarName] || pillarName;
  };

  const handleAction = () => {
    // TODO: This navigation logic might need updating based on new V2 data
    if (action_type === 'mastery' && weak_flashcards.length > 0) {
      navigate(`/weak-concepts`);
    } else {
      navigate(`/courses/${courseId}`);
    }
    onClose();
  };

  const getActionButtonText = () => {
    if (action_type === 'coverage') return 'Start Quiz on Uncovered Topics';
    if (action_type === 'accuracy') return 'Practice Weak Concepts';
    if (action_type === 'momentum') return 'Start Quick Review';
    if (action_type === 'maintenance') return 'Continue Practicing';
    return 'Start Quiz';
  };
  
  const pillarDetails = {
    coverage: `You've attempted ${flashcards_attempted} of ${total_flashcards_in_exam} flashcards.`,
    accuracy: `Based on your performance on questions of varying difficulty.`,
    momentum: `Reflects your recent performance trend.`
  };

  const renderPillar = (pillarName, factor) => {
    const score = factor * 100;
    const color = getColorForScore(score);
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
            <p className="pillar-details">{pillarDetails[pillarName]}</p>
          </div>
          <div className="pillar-percentage">{percentage}%</div>
        </div>
        <div className="pillar-bar-container">
          <div 
            className="pillar-bar" 
            style={{ 
              width: barWidth,
              backgroundColor: color
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
          {renderPillar('coverage', coverage_factor)}
          {renderPillar('accuracy', accuracy_factor)}
          {renderPillar('momentum', momentum_factor)}
        </div>

        {/* Recommendation */}
        <div className="modal-recommendation-section">
          <div className={`recommendation-card ${urgency_level || 'low'}`}>
            <div className="recommendation-icon">
             {/* Icons can be simplified or kept if needed */}
            </div>
            <div className="recommendation-content">
              <h4 className="recommendation-title">Next Step</h4>
              <p className="recommendation-text">{recommendation || "Keep up the great work!"}</p>
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
            <span className="metadata-label">Total Flashcards:</span>
            <span className="metadata-value">{total_flashcards_in_exam}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Attempted:</span>
            <span className="metadata-value">{flashcards_attempted}</span>
          </div>
          {weak_flashcards && weak_flashcards.length > 0 && (
            <div className="metadata-item weak">
              <span className="metadata-label">Weak Areas:</span>
              <span className="metadata-value">{weak_flashcards.length}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReadinessBreakdownModal;

