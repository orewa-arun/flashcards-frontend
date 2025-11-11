/**
 * MixModeCard - Premium, highlighted card for Mix Mode
 * 
 * Features:
 * - Larger and more prominent than other options
 * - "Recommended" tag
 * - Premium design with brand colors
 * - Displays exam readiness score preview
 */

import React, { useEffect, useState } from 'react';
import { FaShapes } from 'react-icons/fa';
import { getDeckExamReadiness } from '../../api/mixMode';
import './MixModeCard.css';

const MixModeCard = ({ onClick, courseId, deckId }) => {
  const [readinessScore, setReadinessScore] = useState(null);
  const [isLoadingReadiness, setIsLoadingReadiness] = useState(false);
  
  useEffect(() => {
    const fetchReadiness = async () => {
      if (!courseId || !deckId) return;
      
      setIsLoadingReadiness(true);
      try {
        const data = await getDeckExamReadiness(courseId, [deckId], false);
        setReadinessScore(data.overall_readiness_score);
      } catch (error) {
        console.error('Failed to fetch readiness for MixModeCard:', error);
        // Fail silently - readiness is optional
      } finally {
        setIsLoadingReadiness(false);
      }
    };
    
    fetchReadiness();
  }, [courseId, deckId]);
  
  const getReadinessColor = (score) => {
    if (score < 40) return '#E74C3C';
    if (score < 70) return '#F39C12';
    if (score < 85) return '#27AE60';
    return '#2d7a3e';
  };
  
  return (
    <div className="mix-mode-card" onClick={onClick}>
      {/* Recommended Tag */}
      <div className="recommended-tag">
        <span className="recommended-badge">✨ Recommended</span>
      </div>
      
      {/* Readiness Score Badge */}
      {readinessScore !== null && !isLoadingReadiness && (
        <div className="readiness-badge" style={{ borderColor: getReadinessColor(readinessScore) }}>
          <span className="readiness-label">Readiness</span>
          <span className="readiness-score" style={{ color: getReadinessColor(readinessScore) }}>
            {Math.round(readinessScore)}%
          </span>
        </div>
      )}
      
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

