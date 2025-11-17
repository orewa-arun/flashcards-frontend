import './LandingComparison.css'

function LandingComparison() {
  const comparisons = [
    {
      traditional: "Hours scrolling PDFs",
      exammate: "AI-personalized adaptive learning"
    },
    {
      traditional: "Low retention, fatigue",
      exammate: "AI-driven active engagement"
    },
    {
      traditional: "No progress tracking",
      exammate: "AI-powered exam readiness tracking"
    },
    {
      traditional: "Days to master material",
      exammate: "AI optimization: Exam-ready in hours"
    }
  ]

  return (
    <section className="landing-comparison landing-section bg-white section-padding-lg">
      <div className="landing-section-inner">
        <h2 className="comparison-title">Why Students Choose Exammate</h2>
        
        <div className="comparison-table-card">
          <div className="comparison-table">
            <div className="table-header">
              <div className="header-col traditional-col">Traditional Study Method</div>
              <div className="header-divider"></div>
              <div className="header-col exammate-col">Exammate Method</div>
            </div>
            
            {comparisons.map((item, index) => (
              <div key={index} className="table-row">
                <div className="row-col traditional-col">
                  <svg className="row-icon muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="9"/>
                  </svg>
                  <span className="text">{item.traditional}</span>
                </div>
                <div className="row-arrow">→</div>
                <div className="row-col exammate-col">
                  <svg className="row-icon highlight" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <span className="text">{item.exammate}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

export default LandingComparison
