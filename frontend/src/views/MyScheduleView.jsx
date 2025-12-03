/**
 * MyScheduleView - The Academic Planner ($5M Redesign)
 * Radical redesign: Integrated intelligence, chronological narrative, brand-aligned
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaCalendarAlt, FaClock, FaBook, FaExclamationTriangle, FaCheckCircle } from 'react-icons/fa';
import { getMySchedule } from '../api/timetable';
import { getUserProfile } from '../api/profile';
import ReadinessRing from '../components/ReadinessRing';
import './MyScheduleView.css';

const MyScheduleView = () => {
  const navigate = useNavigate();
  
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [countdowns, setCountdowns] = useState({});

  useEffect(() => {
    loadSchedule();
  }, []);

  // Live countdown timer
  useEffect(() => {
    if (!schedule?.exams) return;

    const updateCountdowns = () => {
      const newCountdowns = {};
      schedule.exams.forEach((exam, index) => {
        const now = new Date();
        const examDate = new Date(exam.date_ist);
        const diffMillis = examDate - now;

        if (diffMillis > 0) {
          const days = Math.floor(diffMillis / (1000 * 60 * 60 * 24));
          const hours = Math.floor((diffMillis % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          const minutes = Math.floor((diffMillis % (1000 * 60 * 60)) / (1000 * 60));
          const seconds = Math.floor((diffMillis % (1000 * 60)) / 1000);
          newCountdowns[index] = { days, hours, minutes, seconds };
        } else {
          newCountdowns[index] = null; // Past exam
        }
      });
      setCountdowns(newCountdowns);
    };

    updateCountdowns();
    const intervalId = setInterval(updateCountdowns, 1000);

    return () => clearInterval(intervalId);
  }, [schedule]);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      const data = await getMySchedule();
      
      // Fallback: if backend didn't include enrolled_courses, fetch from profile
      if (!data || typeof data.enrolled_courses === 'undefined') {
        try {
          const profile = await getUserProfile();
          setSchedule({ exams: data?.exams || [], enrolled_courses: profile?.enrolled_courses || [] });
        } catch (e) {
          setSchedule(data || { exams: [], enrolled_courses: [] });
        }
      } else {
        setSchedule(data);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load schedule');
      console.error('Error loading schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const formatCountdown = (countdown) => {
    if (!countdown) return null;
    const parts = [];
    if (countdown.days > 0) {
      parts.push(`${String(countdown.days).padStart(2, '0')}d`);
    }
    parts.push(`${String(countdown.hours).padStart(2, '0')}h`);
    parts.push(`${String(countdown.minutes).padStart(2, '0')}m`);
    parts.push(`${String(countdown.seconds).padStart(2, '0')}s`);
    return parts.join(' ');
  };

  if (loading) {
    return (
      <div className="my-schedule-loading">
        <div className="loading-spinner"></div>
        <p>Loading your planner...</p>
      </div>
    );
  }

  return (
    <div className="my-schedule-view">
      {/* Elegant Header */}
      <div className="schedule-header" style={{ animation: 'none', transform: 'none' }}>
        <div className="header-content" style={{ animation: 'none', transform: 'none' }}>
          <h1 className="page-title" style={{ animation: 'none', transform: 'none' }}>
            <FaCalendarAlt className="title-icon" style={{ animation: 'none', transform: 'none' }} />
            My Academic Planner
          </h1>
          <p className="page-subtitle" style={{ animation: 'none', transform: 'none' }}>
            Your upcoming deadlines and exam readiness, all in one place
          </p>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* Schedule Content */}
      <div className="schedule-content">
        {!schedule || schedule.enrolled_courses?.length === 0 ? (
          <div className="empty-state" style={{ animation: 'none', transform: 'none' }}>
            <FaCalendarAlt className="empty-icon" style={{ animation: 'none', transform: 'none' }} />
            <h2 style={{ animation: 'none', transform: 'none' }}>No Courses Enrolled</h2>
            <p style={{ animation: 'none', transform: 'none' }}>Click the <strong>"Enroll"</strong> button on any course page to add it to your planner</p>
            <button 
              className="browse-courses-btn"
              onClick={() => navigate('/courses')}
            >
              <FaBook /> Browse Courses Now
            </button>
          </div>
        ) : schedule.exams?.length === 0 ? (
          <div className="empty-state">
            <FaCalendarAlt className="empty-icon" />
            <h2>No Exams Scheduled Yet</h2>
            <p>Your enrolled courses don't have exam dates set yet</p>
          </div>
        ) : (
          <div className="planner-timeline">
            {schedule.exams.map((exam, index) => {
              const countdown = countdowns[index];
              const isPast = countdown === null;
              
              return (
                <div key={index} className={`planner-entry ${isPast ? 'past' : ''}`}>
                  {/* Spine Connection */}
                  <div className="spine-connection">
                    <div className="connection-line"></div>
                    <div className="connection-dot"></div>
                  </div>

                  {/* Readiness Ring (Left - The Intelligence) */}
                  <div className="entry-readiness">
                    <ReadinessRing 
                      courseId={exam.course_id}
                      examId={exam.exam_id}
                      examName={exam.subject}
                      lectures={exam.lectures || []}
                      size="lg"
                    />
                  </div>

                  {/* Entry Details (Right) */}
                  <div className="entry-details">
                    <div className="entry-header">
                      <span className="course-tag">{exam.course_id}</span>
                      {countdown && (
                        <div className="live-countdown">
                          <FaClock className="countdown-icon" />
                          <span className="countdown-text">
                            Starts in: <strong>{formatCountdown(countdown)}</strong>
                          </span>
                        </div>
                      )}
                      {isPast && (
                        <span className="past-badge">Past</span>
                      )}
                    </div>

                    <h3 className="entry-title">{exam.subject}</h3>

                    <div className="entry-meta">
                      <div className="meta-item">
                        <FaCalendarAlt className="meta-icon" />
                        <span>{formatDate(exam.date_ist)}</span>
                      </div>
                    </div>

                    {exam.lectures && exam.lectures.length > 0 && (
                      <div className="entry-lectures">
                        <span className="lectures-label">📚 Covers:</span>
                        <div className="lectures-tags">
                          {exam.lectures.map((lectureId, idx) => (
                            <span key={idx} className="lecture-tag">{lectureId}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {exam.notes && (
                      <p className="entry-notes">{exam.notes}</p>
                    )}

                    {/* Intelligent CTA */}
                    {!isPast && (
                      <div className="entry-actions">
                        <button
                          className="action-btn primary"
                          onClick={() => {
                            // Navigate to weak concepts for this course
                            navigate('/weak-concepts');
                          }}
                        >
                          <FaExclamationTriangle /> Start Review Session
                        </button>
                        <button
                          className="action-btn secondary"
                          onClick={() => navigate(`/courses/${exam.course_id}/timetable`)}
                        >
                          View Full Schedule
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyScheduleView;
