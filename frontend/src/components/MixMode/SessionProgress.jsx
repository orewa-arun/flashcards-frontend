/**
 * SessionProgress - Header component displaying session progress
 */

import React from 'react';
import './SessionProgress.css';

const SessionProgress = ({ seenInRound, totalFlashcards, currentRound }) => {
  const progressPercentage = totalFlashcards > 0 
    ? Math.round((seenInRound / totalFlashcards) * 100) 
    : 0;

  return (
    <div className="session-progress-header">
      <div className="progress-info">
        <div className="progress-title">
          <span className="round-label">Round {currentRound}</span>
          <span className="progress-fraction">{seenInRound} / {totalFlashcards}</span>
        </div>
        <div className="progress-bar-container">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
      </div>
      <div className="progress-percentage">{progressPercentage}%</div>
    </div>
  );
};

export default SessionProgress;

