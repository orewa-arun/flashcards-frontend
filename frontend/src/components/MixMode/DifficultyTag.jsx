/**
 * DifficultyTag - Color-coded difficulty indicator
 */

import React from 'react';
import { getDifficultyColor, getDifficultyLabel } from '../../theme/mixTheme';
import './DifficultyTag.css';

const DifficultyTag = ({ level }) => {
  const color = getDifficultyColor(level);
  const label = getDifficultyLabel(level);
  
  return (
    <span 
      className="difficulty-tag" 
      style={{ 
        backgroundColor: `${color}15`,
        color: color,
        borderColor: `${color}40`
      }}
    >
      {label}
    </span>
  );
};

export default DifficultyTag;

