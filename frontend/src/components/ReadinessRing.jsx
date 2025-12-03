/**
 * ReadinessRing - Per-Lecture Readiness System
 * 
 * A clean, minimal progress indicator for exam readiness scores.
 * Shows percentage based on average of per-lecture accuracy scores.
 * Click to see breakdown by lecture.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getLectureReadiness } from '../api/examReadiness';
import LectureReadinessModal from './LectureReadinessModal';
import './ReadinessRing.css';

const ReadinessRing = ({ courseId, examId, examName, lectures = [], size = 'md' }) => {
  const [lectureScores, setLectureScores] = useState({});
  const [overallScore, setOverallScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  
  // Track if we've already fetched for this combination
  const fetchedRef = useRef(false);
  const lastFetchKey = useRef('');

  // Create a stable key for the current props
  const fetchKey = `${courseId}-${lectures.sort().join(',')}`;

  const loadReadiness = useCallback(async () => {
    // If no lectures, show 0%
    if (!lectures || lectures.length === 0) {
      setOverallScore(0);
      setLoading(false);
      return;
    }

    // Prevent duplicate fetches for the same data
    if (lastFetchKey.current === fetchKey && fetchedRef.current) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      lastFetchKey.current = fetchKey;
      fetchedRef.current = true;
      
      const scores = await getLectureReadiness(courseId, lectures);
      setLectureScores(scores);
      
      // Calculate overall score as average of lecture scores
      const scoreValues = Object.values(scores);
      if (scoreValues.length > 0) {
        const average = scoreValues.reduce((sum, s) => sum + s, 0) / scoreValues.length;
        setOverallScore(Math.round(average));
      } else {
        setOverallScore(0);
      }
    } catch (err) {
      console.error('Error loading readiness:', err);
      setError('Failed to load');
      setOverallScore(0);
      fetchedRef.current = false; // Allow retry on error
    } finally {
      setLoading(false);
    }
  }, [courseId, fetchKey, lectures]);

  useEffect(() => {
    loadReadiness();
  }, [loadReadiness]);

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
  if (error) {
    return (
      <div className={`readiness-badge size-${size} status-error`}>
        <div className="badge-content">
          <span className="badge-icon">⚠️</span>
          <span className="badge-score">—</span>
        </div>
      </div>
    );
  }

  const color = getColorForScore(overallScore);
  const urgencyClass = getUrgencyClass(overallScore);
  const label = getUrgencyLabel(overallScore);

  // Exam object for the modal
  const examData = {
    exam_id: examId,
    subject: examName,
    lectures: lectures
  };

  const handleClick = (e) => {
    e.stopPropagation();
    setShowModal(true);
  };

  return (
    <>
      <button 
        type="button"
        className={`readiness-badge size-${size} status-${urgencyClass} clickable`}
        onClick={handleClick}
        style={{ '--score-color': color }}
        aria-label={`Exam readiness: ${overallScore}% - ${label}. Click for details.`}
      >
        <div className="badge-content">
          <div className="badge-score">{overallScore}%</div>
          <div className="badge-label">{label}</div>
        </div>
        <div 
          className="badge-progress" 
          style={{ width: `${overallScore}%` }}
        ></div>
      </button>

      <LectureReadinessModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        exam={examData}
        courseId={courseId}
      />
    </>
  );
};

export default ReadinessRing;
