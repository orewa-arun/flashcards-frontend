import { useState } from 'react'
import './LandingFAQ.css'

function LandingFAQ() {
  const [openIndex, setOpenIndex] = useState(null)

  const faqs = [
    {
      question: "How does the AI help me prepare faster?",
      answer: "Our AI uses advanced machine learning to analyze your quiz responses and identify knowledge gaps instantly. It then creates a personalized study path, recommending only the flashcards you need to review. This AI-driven approach eliminates time wasted on material you already know, reducing study time by up to 70% compared to traditional methods."
    },
    {
      question: "What makes your AI-powered flashcards different?",
      answer: "Our AI generates 6 distinct learning perspectives for each concept: Concise explanations, Analogies, ELI5 (simplified), Real-world examples, Use cases, and Common mistakes. The AI adapts the complexity and style based on your learning patterns, ensuring deep understanding rather than surface-level memorization."
    },
    {
      question: "How does the AI-adaptive quiz system work?",
      answer: "Our AI quiz engine uses real-time performance tracking and predictive algorithms. When you answer incorrectly, the AI immediately recommends specific flashcards and adjusts future question difficulty. The AI learns your strengths and weaknesses, focusing more time on challenging topics while accelerating through mastered material."
    },
    {
      question: "How does AI calculate my Exam Readiness Score?",
      answer: "The AI analyzes multiple data points: quiz performance, response times, topic coverage, concept mastery, and learning velocity. Using machine learning algorithms, it calculates a dynamic 0-100% readiness score that predicts your exam preparedness. The AI continuously updates this score as you study, showing exactly which topics need more attention."
    },
    {
      question: "Does the AI track my learning patterns over time?",
      answer: "Yes. Our AI dashboard provides intelligent analytics including performance trends, optimal study times, retention rates, and personalized insights. The AI identifies patterns in your learning behavior and suggests the best times and methods for you to study based on when you perform best."
    },
    {
      question: "How does the AI optimize my study time?",
      answer: "Most students achieve exam readiness in 2-4 hours with our AI. The system starts with a diagnostic quiz to map your knowledge, then uses AI algorithms to create an optimized study sequence. It recommends 30-minute focused sessions on high-impact topics, ensuring every minute is spent on material that maximally improves your score."
    },
    {
      question: "How does AI generate quiz questions?",
      answer: "Our AI creates diverse question types that mirror real exam formats: MCQs, multiple-correct-answer questions, classification, sequencing, matching, and scenario-based problems. The AI analyzes exam patterns and student performance data to generate questions at the right difficulty level for your current knowledge state."
    },
    {
      question: "Can I access the AI features on mobile?",
      answer: "Absolutely. All AI features—adaptive quizzes, personalized recommendations, and real-time analytics—work seamlessly on smartphones, tablets, and desktops. The AI synchronizes your progress across devices, so you can study anywhere."
    },
    {
      question: "How does the AI stay current with exam content?",
      answer: "Our AI system continuously learns from thousands of student interactions, curriculum updates, and exam patterns. It automatically adjusts question difficulty, updates content relevance, and improves explanations based on what helps students succeed most effectively."
    },
    {
      question: "What AI technology powers exammate.ai?",
      answer: "We use advanced machine learning algorithms including natural language processing for content generation, adaptive learning models for personalization, and predictive analytics for readiness scoring. Our AI is specifically trained on educational data to optimize exam preparation outcomes."
    }
  ]

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index)
  }

  return (
    <section id="faq" className="landing-faq landing-section bg-cream section-padding-lg">
      <div className="landing-section-inner">
        <div className="faq-header">
          <h2 className="faq-title">Frequently Asked Questions</h2>
          <p className="faq-subtitle">Everything you need to know about exammate.ai</p>
        </div>
        <br/>
        
        <div className="faq-list">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className={`faq-item ${openIndex === index ? 'open' : ''}`}
            >
              <button
                className="faq-question"
                onClick={() => toggleFAQ(index)}
                aria-expanded={openIndex === index}
              >
                <span className="question-text">{faq.question}</span>
                <svg
                  className="faq-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  {openIndex === index ? (
                    <line x1="5" y1="12" x2="19" y2="12" />
                  ) : (
                    <>
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </>
                  )}
                </svg>
              </button>
              
              <div className="faq-answer-wrapper">
                <div className="faq-answer">
                  <p>{faq.answer}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default LandingFAQ

