import React, { useState, useEffect } from 'react';
import { FaCalendarAlt, FaClock } from 'react-icons/fa';
import { getMySchedule } from '../api/timetable';
import './NextDeadline.css';

const NextDeadline = ({ courseId }) => {
  const [deadline, setDeadline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [countdown, setCountdown] = useState(null);
  const [showTooltip, setShowTooltip] = useState(false);

  // Fetch the deadline data
  useEffect(() => {
    const fetchDeadline = async () => {
      try {
        const scheduleData = await getMySchedule();
        
        if (scheduleData && scheduleData.exams) {
          const now = new Date();
          
          // Filter exams for this specific course that are in the future
          const upcomingExams = scheduleData.exams
            .filter(exam => exam.course_id === courseId)
            .map(exam => ({
              ...exam,
              date: new Date(exam.date_ist),
            }))
            .filter(exam => exam.date > now)
            .sort((a, b) => a.date - b.date);

          if (upcomingExams.length > 0) {
            setDeadline(upcomingExams[0]);
          }
        }
      } catch (error) {
        console.error('Failed to load deadline:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDeadline();
  }, [courseId]);

  // Live countdown timer that updates every second
  useEffect(() => {
    if (!deadline) return;

    const updateCountdown = () => {
      const now = new Date();
      const diffMillis = deadline.date - now;

      if (diffMillis <= 0) {
        setCountdown({ days: 0, hours: 0, minutes: 0, seconds: 0 });
        return;
      }

      const days = Math.floor(diffMillis / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diffMillis % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diffMillis % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diffMillis % (1000 * 60)) / 1000);

      setCountdown({ days, hours, minutes, seconds });
    };

    // Initial calculation
    updateCountdown();

    // Update every second
    const intervalId = setInterval(updateCountdown, 1000);

    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, [deadline]);

  if (loading) {
    return null; // Don't render during loading to avoid layout shift
  }

  // If no deadline exists, render a placeholder
  if (!deadline) {
    return (
      <div className="meta-item deadline-item deadline-placeholder">
        <FaCalendarAlt className="meta-icon" />
        <span className="meta-text">
          <em>No upcoming deadlines</em>
        </span>
      </div>
    );
  }

  if (!countdown) {
    return null; // Wait for countdown to be calculated
  }

  // Determine urgency class
  const totalHours = countdown.days * 24 + countdown.hours;
  let urgencyClass = 'urgency-low';
  if (totalHours < 24) {
    urgencyClass = 'urgency-high';
  } else if (countdown.days <= 7) {
    urgencyClass = 'urgency-medium';
  }

  // Format countdown text
  const formatCountdown = () => {
    const parts = [];
    if (countdown.days > 0) {
      parts.push(`${String(countdown.days).padStart(2, '0')}d`);
    }
    parts.push(`${String(countdown.hours).padStart(2, '0')}h`);
    parts.push(`${String(countdown.minutes).padStart(2, '0')}m`);
    parts.push(`${String(countdown.seconds).padStart(2, '0')}s`);
    return parts.join(' ');
  };

  // Format full date for tooltip
  const formatFullDate = () => {
    return deadline.date.toLocaleString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div 
      className={`meta-item deadline-item ${urgencyClass}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <FaCalendarAlt className="meta-icon" />
      <span className="meta-text">
        <strong>{deadline.subject}</strong>
        <span className="countdown-timer">{formatCountdown()}</span>
      </span>
      {showTooltip && (
        <div className="deadline-tooltip">
          <FaClock className="tooltip-icon" />
          {formatFullDate()}
        </div>
      )}
    </div>
  );
};

export default NextDeadline;
