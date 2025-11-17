import './LandingSocialProof.css'

function LandingSocialProof() {
  return (
    <section className="landing-social-proof">
      <div className="social-proof-container">
        <div className="testimonial-card">
          <div className="testimonial-profile">
            <img 
              src="/testimonial_pictures/Ahmed_Hossain.jpeg" 
              alt="Ahmed Hossain" 
              className="testimonial-avatar"
            />
            <div className="testimonial-rating">
              <span className="star">★</span>
              <span className="star">★</span>
              <span className="star">★</span>
              <span className="star">★</span>
              <span className="star">★</span>
            </div>
          </div>
          
          <blockquote className="testimonial-quote">
            "I used exammate for 2 hours before my exam. I went from stressed to confident. It actually works."
          </blockquote>
          
          <cite className="testimonial-attribution">
            — Ahmed Hossain, Student
          </cite>
        </div>
      </div>
    </section>
  )
}

export default LandingSocialProof
