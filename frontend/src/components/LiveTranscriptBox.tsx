import { useEffect, useRef } from 'react'
import type { TranscriptLine } from '../types/ws'

interface Props {
  lines: TranscriptLine[]
  thinking?: boolean
}

export function LiveTranscriptBox({ lines, thinking = false }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines, thinking])

  if (lines.length === 0 && !thinking) return null

  return (
    <div className="transcript-card animate-slide-up">
      {lines.map((line, i) => (
        <div key={line.id}>
          {i > 0 && (
            <div
              style={{
                height: 1,
                margin: '10px 0',
                background: 'linear-gradient(90deg, transparent, var(--border), transparent)',
              }}
            />
          )}
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <span className="chip">{line.role === 'user' ? 'YOU' : 'ELEVATE'}</span>
            <p
              style={{
                fontFamily: 'var(--font-ui)',
                fontSize: 16,
                lineHeight: 1.6,
                color: 'var(--text)',
                opacity: line.role === 'assistant' ? 0.88 : 1,
              }}
            >
              {line.text}
            </p>
          </div>
        </div>
      ))}
      {thinking && (
        <div>
          {lines.length > 0 && (
            <div
              style={{
                height: 1,
                margin: '10px 0',
                background: 'linear-gradient(90deg, transparent, var(--border), transparent)',
              }}
            />
          )}
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', opacity: 0.55 }}>
            <span className="chip">ELEVATE</span>
            <div style={{ display: 'flex', gap: 4, paddingTop: 8 }}>
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}
