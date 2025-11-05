import React, { useEffect, useState } from 'react'
import ExamCountdown from './ExamCountdown'
import { getUserProfile } from '../api/profile'
import './CourseCountdownDock.css'

/**
 * CourseCountdownDock - shows stacked countdowns for enrolled courses on the courses list page
 */
export default function CourseCountdownDock() {
  const [courseIds, setCourseIds] = useState([])
  const [hiddenIds, setHiddenIds] = useState(new Set())

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const profile = await getUserProfile()
        if (!cancelled) setCourseIds(profile?.enrolled_courses || [])
      } catch {
        if (!cancelled) setCourseIds([])
      }
    })()
    return () => { cancelled = true }
  }, [])

  // Observe course cards and hide dock items when their card is visible
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      setHiddenIds((prev) => {
        const next = new Set(prev)
        entries.forEach((e) => {
          const cid = e.target.getAttribute('data-course-id')
          if (!cid) return
          if (e.isIntersecting && e.intersectionRatio > 0.2) next.add(cid)
          else next.delete(cid)
        })
        return next
      })
    }, { threshold: [0, 0.2, 0.5, 1] })

    document.querySelectorAll('[data-course-id]').forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [courseIds])

  if (!courseIds || courseIds.length === 0) return null

  // Build filtered & sorted list (we let ExamCountdown compute urgency; here only cap length)
  const visibleIds = courseIds.filter((cid) => !hiddenIds.has(cid)).slice(0, 3)
  if (visibleIds.length === 0) return null

  return (
    <div className="countdown-dock">
      {visibleIds.map((cid) => (
        <ExamCountdown key={cid} courseId={cid} docked showLabel />
      ))}
    </div>
  )
}


