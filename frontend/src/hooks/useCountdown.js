import { useEffect, useMemo, useRef, useState } from 'react'

/**
 * useCountdown - returns a live ticking breakdown to a target Date instance.
 * If target is in the past, all values clamp to zero.
 */
export default function useCountdown(targetDate) {
  const [now, setNow] = useState(() => Date.now())
  const timerRef = useRef(null)

  useEffect(() => {
    // Tick every second
    timerRef.current = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timerRef.current)
  }, [])

  const result = useMemo(() => {
    const targetMs = targetDate instanceof Date ? targetDate.getTime() : Number(targetDate) || 0
    let delta = Math.max(0, targetMs - now)

    const days = Math.floor(delta / (24 * 60 * 60 * 1000))
    delta -= days * 24 * 60 * 60 * 1000
    const hours = Math.floor(delta / (60 * 60 * 1000))
    delta -= hours * 60 * 60 * 1000
    const minutes = Math.floor(delta / (60 * 1000))
    delta -= minutes * 60 * 1000
    const seconds = Math.floor(delta / 1000)

    return { days, hours, minutes, seconds, totalMs: Math.max(0, targetMs - now) }
  }, [now, targetDate])

  return result
}


