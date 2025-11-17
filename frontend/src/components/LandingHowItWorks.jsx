import './LandingHowItWorks.css'

function LandingHowItWorks() {
  const steps = [
    {
      number: 1,
      title: 'Take AI Quiz',
      description: 'AI instantly identifies your knowledge gaps',
      iconPath: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01'
    },
    {
      number: 2,
      title: 'AI-Guided Study',
      description: 'Our AI recommends exact flashcards you need',
      iconPath: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'
    },
    {
      number: 3,
      title: 'Ace Your Exam',
      description: 'AI adapts difficulty until you master concepts',
      iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
    }
  ]

  return (
    <section id="how-it-works" className="landing-how-it-works">
      <div className="how-it-works-container">
        <h2 className="how-it-works-headline">
          How It Works
        </h2>
        
        <div className="steps-flow">
          {steps.map((step, index) => (
            <div key={step.number} className="step-container">
              <div className="step-card">
                <svg className="step-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d={step.iconPath}/>
                </svg>
                <div className="step-number-badge">
                  {step.number}
                </div>
                <h3 className="step-title">
                  {step.title}
                </h3>
                <p className="step-description">
                  {step.description}
                </p>
              </div>
              
              {index < steps.length - 1 && (
                <div className="step-arrow">
                  →
                </div>
              )}
            </div>
          ))}
        </div>
        
        <p className="how-it-works-subtitle">
          Fresh questions every time. Master at your own speed.
        </p>
      </div>
    </section>
  )
}

export default LandingHowItWorks
