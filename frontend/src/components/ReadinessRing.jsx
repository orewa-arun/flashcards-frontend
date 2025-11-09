/**
 * ReadinessRing - Completely Redesigned
 * 
 * A clean, minimal progress indicator for exam readiness scores.
 * Shows percentage with color-coded urgency and click-to-expand details.
 */
import React, { useState, useEffect } from 'react';
import { getExamReadiness } from '../api/examReadiness';
import ReadinessBreakdownModal from './ReadinessBreakdownModal';
import './ReadinessRing.css';

const ReadinessRing = ({ courseId, examId, examName, size = 'md' }) => {
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadReadiness();
  }, [courseId, examId]);

  const loadReadiness = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getExamReadiness(courseId, examId);
      setReadiness(data);
    } catch (err) {
      console.error('Error loading readiness:', err);
      setError('Failed to load');
    } finally {
      setLoading(false);
    }
  };

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

  const getUrgencyLabel = (score) => {
    if (score >= 75) return 'Ready';
    if (score >= 50) return 'Needs Work';
    return 'Critical';
  };

  // Loading state
  if (loading) {
    return (
      <div className={`readiness-badge size-${size}`}>
        <div className="readiness-shimmer"></div>
      </div>
    );
  }

  // Error state
  if (error || !readiness) {
    return (
      <div className={`readiness-badge size-${size} status-error`}>
        <div className="badge-content">
          <span className="badge-icon">⚠️</span>
          <span className="badge-score">—</span>
        </div>
      </div>
    );
  }

  const { overall_readiness_score } = readiness;
  const overall_score = overall_readiness_score; // Use this variable for consistency
  const color = getColorForScore(overall_score);
  const urgencyClass = getUrgencyClass(overall_score);
  const label = getUrgencyLabel(overall_score);

  return (
    <>
      <div 
        className={`readiness-badge size-${size} status-${urgencyClass} clickable`}
        onClick={() => setShowModal(true)}
        style={{ '--score-color': color }}
      >
        <div className="badge-content">
          <div className="badge-score">{Math.round(overall_score)}%</div>
          <div className="badge-label">{label}</div>
        </div>
        <div 
          className="badge-progress" 
          style={{ width: `${overall_score}%` }}
        ></div>
      </div>

      {showModal && (
        <ReadinessBreakdownModal
          readiness={readiness}
          examName={examName}
          courseId={courseId}
          onClose={() => setShowModal(false)}
          onRefresh={loadReadiness}
        />
      )}
    </>
  );
};

export default ReadinessRing;
