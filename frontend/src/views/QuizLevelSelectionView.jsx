/**
 * QuizLevelSelectionView - Choose quiz difficulty level
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FaSeedling, FaGraduationCap, FaBrain, FaTrophy } from 'react-icons/fa';
import './QuizLevelSelectionView.css';

const QuizLevelSelectionView = () => {
  const navigate = useNavigate();
  const { courseId, lectureId } = useParams();

  // Format lecture ID for display (e.g., "SI_lec_1" -> "SI Lecture 1")
  const formatLectureTitle = (id) => {
    if (!id) return '';
    return id
      .replace(/_/g, ' ')
      .replace(/lec/i, 'Lecture')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const levels = [
    {
      level: 1,
      name: 'Easy',
      subtitle: 'Foundation',
      description: 'Test your basic understanding of core concepts',
      icon: <FaSeedling />,
      color: '#4caf50',
      estimatedTime: '10-15 min'
    },
    {
      level: 2,
      name: 'Medium',
      subtitle: 'Comprehension & Application',
      description: 'Apply concepts to new scenarios and examples',
      icon: <FaGraduationCap />,
      color: '#2196f3',
      estimatedTime: '15-20 min'
    },
    {
      level: 3,
      name: 'Hard',
      subtitle: 'Analysis & Critical Thinking',
      description: 'Analyze complex situations and solve challenging problems',
      icon: <FaBrain />,
      color: '#ff9800',
      estimatedTime: '20-25 min'
    },
    {
      level: 4,
      name: 'Boss Level',
      subtitle: 'Synthesis & Mastery',
      description: 'Master-level questions requiring deep synthesis',
      icon: <FaTrophy />,
      color: '#f44336',
      estimatedTime: '25-30 min'
    }
  ];

  const handleLevelSelect = (level) => {
    navigate(`/courses/${courseId}/${lectureId}/quiz/${level}`);
  };

  const handleBackToLecture = () => {
    navigate(`/courses/${courseId}/${lectureId}`);
  };

  return (
    <div className="quiz-level-selection">
      <div className="quiz-level-header">
        <button className="back-button" onClick={handleBackToLecture}>
          ← Back to Lecture
        </button>
        <div className="course-lecture-info">
          <span className="course-badge">{courseId}</span>
          <span className="separator">•</span>
          <span className="lecture-name">{formatLectureTitle(lectureId)}</span>
        </div>
        <h1>Choose Your Challenge</h1>
        <p className="subtitle">Select a difficulty level to start your personalized quiz</p>
      </div>

      <div className="level-cards">
        {levels.map((levelData) => (
          <div
            key={levelData.level}
            className="level-card"
            onClick={() => handleLevelSelect(levelData.level)}
            style={{ borderColor: levelData.color }}
          >
            <div className="level-icon" style={{ color: levelData.color }}>
              {levelData.icon}
            </div>
            <div className="level-info">
              <h2>{levelData.name}</h2>
              <h3>{levelData.subtitle}</h3>
              <p className="level-description">{levelData.description}</p>
              <div className="level-meta">
                <span className="time-estimate">⏱️ {levelData.estimatedTime}</span>
                <span className="level-number">Level {levelData.level}</span>
              </div>
            </div>
            <div className="level-arrow" style={{ color: levelData.color }}>
              →
            </div>
          </div>
        ))}
      </div>

      <div className="quiz-info-box">
        <h3>💡 How it works</h3>
        <ul>
          <li>Each quiz is <strong>personalized</strong> based on your performance</li>
          <li>Questions focus on concepts you need to practice</li>
          <li>Get <strong>immediate feedback</strong> on each answer</li>
          <li>Review linked flashcards for questions you miss</li>
        </ul>
      </div>
    </div>
  );
};

export default QuizLevelSelectionView;


