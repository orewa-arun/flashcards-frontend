/**
 * LectureReadinessModal - Professional per-lecture readiness breakdown
 * 
 * Clean, brand-aligned modal showing readiness scores
 * for each lecture covered by an exam.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FaTimes } from 'react-icons/fa';
import { getLectureReadiness } from '../api/examReadiness';
import './LectureReadinessModal.css';

const LectureReadinessModal = ({ isOpen, onClose, exam, courseId }) => {
  const [lectureScores, setLectureScores] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Track last fetched key to prevent duplicate calls
  const lastFetchKey = useRef('');
  const hasFetched = useRef(false);

  const fetchLectureScores = useCallback(async () => {
    if (!exam?.lectures?.length) {
      setLoading(false);
      return;
    }

    const fetchKey = `${courseId}-${exam.lectures.sort().join(',')}`;
    
    // Skip if already fetched for this combination
    if (lastFetchKey.current === fetchKey && hasFetched.current) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      lastFetchKey.current = fetchKey;
      
      const scores = await getLectureReadiness(courseId, exam.lectures);
      setLectureScores(scores);
      hasFetched.current = true;
    } catch (err) {
      console.error('Error fetching lecture scores:', err);
      setError('Failed to load lecture scores');
      hasFetched.current = false;
    } finally {
      setLoading(false);
    }
  }, [courseId, exam?.lectures]);

  useEffect(() => {
    if (isOpen) {
      fetchLectureScores();
    }
  }, [isOpen, fetchLectureScores]);

  const formatLectureName = (lectureId) => {
    return lectureId
      .replace(/_/g, ' ')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const calculateOverallScore = () => {
    const scores = Object.values(lectureScores);
    if (scores.length === 0) return 0;
    const sum = scores.reduce((acc, score) => acc + score, 0);
    return Math.round(sum / scores.length);
  };

  if (!isOpen) return null;

  const overallScore = calculateOverallScore();

  return (
    <div className="lecture-modal-overlay" onClick={onClose}>
      <div className="lecture-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="lecture-modal-header">
          <div>
            <h2 className="lecture-modal-title">Exam Readiness</h2>
            <p className="lecture-modal-subtitle">{exam?.subject}</p>
          </div>
          <button className="lecture-modal-close" onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>

        {/* Overall Score */}
        <div className="lecture-modal-overall">
          <div className="overall-score-circle">
            <span className="overall-score-value">{loading ? '—' : overallScore}</span>
            <span className="overall-score-percent">%</span>
          </div>
          <p className="overall-score-label">Overall Readiness</p>
        </div>

        {/* Lectures Breakdown */}
        <div className="lecture-modal-content">
          <h3 className="section-title">Lecture Breakdown</h3>
          
          {loading ? (
            <div className="lecture-loading">
              <div className="lecture-loading-spinner"></div>
              <p>Loading...</p>
            </div>
          ) : error ? (
            <div className="lecture-error">
              <p>{error}</p>
              <button onClick={fetchLectureScores}>Retry</button>
            </div>
          ) : exam?.lectures?.length === 0 ? (
            <div className="lecture-empty">
              <p>No lectures assigned to this exam</p>
            </div>
          ) : (
            <div className="lecture-list">
              {exam.lectures.map((lectureId, index) => {
                const score = lectureScores[lectureId] || 0;
                
                return (
                  <div key={lectureId} className="lecture-item">
                    <div className="lecture-info">
                      <span className="lecture-number">{index + 1}</span>
                      <span className="lecture-name">{formatLectureName(lectureId)}</span>
                    </div>
                    <div className="lecture-score-section">
                      <div className="lecture-progress-container">
                        <div 
                          className="lecture-progress-bar"
                          style={{ width: `${score}%` }}
                        />
                      </div>
                      <span className="lecture-score-value">
                        {Math.round(score)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="lecture-modal-footer">
          <p>Based on your quiz performance for each lecture</p>
        </div>
      </div>
    </div>
  );
};

export default LectureReadinessModal;

