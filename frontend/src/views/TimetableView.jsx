/**
 * TimetableView - Display and manage course exam timetables
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaCalendarAlt, FaPlus, FaTrash, FaEdit, FaSave, FaTimes, FaArrowLeft, FaClock, FaChevronDown } from 'react-icons/fa';
import { getTimetable, updateTimetable, deleteExam } from '../api/timetable';
import ReadinessRing from '../components/ReadinessRing';
import './TimetableView.css';

const TimetableView = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  
  const [timetable, setTimetable] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  
  // Edit state
  const [editedExams, setEditedExams] = useState([]);
  const [availableLectures, setAvailableLectures] = useState([]);
  const [lectureDropdownOpen, setLectureDropdownOpen] = useState({});

  useEffect(() => {
    loadTimetable();
    loadCourseLectures();
  }, [courseId]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.lecture-selector')) {
        setLectureDropdownOpen({});
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadCourseLectures = async () => {
    try {
      const response = await fetch('/courses.json');
      const courses = await response.json();
      const course = courses.find(c => c.course_id === courseId);
      
      if (course && course.lecture_slides) {
        // Extract lecture IDs from the course structure
        const lectures = course.lecture_slides.map(slide => {
          // Extract lecture ID from pdf_path or create from course_code + lecture_number
          const pathParts = slide.pdf_path.split('/');
          const fileName = pathParts[pathParts.length - 1].replace('.pdf', '');
          return {
            id: fileName,
            name: slide.lecture_name || fileName
          };
        });
        setAvailableLectures(lectures);
      }
    } catch (err) {
      console.error('Error loading course lectures:', err);
    }
  };

  const loadTimetable = async () => {
    try {
      setLoading(true);
      const data = await getTimetable(courseId);
      setTimetable(data);
      setEditedExams(data.exams || []);
      setError(null);
    } catch (err) {
      setError('Failed to load timetable');
      console.error('Error loading timetable:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddExam = () => {
    const newExam = {
      exam_id: `temp_${Date.now()}`,
      subject: '',
      date_ist: '',
      lectures: [],
      notes: ''
    };
    setEditedExams([...editedExams, newExam]);
  };

  const handleRemoveExam = (examId) => {
    setEditedExams(editedExams.filter(exam => exam.exam_id !== examId));
  };

  const handleExamChange = (examId, field, value) => {
    setEditedExams(editedExams.map(exam => {
      if (exam.exam_id === examId) {
        return { ...exam, [field]: value };
      }
      return exam;
    }));
  };

  const toggleLectureSelection = (examId, lectureId) => {
    setEditedExams(editedExams.map(exam => {
      if (exam.exam_id === examId) {
        const currentLectures = exam.lectures || [];
        const isSelected = currentLectures.includes(lectureId);
        
        const updatedLectures = isSelected
          ? currentLectures.filter(id => id !== lectureId)
          : [...currentLectures, lectureId];
        
        return { ...exam, lectures: updatedLectures };
      }
      return exam;
    }));
  };

  const toggleLectureDropdown = (examId) => {
    setLectureDropdownOpen(prev => ({
      ...prev,
      [examId]: !prev[examId]
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Validate exams
      for (const exam of editedExams) {
        if (!exam.subject || !exam.date_ist) {
          alert('Please fill in all required fields (Subject and Date)');
          return;
        }
      }
      
      const response = await updateTimetable(courseId, editedExams);
      setTimetable(response.timetable);
      setEditedExams(response.timetable.exams || []);
      setEditing(false);
      setError(null);
    } catch (err) {
      setError('Failed to save timetable');
      console.error('Error saving timetable:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedExams(timetable?.exams || []);
    setEditing(false);
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-IN', {
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

  const formatUpdateTime = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="timetable-loading">
        <div className="loading-spinner"></div>
        <p>Loading timetable...</p>
      </div>
    );
  }

  return (
    <div className="timetable-view">
      {/* Header */}
      <div className="timetable-header">
        <button className="back-btn" onClick={() => navigate(-1)}>
          <FaArrowLeft /> Back
        </button>
        
        <div className="header-content">
          <h1 className="page-title">
            <FaCalendarAlt className="title-icon" />
            Exam Timetable
          </h1>
          <p className="page-subtitle">{courseId}</p>
        </div>

        {!editing && (
          <button className="edit-btn" onClick={() => setEditing(true)}>
            <FaEdit /> Edit Timetable
          </button>
        )}
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* Last Updated Info */}
      {timetable?.last_updated_by && !editing && (
        <div className="last-updated-info">
          <FaClock />
          <span>
            Last updated by <strong>{timetable.last_updated_by.user_name}</strong> on {formatUpdateTime(timetable.last_updated_by.timestamp_ist)}
          </span>
        </div>
      )}

      {/* Timetable Content */}
      <div className="timetable-content">
        {editing ? (
          // Edit Mode
          <div className="edit-mode">
            <div className="edit-actions">
              <button className="add-exam-btn" onClick={handleAddExam}>
                <FaPlus /> Add Exam
              </button>
              <div className="save-cancel-btns">
                <button className="cancel-btn" onClick={handleCancel} disabled={saving}>
                  <FaTimes /> Cancel
                </button>
                <button className="save-btn" onClick={handleSave} disabled={saving}>
                  <FaSave /> {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>

            <div className="exams-list edit">
              {editedExams.length === 0 ? (
                <div className="empty-state">
                  <FaCalendarAlt className="empty-icon" />
                  <p>No exams scheduled yet</p>
                  <button className="add-first-exam-btn" onClick={handleAddExam}>
                    <FaPlus /> Add Your First Exam
                  </button>
                </div>
              ) : (
                editedExams.map(exam => (
                  <div key={exam.exam_id} className="exam-card editing">
                    <div className="exam-edit-fields">
                      <div className="field">
                        <label>Subject *</label>
                        <input
                          type="text"
                          placeholder="e.g., Midterm Exam"
                          value={exam.subject}
                          onChange={(e) => handleExamChange(exam.exam_id, 'subject', e.target.value)}
                        />
                      </div>
                      
                      <div className="field">
                        <label>Date & Time (IST) *</label>
                        <input
                          type="datetime-local"
                          value={exam.date_ist}
                          onChange={(e) => handleExamChange(exam.exam_id, 'date_ist', e.target.value)}
                        />
                      </div>
                      
                      <div className="field full-width">
                        <label>Lectures Covered (Optional)</label>
                        <div className="lecture-selector">
                          <button
                            type="button"
                            className="lecture-dropdown-toggle"
                            onClick={() => toggleLectureDropdown(exam.exam_id)}
                          >
                            <span>
                              {exam.lectures && exam.lectures.length > 0
                                ? `${exam.lectures.length} lecture${exam.lectures.length > 1 ? 's' : ''} selected`
                                : 'Select lectures'}
                            </span>
                            <FaChevronDown className={lectureDropdownOpen[exam.exam_id] ? 'rotate' : ''} />
                          </button>
                          
                          {lectureDropdownOpen[exam.exam_id] && (
                            <div className="lecture-dropdown-menu">
                              {availableLectures.length === 0 ? (
                                <div className="lecture-dropdown-empty">No lectures available</div>
                              ) : (
                                availableLectures.map(lecture => {
                                  const isSelected = exam.lectures?.includes(lecture.id);
                                  return (
                                    <label key={lecture.id} className="lecture-option">
                                      <input
                                        type="checkbox"
                                        checked={isSelected}
                                        onChange={() => toggleLectureSelection(exam.exam_id, lecture.id)}
                                      />
                                      <span>{lecture.name}</span>
                                    </label>
                                  );
                                })
                              )}
                            </div>
                          )}
                        </div>
                        
                        {exam.lectures && exam.lectures.length > 0 && (
                          <div className="selected-lectures-preview">
                            {exam.lectures.map((lectureId, idx) => (
                              <span key={idx} className="lecture-chip">
                                {lectureId}
                                <button
                                  type="button"
                                  onClick={() => toggleLectureSelection(exam.exam_id, lectureId)}
                                  className="lecture-chip-remove"
                                >
                                  ×
                                </button>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      <div className="field full-width">
                        <label>Notes (Optional)</label>
                        <textarea
                          placeholder="e.g., Bring calculator, focus on sorting algorithms"
                          value={exam.notes || ''}
                          onChange={(e) => handleExamChange(exam.exam_id, 'notes', e.target.value)}
                          rows="2"
                        />
                      </div>
                    </div>
                    
                    <button 
                      className="delete-exam-btn"
                      onClick={() => handleRemoveExam(exam.exam_id)}
                    >
                      <FaTrash /> Remove
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          // View Mode
          <div className="view-mode">
            {editedExams.length === 0 ? (
              <div className="empty-state">
                <FaCalendarAlt className="empty-icon" />
                <h2>No exams scheduled</h2>
                <p>Click "Edit Timetable" to add your exam schedule</p>
              </div>
            ) : (
              <div className="exams-list">
                {editedExams.map(exam => (
                  <div key={exam.exam_id} className="exam-card with-readiness">
                    <div className="exam-icon">
                      <FaCalendarAlt />
                    </div>
                    <div className="exam-details">
                      <h3 className="exam-subject">{exam.subject}</h3>
                      <div className="exam-date">
                        <FaClock />
                        <span>{formatDate(exam.date_ist)}</span>
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
                    </div>
                    <div className="exam-readiness">
                      <ReadinessRing 
                        courseId={courseId}
                        examId={exam.exam_id}
                        examName={exam.subject}
                        size="md"
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TimetableView;

