/**
 * MyScheduleView - Aggregated exam schedule for all enrolled courses
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaCalendarAlt, FaClock, FaBook, FaExternalLinkAlt } from 'react-icons/fa';
import { getMySchedule } from '../api/timetable';
import { getUserProfile } from '../api/profile';
import ReadinessRing from '../components/ReadinessRing';
import './MyScheduleView.css';

const MyScheduleView = () => {
  const navigate = useNavigate();
  
  const [schedule, setSchedule] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSchedule();
  }, []);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      const data = await getMySchedule();
      console.log('📅 My Schedule API Response:', data);
      console.log('📚 Enrolled courses:', data?.enrolled_courses);
      console.log('📝 Exams:', data?.exams);
      
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
      const now = new Date();
      const diffDays = Math.floor((date - now) / (1000 * 60 * 60 * 24));
      
      const formattedDate = date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      let daysUntil = '';
      if (diffDays < 0) {
        daysUntil = '(Past)';
      } else if (diffDays === 0) {
        daysUntil = '(Today!)';
      } else if (diffDays === 1) {
        daysUntil = '(Tomorrow!)';
      } else if (diffDays <= 7) {
        daysUntil = `(In ${diffDays} days)`;
      } else if (diffDays <= 30) {
        daysUntil = `(In ${Math.ceil(diffDays / 7)} weeks)`;
      }
      
      return { formattedDate, daysUntil, diffDays };
    } catch {
      return { formattedDate: dateStr, daysUntil: '', diffDays: 999 };
    }
  };

  const getUrgencyClass = (diffDays) => {
    if (diffDays < 0) return 'past';
    if (diffDays === 0) return 'today';
    if (diffDays <= 3) return 'urgent';
    if (diffDays <= 7) return 'soon';
    return 'future';
  };

  if (loading) {
    return (
      <div className="my-schedule-loading">
        <div className="loading-spinner"></div>
        <p>Loading your schedule...</p>
      </div>
    );
  }

  return (
    <div className="my-schedule-view">
      {/* Header */}
      <div className="schedule-header force-normal">
        <div className="header-content">
          <h1 className="page-title">
            <FaCalendarAlt className="title-icon" />
            My Exam Schedule
          </h1>
          <p className="page-subtitle">
            All your exam dates in one place
          </p>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* Schedule Content */}
      <div className="schedule-content force-normal">
        {!schedule || schedule.enrolled_courses?.length === 0 ? (
          <div className="empty-state">
            <FaCalendarAlt className="empty-icon" />
            <h2>No Courses Enrolled</h2>
            <p>Click the <strong>"Enroll"</strong> button on any course page to add it to your schedule</p>
            <div className="enrollment-steps">
              <div className="step">
                <span className="step-number">1</span>
                <span>Browse available courses</span>
              </div>
              <div className="step">
                <span className="step-number">2</span>
                <span>Click "Enroll" button on course page</span>
              </div>
              <div className="step">
                <span className="step-number">3</span>
                <span>Your exam dates will appear here</span>
              </div>
            </div>
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
            {Array.isArray(schedule.enrolled_courses) && schedule.enrolled_courses.length > 0 ? (
              <div className="enrolled-courses-info">
                <p><strong>Enrolled in:</strong></p>
                <div className="enrolled-badges">
                  {schedule.enrolled_courses.map((cid) => (
                    <button
                      key={cid}
                      className="enrolled-course-badge"
                      onClick={() => navigate(`/courses/${cid}/timetable`)}
                    >
                      {cid}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="enrolled-courses-info">
                <p><strong>Enrolled in:</strong> N/A</p>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="schedule-stats">
              <div className="stat-card">
                <span className="stat-label">Enrolled Courses</span>
                <span className="stat-value">{schedule.enrolled_courses.length}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Total Exams</span>
                <span className="stat-value">{schedule.exams.length}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Upcoming</span>
                <span className="stat-value">
                  {schedule.exams.filter(e => formatDate(e.date_ist).diffDays >= 0).length}
                </span>
              </div>
            </div>

            <div className="exams-timeline">
              {schedule.exams.map((exam, index) => {
                const { formattedDate, daysUntil, diffDays } = formatDate(exam.date_ist);
                const urgencyClass = getUrgencyClass(diffDays);
                
                return (
                  <div key={index} className={`exam-timeline-card ${urgencyClass}`}>
                    <div className="exam-timeline-indicator">
                      <div className="indicator-dot"></div>
                      {index < schedule.exams.length - 1 && <div className="indicator-line"></div>}
                    </div>
                    
                    <div className="exam-timeline-content">
                      <div className="exam-header-row">
                        <span className="course-badge">{exam.course_id}</span>
                        {daysUntil && <span className="days-until">{daysUntil}</span>}
                      </div>
                      
                      <h3 className="exam-subject">{exam.subject}</h3>
                      
                      <div className="exam-meta">
                        <div className="meta-item">
                          <FaClock />
                          <span>{formattedDate}</span>
                        </div>
                      </div>
                      
                      {exam.lectures && exam.lectures.length > 0 && (
                        <div className="exam-lectures">
                          <span className="lectures-label">📚 Covers:</span>
                          <div className="lectures-tags">
                            {exam.lectures.map((lectureId, idx) => (
                              <span key={idx} className="lecture-tag">{lectureId}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {exam.notes && (
                        <p className="exam-notes">{exam.notes}</p>
                      )}
                      
                      <button
                        className="view-course-timetable-btn"
                        onClick={() => navigate(`/courses/${exam.course_id}/timetable`)}
                      >
                        <FaExternalLinkAlt /> View Course Timetable
                      </button>
                    </div>
                    
                    <div className="exam-readiness-section">
                      <ReadinessRing 
                        courseId={exam.course_id}
                        examId={exam.exam_id}
                        examName={exam.subject}
                        size="sm"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MyScheduleView;

