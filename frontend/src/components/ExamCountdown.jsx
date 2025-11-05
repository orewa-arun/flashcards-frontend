import React, { useEffect, useMemo, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { FaCalendarAlt, FaClock } from 'react-icons/fa'
import useCountdown from '../hooks/useCountdown'
import { getTimetable } from '../api/timetable'
import './ExamCountdown.css'

/**
 * ExamCountdown - floating countdown orb for next upcoming exam of current course
 */
export default function ExamCountdown({ courseId: propCourseId, docked = false, showLabel = false }) {
  const { courseId: routeCourseId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  const courseId = propCourseId || routeCourseId

  const [nextExam, setNextExam] = useState(null)
  const [targetDate, setTargetDate] = useState(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!courseId) return
    let cancelled = false
    ;(async () => {
      try {
        const data = await getTimetable(courseId)
        const exams = Array.isArray(data?.exams) ? data.exams : []
        const now = Date.now()

        const future = exams
          .map((e) => ({
            ...e,
            // Parse IST string or ISO into Date reliably
            ts: e.date_ist ? Date.parse(e.date_ist) : (e.date ? Date.parse(e.date) : NaN)
          }))
          .filter((e) => Number.isFinite(e.ts) && e.ts > now)
          .sort((a, b) => a.ts - b.ts)

        const first = future[0] || null
        if (!cancelled) {
          setNextExam(first)
          setTargetDate(first ? new Date(first.ts) : null)
        }
      } catch (err) {
        // Fail silent - do not render if error
        if (!cancelled) {
          setNextExam(null)
          setTargetDate(null)
        }
      }
    })()
    return () => { cancelled = true }
  }, [courseId, location.pathname])

  const countdown = useCountdown(targetDate || 0)

  const urgency = useMemo(() => {
    const d = countdown?.totalMs ?? 0
    if (d <= 24 * 60 * 60 * 1000) return 'urgent' // < 24h
    if (d <= 7 * 24 * 60 * 60 * 1000) return 'soon' // < 7d
    return 'future'
  }, [countdown.totalMs])

  if (!courseId || !nextExam || !targetDate || countdown.totalMs <= 0) {
    return null
  }

  return (
    <div className={`exam-countdown ${open ? 'open' : ''} ${urgency} ${docked ? 'docked' : ''}`}
         onMouseEnter={() => setOpen(true)}
         onMouseLeave={() => setOpen(false)}
         onClick={() => setOpen((v) => !v)}>
      {/* Collapsed orb */}
      <div className="orb">
        <FaCalendarAlt />
        <span className="mini">
          {countdown.days > 0 ? `${countdown.days}d` : `${countdown.hours}h`}
        </span>
      </div>
      {(showLabel || open) && (
        <div className="mini-label" title={`${courseId} — ${nextExam.subject || 'Upcoming Exam'}`}>
          <span className="course">{courseId}</span>
          <span className="dot">•</span>
          <span className="exam">{(nextExam.subject || 'Exam').slice(0, 24)}{(nextExam.subject || '').length > 24 ? '…' : ''}</span>
        </div>
      )}

      {/* Expanded card */}
      <div className="panel">
        <div className="panel-header">
          <span className="badge">{courseId}</span>
          <span className="time-left">
            {String(countdown.days).padStart(2, '0')}d{' '}
            {String(countdown.hours).padStart(2, '0')}h{' '}
            {String(countdown.minutes).padStart(2, '0')}m{' '}
            {String(countdown.seconds).padStart(2, '0')}s
          </span>
        </div>
        <div className="panel-title">{nextExam.subject || 'Upcoming Exam'}</div>
        <div className="panel-row">
          <FaClock />
          <span>{new Date(targetDate).toLocaleString('en-IN', { dateStyle: 'full', timeStyle: 'short' })}</span>
        </div>
        {Array.isArray(nextExam.lectures) && nextExam.lectures.length > 0 && (
          <div className="panel-lectures">
            <span className="label">Covers:</span>
            <div className="lectures">
              {nextExam.lectures.map((id, i) => (
                <span className="chip" key={`${id}-${i}`}>{id}</span>
              ))}
            </div>
          </div>
        )}
        <button className="panel-action" onClick={(e) => { e.stopPropagation(); navigate(`/courses/${courseId}/timetable`) }}>View Full Timetable</button>
      </div>
    </div>
  )
}


