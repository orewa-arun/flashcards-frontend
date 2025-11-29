/**
 * ExamReadinessBar Component
 * 
 * A modern, clean exam readiness indicator with Trinity breakdown.
 * Redesigned for clarity and visual impact.
 */

import React, { useState, useEffect } from 'react';
import './ExamReadinessBar.css';

const ExamReadinessBar = ({ readinessData, isLoading, showBreakdown = false }) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [isExpanded, setIsExpanded] = useState(showBreakdown);

  const score = readinessData?.overall_readiness_score || 0;
  const coverage = readinessData?.coverage_factor ? Math.round(readinessData.coverage_factor * 100) : 0;
  const accuracy = readinessData?.accuracy_factor ? Math.round(readinessData.accuracy_factor * 100) : 0;
  const momentum = readinessData?.momentum_factor ? Math.round(readinessData.momentum_factor * 100) : 0;

  // Animate score on mount and when it changes
  useEffect(() => {
    if (score === 0) {
      setAnimatedScore(0);
      return;
    }

    const duration = 800;
    const steps = 30;
    const increment = score / steps;
    const stepDuration = duration / steps;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setAnimatedScore(Math.round(score * 100) / 100);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.round(increment * currentStep * 100) / 100);
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [score]);

  const getScoreLevel = (scoreValue) => {
    if (scoreValue < 25) return { level: 'critical', label: 'Needs Work', color: '#dc2626' };
    if (scoreValue < 50) return { level: 'low', label: 'Getting Started', color: '#ea580c' };
    if (scoreValue < 75) return { level: 'medium', label: 'Making Progress', color: '#eab308' };
    if (scoreValue < 90) return { level: 'good', label: 'Almost There', color: '#22c55e' };
    return { level: 'excellent', label: 'Exam Ready!', color: '#16a34a' };
  };

  const scoreInfo = getScoreLevel(animatedScore);

  if (isLoading) {
    return (
      <div className="readiness-card">
        <div className="readiness-card__loading">
          <div className="loading-pulse"></div>
          <div className="loading-pulse loading-pulse--short"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="readiness-card">
      {/* Main Score Section */}
      <div className="readiness-card__main">
        <div className="readiness-card__info">
          <span className="readiness-card__title">EXAM READINESS</span>
          <span className="readiness-card__status" style={{ color: scoreInfo.color }}>
            {scoreInfo.label}
          </span>
        </div>
        <div className="readiness-card__score" style={{ color: scoreInfo.color }}>
          <span className="score-value">{animatedScore.toFixed(animatedScore % 1 === 0 ? 0 : 2)}</span>
          <span className="score-percent">%</span>
        </div>
      </div>

      {/* Main Progress Bar */}
      <div className="readiness-card__progress">
        <div 
          className="readiness-card__progress-fill"
          style={{ 
            width: `${Math.min(animatedScore, 100)}%`,
            backgroundColor: scoreInfo.color
          }}
        />
      </div>

      {/* Toggle Button */}
      {readinessData && (
        <button 
          className="readiness-card__toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Hide' : 'Show'} Trinity Breakdown
          <svg 
            className={`toggle-chevron ${isExpanded ? 'toggle-chevron--up' : ''}`}
            width="16" 
            height="16" 
            viewBox="0 0 16 16"
          >
            <path 
              d="M4 6L8 10L12 6" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
        </button>
      )}

      {/* Trinity Breakdown */}
      {isExpanded && readinessData && (
        <div className="trinity-breakdown">
          <TrinityPillar 
            type="coverage"
            name="Coverage"
            value={coverage}
            description="Flashcards attempted"
            color="#2d7a3e"
          />
          <TrinityPillar 
            type="accuracy"
            name="Accuracy"
            value={accuracy}
            description="Questions answered correctly"
            color="#0891b2"
          />
          <TrinityPillar 
            type="momentum"
            name="Momentum"
            value={momentum}
            description="Recent performance trend"
            color="#7c3aed"
          />
        </div>
      )}
    </div>
  );
};

const TrinityIcon = ({ type, color }) => {
  switch (type) {
    case 'coverage':
      // Book / document icon
      return (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect x="5" y="3" width="14" height="18" rx="2" stroke={color} strokeWidth="1.8" />
          <path d="M9 7H15" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
          <path d="M9 11H15" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
          <path d="M9 15H13" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      );
    case 'accuracy':
      // Target icon
      return (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="12" cy="12" r="8" stroke={color} strokeWidth="1.8" />
          <circle cx="12" cy="12" r="4.5" stroke={color} strokeWidth="1.8" />
          <circle cx="12" cy="12" r="1.4" fill={color} />
          <path
            d="M12 4V2M20 12H22M12 20V22M4 12H2"
            stroke={color}
            strokeWidth="1.4"
            strokeLinecap="round"
          />
        </svg>
      );
    case 'momentum':
    default:
      // Lightning / momentum icon
      return (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M11 3L5 13H11L9.5 21L19 9H13L15 3H11Z"
            stroke={color}
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
  }
};

const TrinityPillar = ({ type, name, value, description, color }) => {
  return (
    <div className="trinity-pillar">
      <div className="trinity-pillar__header">
        <span className="trinity-pillar__icon">
          <TrinityIcon type={type} color={color} />
        </span>
        <div className="trinity-pillar__info">
          <span className="trinity-pillar__name">{name}</span>
          <span className="trinity-pillar__desc">{description}</span>
        </div>
        <span className="trinity-pillar__value" style={{ color }}>
          {value}%
        </span>
      </div>
      <div className="trinity-pillar__bar">
        <div 
          className="trinity-pillar__bar-fill"
          style={{ 
            width: `${value}%`,
            backgroundColor: color
          }}
        />
      </div>
    </div>
  );
};

export default ExamReadinessBar;
