import { useEffect, useRef, useState } from 'react'
import type { OrbState } from '../types/ws'

interface Props {
  running: boolean
  orbState: OrbState
}

export function SessionTimer({ running, orbState }: Props) {
  const [seconds, setSeconds] = useState(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => setSeconds((s) => s + 1), 1000)
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
      setSeconds(0)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [running])

  const mm = String(Math.floor(seconds / 60)).padStart(2, '0')
  const ss = String(seconds % 60).padStart(2, '0')
  const live = running && (orbState === 'listening' || orbState === 'speaking')

  return (
    <div className="flex items-center gap-2">
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          background: running ? (live ? 'var(--interrupt-hot)' : 'var(--accent)') : 'var(--text-subtle)',
          display: 'inline-block',
          animation: running ? 'orb-pulse 2s ease-in-out infinite' : 'none',
        }}
      />
      <span
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 14,
          fontWeight: 400,
          color: running ? 'var(--text)' : 'var(--text-subtle)',
          letterSpacing: '0.16em',
          textTransform: 'uppercase',
        }}
      >
        {mm}:{ss}
      </span>
    </div>
  )
}
