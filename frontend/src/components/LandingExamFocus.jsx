import './LandingExamFocus.css'

function LandingExamFocus() {
  return (
    <section className="landing-exam-focus landing-section bg-cream section-padding-lg">
      <div className="landing-section-inner">
        <div className="exam-focus-content">
          <div className="time-comparison">
            <div className="time-block exammate-time">
              <svg className="time-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
              <div className="time-value">30 min</div>
              <div className="time-label">on exammate</div>
            </div>
            
            <div className="equals-sign">=</div>
            
            <div className="time-block traditional-time">
              <svg className="time-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              <div className="time-value strikethrough">3 hours</div>
              <div className="time-label">scrolling PDFs</div>
            </div>
          </div>
          
          <p className="focus-tagline">Same exam results. AI makes the difference.</p>
        </div>
      </div>
    </section>
  )
}

export default LandingExamFocus
