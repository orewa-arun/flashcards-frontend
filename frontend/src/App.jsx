import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import './App.css'
import CourseListView from './views/CourseListView'
import CourseDetailView from './views/CourseDetailView'
import DeckView from './views/DeckView'
import QuizView from './views/QuizView'
import ResultsView from './views/ResultsView'

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<CourseListView />} />
          <Route path="/courses/:courseId" element={<CourseDetailView />} />
          <Route path="/courses/:courseId/:lectureId" element={<DeckView />} />
          <Route path="/courses/:courseId/:lectureId/quiz" element={<QuizView />} />
          <Route path="/courses/:courseId/:lectureId/results" element={<ResultsView />} />
        </Routes>
        <Analytics />
      </div>
    </Router>
  )
}

export default App
