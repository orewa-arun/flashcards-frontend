import React, { useEffect, useState } from 'react'
import { FaCalendarAlt } from 'react-icons/fa'
import { getTimetable } from '../api/timetable'
import './CourseCardBadge.css'

export default function CourseCardBadge({ courseId }) {
  const [exam, setExam] = useState(null)
  const [target, setTarget] = useState(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await getTimetable(courseId)
        const now = Date.now()
        const future = (data?.exams || [])
          .map((e) => ({ ...e, ts: e.date_ist ? Date.parse(e.date_ist) : (e.date ? Date.parse(e.date) : NaN) }))
          .filter((e) => Number.isFinite(e.ts) && e.ts > now)
          .sort((a, b) => a.ts - b.ts)
        const first = future[0] || null
        if (!cancelled) {
          setExam(first)
          setTarget(first ? new Date(first.ts) : null)
        }
      } catch {
        if (!cancelled) { setExam(null); setTarget(null) }
      }
    })()
    return () => { cancelled = true }
  }, [courseId])

  if (!courseId || !exam || !target) return null

  const ms = target.getTime() - Date.now()
  if (ms <= 0) return null
  const days = Math.floor(ms / (24*60*60*1000))
  const hours = Math.floor((ms % (24*60*60*1000)) / (60*60*1000))
  const short = days > 0 ? `${days}d` : `${hours}h`

  return (
    <div className="course-card-badge" title={`${courseId} • ${(exam.subject || 'Exam')} • ${short}`}>
      <div className={`dot ${days===0 ? 'urgent' : (days<=7 ? 'soon' : 'future')}`}>
        <FaCalendarAlt />
        <span className="time">{short}</span>
      </div>
      <div className="label">
        <span className="course">{courseId}</span>
        <span className="sep">•</span>
        <span className="exam">{(exam.subject || 'Exam').slice(0, 22)}{(exam.subject || '').length>22?'…':''}</span>
      </div>
    </div>
  )
}


