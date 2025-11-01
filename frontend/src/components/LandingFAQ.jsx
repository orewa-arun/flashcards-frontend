import React, { useState } from 'react';
import { FaPlus, FaMinus } from 'react-icons/fa';
import './LandingFAQ.css';

const faqs = [
  {
    question: "How are these flashcards different from regular flashcards?",
    answer: "Our AI-powered flashcards go beyond simple definitions. Each concept is broken down into 6 distinct learning modes—from simple analogies to real-world use cases and visual diagrams. This ensures you don't just memorize terms, you truly understand them."
  },
  {
    question: "How does the adaptive quiz work?",
    answer: "Our AI intelligently tracks your performance to identify your weak spots. If you get a question wrong, the system recommends the exact flashcard you need to review and re-tests you on that concept later. The quizzes adapt in real-time to focus on what you need to learn most."
  },
  {
    question: "What is the Exam Readiness Score?",
    answer: "It's your personal progress tracker, showing how prepared you are for your exam on a scale of 0-100%. The score is calculated based on your quiz performance, highlighting topics you've mastered and those that need more attention. You can even see how you stack up against classmates preparing for the same exam."
  },
  {
    question: "How much time does this actually save?",
    answer: "Most students master an entire course in just 2-4 hours. Our focused learning loop—quiz, identify gaps, learn, and re-test—is designed to take you from overwhelmed to exam-ready in a single, focused study session."
  },
  {
    question: "What types of questions are in the quizzes?",
    answer: "Our quizzes are designed to mirror your actual exams, featuring a mix of MCQs, classification, sequencing, matching, and scenario-based questions to ensure you're prepared for any format."
  },
  {
    question: "Can I track my progress?",
    answer: "Absolutely. Your dashboard provides a detailed breakdown of your strengths and weaknesses by topic, your Exam Readiness Score, and your rank compared to classmates. It's the ultimate tool for strategic studying."
  },
  {
    question: "Is this really free?",
    answer: "Yes, exammate.ai is 100% free for all IIT Madras DoMS students. No hidden fees, no credit card required. Our goal is to help our fellow students succeed."
  }
];

function FAQItem({ faq, index, toggleFAQ }) {
  return (
    <div
      className={`faq ${faq.open ? 'open' : ''}`}
      key={index}
      onClick={() => toggleFAQ(index)}
    >
      <div className="faq-question">
        {faq.question}
        <div className="faq-icon">
          {faq.open ? <FaMinus /> : <FaPlus />}
        </div>
      </div>
      <div className="faq-answer">
        {faq.answer}
      </div>
    </div>
  );
}

function LandingFAQ() {
  const [faqsData, setFaqsData] = useState(
    faqs.map((faq) => ({ ...faq, open: false }))
  );

  const toggleFAQ = (index) => {
    setFaqsData(
      faqsData.map((faq, i) => {
        if (i === index) {
          faq.open = !faq.open;
        } else {
          faq.open = false;
        }
        return faq;
      })
    );
  };

  return (
    <section className="landing-faq-section">
      <div className="faq-header">
        <h2>Frequently Asked Questions</h2>
        <p>Everything you need to know to get started with exammate.ai.</p>
      </div>
      <div className="faqs">
        {faqsData.map((faq, index) => (
          <FAQItem faq={faq} index={index} key={index} toggleFAQ={toggleFAQ} />
        ))}
      </div>
    </section>
  );
}

export default LandingFAQ;
