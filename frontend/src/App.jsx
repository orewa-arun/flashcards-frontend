import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { Analytics } from '@vercel/analytics/react'
import './App.css'
import CourseListView from './views/CourseListView'
import CourseDetailView from './views/CourseDetailView'
import DeckView from './views/DeckView'
import QuizView from './views/QuizView'
import ResultsView from './views/ResultsView'
import PrivacyPolicyView from './views/PrivacyPolicyView'
import BookmarksView from './views/BookmarksView'
import QuizHistoryView from './views/QuizHistoryView'
import AdminDashboardView from './views/AdminDashboardView'
import ThemeToggle from './components/ThemeToggle'
import CookieBanner from './components/CookieBanner'
import Navigation from './components/Navigation'
import { initializeUserTracking } from './utils/userTracking'

function App() {
  useEffect(() => {
    // Initialize user tracking on app startup
    initializeUserTracking()
  }, [])

  return (
    <Router>
      <ThemeToggle />
      <CookieBanner />
      <Navigation />
      <div className="app-container">
        <Routes>
          <Route path="/" element={<CourseListView />} />
          <Route path="/courses/:courseId" element={<CourseDetailView />} />
          <Route path="/courses/:courseId/:lectureId" element={<DeckView />} />
          <Route path="/courses/:courseId/:lectureId/quiz" element={<QuizView />} />
          <Route path="/courses/:courseId/:lectureId/results" element={<ResultsView />} />
          <Route path="/bookmarks" element={<BookmarksView />} />
          <Route path="/quiz-history" element={<QuizHistoryView />} />
          <Route path="/privacy-policy" element={<PrivacyPolicyView />} />
          <Route path="/secret-admin-dashboard-xyz" element={<AdminDashboardView />} />
        </Routes>
        <Analytics />
      </div>
    </Router>
  )
}

export default App
