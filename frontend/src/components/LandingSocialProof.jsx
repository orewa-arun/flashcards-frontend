import './LandingSocialProof.css'

function LandingSocialProof() {
  return (
    <section className="landing-social-proof">
      <div className="social-proof-container">
        <div className="testimonial-card">
          <div className="testimonial-rating">
            <span className="star">★</span>
            <span className="star">★</span>
            <span className="star">★</span>
            <span className="star">★</span>
            <span className="star">★</span>
          </div>
          
          <blockquote className="testimonial-quote">
            "15 minutes on flashcards. Scored 80% on my exam."
          </blockquote>
          
          <cite className="testimonial-attribution">
            — Priya R., DoMS 2027
          </cite>
        </div>
      </div>
    </section>
  )
}

export default LandingSocialProof
