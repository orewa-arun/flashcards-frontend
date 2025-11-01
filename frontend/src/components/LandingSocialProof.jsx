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
            "exammate.ai is a great app for MBA students. The unorganised & fast paced nature of the lectures can make it very difficult to take proper notes & find the necessary study & practice materials for the exams, that's where exammate.ai comes up as a life-saver.
            <br/><br/>
            I personally used it for two tests and found it quite helpful.
            <br/><br/>
            Mr. ArunKumar is doing a great job. I wish that this venture of his grows and improves consistently so that more & more students can benefit from it."
          </blockquote>
          
          <cite className="testimonial-attribution">
            — Ahmed Hossain, MBA Student
          </cite>
        </div>
      </div>
    </section>
  )
}

export default LandingSocialProof
