import { useEffect, useRef } from 'react'
import type { TranscriptLine } from '../types/ws'

interface Props {
  lines: TranscriptLine[]
}

const LABEL: React.CSSProperties = {
  fontFamily: 'JetBrains Mono, monospace',
  fontSize: 10,
  fontWeight: 600,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
  color: 'var(--accent)',
  flexShrink: 0,
  width: 64,
  paddingTop: 2,
}

export function LiveTranscriptBox({ lines }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (lines.length === 0) return null

  return (
    <div
      className="glass animate-fade-in-up"
      style={{
        borderRadius: 'var(--radius-lg)',
        padding: '12px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 0,
        maxHeight: 200,
        overflowY: 'auto',
        width: '100%',
      }}
    >
      {lines.map((line, i) => (
        <div key={line.id}>
          {i > 0 && (
            <div style={{ height: 1, background: 'var(--border)', margin: '8px 0' }} />
          )}
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <span style={LABEL}>{line.role === 'user' ? 'You' : 'Elevate'}</span>
            <span style={{
              fontFamily: 'Inter, system-ui, sans-serif',
              fontSize: 13.5,
              lineHeight: 1.55,
              color: line.role === 'user' ? 'var(--text)' : 'var(--text-muted)',
            }}>
              {line.text}
            </span>
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}
