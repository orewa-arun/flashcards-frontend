/**
 * MixModeCard - Premium, highlighted card for Mix Mode
 * 
 * Features:
 * - Larger and more prominent than other options
 * - "Recommended" tag
 * - Premium design with brand colors
 */

import React from 'react';
import { FaShapes } from 'react-icons/fa';
import './MixModeCard.css';

const MixModeCard = ({ onClick }) => {
  return (
    <div className="mix-mode-card" onClick={onClick}>
      {/* Recommended Tag */}
      <div className="recommended-tag">
        <span className="recommended-badge">✨ Recommended</span>
      </div>
      
      {/* Card Content */}
      <div className="mix-mode-content">
        <div className="mix-mode-icon">
          <FaShapes />
        </div>
        
        <h2 className="mix-mode-title">Mix Mode</h2>
        
        <p className="mix-mode-tagline">Adaptive Learning Experience</p>
        
        <p className="mix-mode-description">
          Our intelligent system adapts to your performance in real-time. 
          Questions and flashcards are personalized based on importance and 
          your comfort level with each concept.
        </p>
        
        <div className="mix-mode-features">
          <div className="mix-feature">
            <span className="feature-icon">🎯</span>
            <span className="feature-text">Smart Prioritization</span>
          </div>
          <div className="mix-feature">
            <span className="feature-icon">📈</span>
            <span className="feature-text">Adaptive Difficulty</span>
          </div>
          <div className="mix-feature">
            <span className="feature-icon">💡</span>
            <span className="feature-text">Instant Remediation</span>
          </div>
        </div>
        
        <button className="mix-mode-button">
          Start Mix Mode →
        </button>
      </div>
      
      {/* Premium Glow Effect */}
      <div className="mix-mode-glow"></div>
    </div>
  );
};

export default MixModeCard;

