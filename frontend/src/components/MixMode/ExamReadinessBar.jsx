/**
 * ExamReadinessBar Component
 * 
 * Displays the user's exam readiness score as a primary progress indicator
 * with animated transitions and optional Trinity breakdown.
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

    const duration = 800; // ms
    const steps = 30;
    const increment = score / steps;
    const stepDuration = duration / steps;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setAnimatedScore(score);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.round(increment * currentStep));
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [score]);

  // Determine color based on score
  const getScoreColor = (scoreValue) => {
    if (scoreValue < 40) return 'low';
    if (scoreValue < 70) return 'medium';
    if (scoreValue < 85) return 'good';
    return 'excellent';
  };

  const scoreColor = getScoreColor(animatedScore);

  // Get status message
  const getStatusMessage = (scoreValue) => {
    if (scoreValue < 40) return 'Needs Work';
    if (scoreValue < 70) return 'Making Progress';
    if (scoreValue < 85) return 'Almost There';
    return 'Exam Ready!';
  };

  if (isLoading) {
    return (
      <div className="exam-readiness-bar loading">
        <div className="readiness-skeleton">
          <div className="skeleton-header"></div>
          <div className="skeleton-bar"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`exam-readiness-bar ${scoreColor}`}>
      <div className="readiness-container">
        <div className="readiness-header">
          <div className="readiness-label-group">
            <span className="readiness-label">Exam Readiness</span>
            <span className="readiness-status">{getStatusMessage(animatedScore)}</span>
          </div>
          <div className="readiness-score-display">
            <span className="readiness-score">{animatedScore}</span>
            <span className="readiness-percent">%</span>
          </div>
        </div>
        
        <div className="readiness-progress-track">
          <div 
            className={`readiness-progress-fill ${scoreColor}`}
            style={{ width: `${animatedScore}%` }}
          >
            <div className="progress-shine"></div>
          </div>
        </div>

        {readinessData && (
          <button 
            className="breakdown-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? "Hide breakdown" : "Show breakdown"}
          >
            <span className="toggle-text">
              {isExpanded ? 'Hide' : 'Show'} Trinity Breakdown
            </span>
            <svg 
              className={`toggle-icon ${isExpanded ? 'expanded' : ''}`}
              width="16" 
              height="16" 
              viewBox="0 0 16 16" 
              fill="none"
            >
              <path 
                d="M4 6L8 10L12 6" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </button>
        )}

        {isExpanded && readinessData && (
          <div className="readiness-breakdown">
            <div className="pillar">
              <div className="pillar-header">
                <svg className="pillar-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span className="pillar-name">Coverage</span>
              </div>
              <div className="pillar-bar-container">
                <div className="pillar-bar">
                  <div 
                    className="pillar-bar-fill coverage"
                    style={{ width: `${coverage}%` }}
                  ></div>
                </div>
                <span className="pillar-value">{coverage}%</span>
              </div>
            </div>
            
            <div className="pillar">
              <div className="pillar-header">
                <svg className="pillar-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="2" fill="currentColor"/>
                </svg>
                <span className="pillar-name">Accuracy</span>
              </div>
              <div className="pillar-bar-container">
                <div className="pillar-bar">
                  <div 
                    className="pillar-bar-fill accuracy"
                    style={{ width: `${accuracy}%` }}
                  ></div>
                </div>
                <span className="pillar-value">{accuracy}%</span>
              </div>
            </div>
            
            <div className="pillar">
              <div className="pillar-header">
                <svg className="pillar-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span className="pillar-name">Momentum</span>
              </div>
              <div className="pillar-bar-container">
                <div className="pillar-bar">
                  <div 
                    className="pillar-bar-fill momentum"
                    style={{ width: `${momentum}%` }}
                  ></div>
                </div>
                <span className="pillar-value">{momentum}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExamReadinessBar;

