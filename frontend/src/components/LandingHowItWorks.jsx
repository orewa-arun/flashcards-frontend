import './LandingHowItWorks.css'

function LandingHowItWorks() {
  const steps = [
    {
      number: 1,
      title: 'Take Quiz',
      description: 'See weaknesses'
    },
    {
      number: 2,
      title: 'Study Your Gaps',
      description: 'AI recommends flashcards'
    },
    {
      number: 3,
      title: 'Retake Until Ready',
      description: 'Progress at your pace'
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
                <div className="step-number">
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
