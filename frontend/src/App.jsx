import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { Analytics } from '@vercel/analytics/react'
import './App.css'
import LandingPageView from './views/LandingPageView'
import CourseListView from './views/CourseListView'
import CourseDetailView from './views/CourseDetailView'
import LectureDetailView from './views/LectureDetailView'
import DeckView from './views/DeckView'
import QuizView from './views/QuizView'
import ResultsView from './views/ResultsView'
import PrivacyPolicyView from './views/PrivacyPolicyView'
import BookmarksView from './views/BookmarksView'
import QuizHistoryView from './views/QuizHistoryView'
import AdminDashboardView from './views/AdminDashboardView'
import QuizLevelSelectionView from './views/QuizLevelSelectionView'
import QuizResultsView from './views/QuizResultsView'
import ThemeToggle from './components/ThemeToggle'
import CookieBanner from './components/CookieBanner'
import Navigation from './components/Navigation'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import { initializeAmplitude } from './utils/amplitude'

function App() {
  useEffect(() => {
    // Initialize Amplitude analytics on app startup
    initializeAmplitude()
  }, [])

  return (
    <AuthProvider>
    <Router>
      {/* <ThemeToggle /> */}
      <CookieBanner />
      <Navigation />
      <div className="app-container">
        <Routes>
          <Route path="/" element={<LandingPageView />} />
          <Route path="/privacy-policy" element={<PrivacyPolicyView />} />
            
            {/* Protected Routes - Require Authentication */}
            <Route path="/courses" element={
              <ProtectedRoute>
                <CourseListView />
              </ProtectedRoute>
            } />
            <Route path="/courses/:courseId" element={
              <ProtectedRoute>
                <CourseDetailView />
              </ProtectedRoute>
            } />
            <Route path="/courses/:courseId/:lectureId" element={
              <ProtectedRoute>
                <LectureDetailView />
              </ProtectedRoute>
            } />
            <Route path="/courses/:courseId/:lectureId/flashcards" element={
              <ProtectedRoute>
                <DeckView />
              </ProtectedRoute>
            } />
            {/* Adaptive Quiz Routes */}
            <Route path="/courses/:courseId/:lectureId/quiz" element={
              <ProtectedRoute>
                <QuizLevelSelectionView />
              </ProtectedRoute>
            } />
            <Route path="/courses/:courseId/:lectureId/quiz/:level" element={
              <ProtectedRoute>
                <QuizView />
              </ProtectedRoute>
            } />
            <Route path="/courses/:courseId/:lectureId/quiz/:level/results" element={
              <ProtectedRoute>
                <QuizResultsView />
              </ProtectedRoute>
            } />
            {/* Legacy Results Route */}
            <Route path="/courses/:courseId/:lectureId/results" element={
              <ProtectedRoute>
                <ResultsView />
              </ProtectedRoute>
            } />
            <Route path="/bookmarks" element={
              <ProtectedRoute>
                <BookmarksView />
              </ProtectedRoute>
            } />
            <Route path="/quiz-history" element={
              <ProtectedRoute>
                <QuizHistoryView />
              </ProtectedRoute>
            } />
            
            {/* Admin Route - Also Protected */}
            <Route path="/secret-admin-dashboard-xyz" element={
              <ProtectedRoute>
                <AdminDashboardView />
              </ProtectedRoute>
            } />
        </Routes>
        <Analytics />
      </div>
    </Router>
    </AuthProvider>
  )
}

export default App
