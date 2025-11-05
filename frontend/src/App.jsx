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
import TimetableView from './views/TimetableView'
import MyScheduleView from './views/MyScheduleView'
import WeakConceptsView from './views/WeakConceptsView'
import CourseLayout from './layouts/CourseLayout'
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
            {/* Nested course routes under CourseLayout to inject ExamCountdown */}
            <Route path="/courses/:courseId" element={
              <ProtectedRoute>
                <CourseLayout />
              </ProtectedRoute>
            }>
              <Route index element={<CourseDetailView />} />
              <Route path="timetable" element={<TimetableView />} />
              <Route path=":lectureId" element={<LectureDetailView />} />
              <Route path=":lectureId/flashcards" element={<DeckView />} />
              <Route path=":lectureId/quiz" element={<QuizLevelSelectionView />} />
              <Route path=":lectureId/quiz/:level" element={<QuizView />} />
              <Route path=":lectureId/quiz/:level/results" element={<QuizResultsView />} />
              <Route path=":lectureId/results" element={<ResultsView />} />
            </Route>
            <Route path="/my-schedule" element={
              <ProtectedRoute>
                <MyScheduleView />
              </ProtectedRoute>
            } />
            <Route path="/weak-concepts" element={
              <ProtectedRoute>
                <WeakConceptsView />
              </ProtectedRoute>
            } />
            {/* Note: quiz/lecture routes moved under nested course routes above */}
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
