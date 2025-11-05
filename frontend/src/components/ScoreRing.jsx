/**
 * ScoreRing - Simple percentage display ring
 * 
 * A clean, minimal progress indicator for quiz scores.
 * Shows percentage with color-coded urgency.
 */
import React from 'react';
import './ScoreRing.css';

const ScoreRing = ({ score, size = 'md' }) => {
  const getColorForScore = (score) => {
    if (score >= 75) return '#10b981'; // Green
    if (score >= 50) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
  };

  const getUrgencyClass = (score) => {
    if (score >= 75) return 'ready';
    if (score >= 50) return 'needs-work';
    return 'critical';
  };

  const normalizedScore = Math.min(100, Math.max(0, score));
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;
  const color = getColorForScore(normalizedScore);
  const urgencyClass = getUrgencyClass(normalizedScore);

  const sizeMap = {
    sm: { width: 60, fontSize: '14px', strokeWidth: 6 },
    md: { width: 80, fontSize: '16px', strokeWidth: 6 },
    lg: { width: 100, fontSize: '20px', strokeWidth: 7 }
  };

  const dimensions = sizeMap[size] || sizeMap.md;

  return (
    <div 
      className={`score-ring score-ring-${size} score-ring-${urgencyClass}`}
      style={{ width: dimensions.width, height: dimensions.width }}
    >
      <svg 
        width={dimensions.width} 
        height={dimensions.width}
        className="score-ring-svg"
      >
        {/* Background circle */}
        <circle
          cx={dimensions.width / 2}
          cy={dimensions.width / 2}
          r="45"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={dimensions.strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={dimensions.width / 2}
          cy={dimensions.width / 2}
          r="45"
          fill="none"
          stroke={color}
          strokeWidth={dimensions.strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${dimensions.width / 2} ${dimensions.width / 2})`}
          className="score-ring-progress"
        />
      </svg>
      <div 
        className="score-ring-text"
        style={{ fontSize: dimensions.fontSize }}
      >
        <span className="score-ring-percentage">{Math.round(normalizedScore)}%</span>
      </div>
    </div>
  );
};

export default ScoreRing;

