import { FaSearch, FaBook, FaRedoAlt } from 'react-icons/fa'
import './LandingValueProps.css'

function LandingValueProps() {
  const valueProps = [
    {
      icon: <FaSearch />,
      headline: 'Find Your Gaps',
      description: 'Start with a quiz. Find gaps. Study only that.',
      gradient: 'linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%)'
    },
    {
      icon: <FaBook />,
      headline: 'Learn 6 Ways',
      description: '6 ways to understand hard concepts. Fast.',
      gradient: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)'
    },
    {
      icon: <FaRedoAlt />,
      headline: 'Practice Until Ready',
      description: 'Retake quizzes until you\'re confident.',
      gradient: 'linear-gradient(135deg, #A8E6CF 0%, #2D7A3E 100%)'
    }
  ]

  return (
    <section className="landing-value-props landing-section bg-white section-padding-lg">
      <div className="landing-section-inner">
        <div className="value-props-header text-center mb-lg">
          <h2 className="value-props-title mb-md">
            AI-Powered Learning That Adapts to You
          </h2>
          <div className="subtitle-container">
            <p className="value-props-subtitle">
              Our intelligent AI system analyzes your performance, personalizes your study path, and optimizes every minute to get you exam-ready faster.
            </p>
          </div>
        </div>
        
        <div className="value-props-grid grid-3">
          {valueProps.map((prop, index) => (
            <div key={index} className="value-prop-card elevated-card">
              <div className="value-prop-icon-wrapper">
                <div 
                  className="value-prop-icon-bg"
                  style={{ background: prop.gradient }}
                ></div>
                <div className="value-prop-icon">
                  {prop.icon}
                </div>
              </div>
              <h3 className="value-prop-headline">
                {prop.headline}
              </h3>
              <p className="value-prop-description">
                {prop.description}
              </p>
              <div className="value-prop-number">
                {String(index + 1).padStart(2, '0')}
              </div>
            </div>
          ))}
        </div>
        
        <div className="value-props-stats text-center">
          <div className="stats-grid grid-3">
            <div className="stat-item">
              <div className="stat-number">150+</div>
              <div className="stat-label">Concepts Covered</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">3 hrs</div>
              <div className="stat-label">Average Study Time</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">85%</div>
              <div className="stat-label">Average Score Improvement</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default LandingValueProps
