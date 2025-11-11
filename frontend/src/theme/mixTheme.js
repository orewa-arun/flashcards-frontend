/**
 * Mix Mode Design System
 * 
 * Color palette and design tokens inspired by the brand logo.
 * This theme extends the existing brand design system for Mix Mode.
 */

export const mixTheme = {
  // Primary Colors (from logo)
  colors: {
    primary: '#2d7a3e',           // Logo green
    primaryDark: '#245c30',       // Darker green for hover states
    primaryLight: '#e8f5e9',      // Light green for backgrounds
    
    background: '#f9f7f3',        // Off-white from logo
    cardBackground: '#ffffff',    // Pure white for cards
    
    text: {
      primary: '#1a1a1a',         // Charcoal for main text
      secondary: '#666666',       // Medium gray for secondary text
      tertiary: '#999999',        // Light gray for hints
    },
    
    accent: {
      recommended: '#F39C12',     // Warm orange for "Recommended" tag
      warning: '#E74C3C',         // Red for errors
      success: '#27AE60',         // Success green
      info: '#3498DB',            // Info blue
    },
    
    difficulty: {
      easy: '#27AE60',            // Green
      medium: '#F39C12',          // Orange
      hard: '#E67E22',            // Dark orange
      boss: '#C0392B',            // Red
    },
    
    border: {
      light: '#e5e7eb',
      medium: '#d1d5db',
      dark: '#9ca3af',
    },
  },
  
  // Typography
  typography: {
    fontFamily: {
      primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", "Helvetica Neue", Arial, sans-serif',
      mono: '"SF Mono", "Monaco", "Inconsolata", "Fira Code", "Droid Sans Mono", "Source Code Pro", monospace',
    },
    fontSize: {
      xs: '0.75rem',      // 12px
      sm: '0.875rem',     // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',     // 18px
      xl: '1.25rem',      // 20px
      '2xl': '1.5rem',    // 24px
      '3xl': '1.875rem',  // 30px
      '4xl': '2.25rem',   // 36px
      '5xl': '3rem',      // 48px
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  
  // Spacing (based on 4px grid)
  spacing: {
    xs: '0.25rem',      // 4px
    sm: '0.5rem',       // 8px
    md: '1rem',         // 16px
    lg: '1.5rem',       // 24px
    xl: '2rem',         // 32px
    '2xl': '3rem',      // 48px
    '3xl': '4rem',      // 64px
    '4xl': '6rem',      // 96px
  },
  
  // Border Radius (rounded, friendly)
  borderRadius: {
    sm: '0.375rem',     // 6px
    md: '0.5rem',       // 8px
    lg: '0.75rem',      // 12px
    xl: '1rem',         // 16px
    '2xl': '1.25rem',   // 20px
    '3xl': '1.5rem',    // 24px
    full: '9999px',     // Full circle
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    base: '0 2px 8px rgba(0, 0, 0, 0.06)',
    md: '0 4px 12px rgba(0, 0, 0, 0.08)',
    lg: '0 8px 24px rgba(0, 0, 0, 0.12)',
    xl: '0 12px 32px rgba(0, 0, 0, 0.15)',
    recommended: '0 4px 16px rgba(243, 156, 18, 0.25)', // Orange glow
    primary: '0 4px 16px rgba(45, 122, 62, 0.25)',      // Green glow
  },
  
  // Transitions
  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  // Z-index layers
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    modal: 1030,
    popover: 1040,
    tooltip: 1050,
  },
};

// Utility function to get difficulty color
export const getDifficultyColor = (level) => {
  const levelMap = {
    easy: mixTheme.colors.difficulty.easy,
    medium: mixTheme.colors.difficulty.medium,
    hard: mixTheme.colors.difficulty.hard,
    boss: mixTheme.colors.difficulty.boss,
  };
  return levelMap[level?.toLowerCase()] || mixTheme.colors.difficulty.medium;
};

// Utility function to get difficulty label
export const getDifficultyLabel = (level) => {
  const levelMap = {
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard',
    boss: 'Boss',
  };
  return levelMap[level?.toLowerCase()] || 'Medium';
};

export default mixTheme;

