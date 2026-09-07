import { useEffect, useRef, type ReactNode } from 'react'
import type { FeedbackLogEntry, FeedbackPayload } from '../types/ws'

interface Props {
  log: FeedbackLogEntry[]
  open: boolean
  onToggle: () => void
}

function Item({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div
        style={{
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'var(--accent)',
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      {children}
    </div>
  )
}

function Card({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '10px 12px',
        marginBottom: 6,
        fontSize: 13,
        lineHeight: 1.45,
        color: 'var(--text-muted)',
      }}
    >
      {children}
    </div>
  )
}

function TurnBlock({ entry, index }: { entry: FeedbackLogEntry; index: number }) {
  const fb = entry.payload
  return (
    <div style={{ marginBottom: 16 }}>
      {index > 0 && (
        <div
          style={{
            height: 1,
            margin: '0 0 14px',
            background: 'linear-gradient(90deg, transparent, var(--border), transparent)',
          }}
        />
      )}
      <p
        style={{
          fontSize: 10,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
          color: 'var(--text-subtle)',
          marginBottom: 10,
        }}
      >
        Turn {index + 1}
      </p>

      {fb.grammar.length > 0 && (
        <Item label="Grammar">
          {fb.grammar.map((g, i) => (
            <Card key={i}>
              <div
                style={{
                  color: 'var(--text-subtle)',
                  textDecoration: 'line-through',
                  marginBottom: 4,
                }}
              >
                {String((g as { original?: string }).original ?? '')}
              </div>
              <div style={{ color: 'var(--text)' }}>
                {(g as { correction?: string }).correction ?? ''}
              </div>
              {(g as { note?: string }).note && (
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-subtle)' }}>
                  {(g as { note?: string }).note}
                </div>
              )}
            </Card>
          ))}
        </Item>
      )}

      {fb.phrasing.length > 0 && (
        <Item label="Phrasing">
          {fb.phrasing.map((p, i) => (
            <Card key={i}>
              <div style={{ color: 'var(--text-subtle)', marginBottom: 4 }}>
                {String((p as { original?: string }).original ?? '')}
              </div>
              <div style={{ color: 'var(--accent-bright, var(--accent))' }}>
                → {(p as { upgrade?: string }).upgrade ?? ''}
              </div>
              {(p as { note?: string }).note && (
                <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-subtle)' }}>
                  {(p as { note?: string }).note}
                </div>
              )}
            </Card>
          ))}
        </Item>
      )}

      {fb.pronunciation.length > 0 && (
        <Item label="Pronunciation">
          {fb.pronunciation.map((p, i) => (
            <Card key={i}>
              <strong style={{ color: 'var(--text)' }}>
                {(p as { word?: string }).word ?? ''}
              </strong>
              {(p as { tip?: string }).tip && (
                <div style={{ marginTop: 4 }}>{(p as { tip?: string }).tip}</div>
              )}
            </Card>
          ))}
        </Item>
      )}

      {fb.notes?.trim() && (
        <p
          style={{
            fontSize: 13,
            color: 'var(--text-subtle)',
            lineHeight: 1.45,
            marginTop: 4,
          }}
        >
          {fb.notes}
        </p>
      )}
    </div>
  )
}

export function slipCount(log: FeedbackLogEntry[]): number {
  return log.reduce((n, e) => {
    const fb: FeedbackPayload = e.payload
    return n + fb.grammar.length + fb.phrasing.length + fb.pronunciation.length
  }, 0)
}

export function FeedbackPanel({ log, open, onToggle }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [log])

  const empty = log.length === 0

  return (
    <>
      <button
        onClick={onToggle}
        title={open ? 'Hide feedback' : 'Show feedback'}
        style={{
          position: 'fixed',
          top: 'calc(var(--topbar-h) + 12px)',
          right: open ? 292 : 12,
          zIndex: 55,
          height: 32,
          padding: '0 12px',
          borderRadius: 8,
          border: '1px solid var(--border-accent)',
          background: 'var(--surface)',
          color: 'var(--accent)',
          fontFamily: 'Plus Jakarta Sans, system-ui, sans-serif',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.04em',
          cursor: 'pointer',
          boxShadow: '0 0 12px var(--accent-glow)',
          transition: 'right 0.28s cubic-bezier(0.22,1,0.36,1)',
        }}
      >
        {open ? 'Hide notes' : log.length > 0 ? `Coach notes · ${log.length}` : 'Coach notes'}
      </button>

      <aside
        style={{
          position: 'fixed',
          top: 'var(--topbar-h)',
          right: 0,
          bottom: 0,
          width: 280,
          background: 'var(--bg-elevated)',
          borderLeft: '1px solid var(--border)',
          zIndex: 50,
          transform: open ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.28s cubic-bezier(0.22,1,0.36,1)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '16px 16px 10px' }}>
          <p
            style={{
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'var(--accent)',
            }}
          >
            Coach notes
          </p>
          <p style={{ fontSize: 12, color: 'var(--text-subtle)', marginTop: 4 }}>
            Corrections stay visual — never spoken
          </p>
        </div>
        <div className="accent-line" style={{ margin: '0 16px' }} />

        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px 24px' }}>
          {empty && (
            <p style={{ fontSize: 13, color: 'var(--text-subtle)', lineHeight: 1.5 }}>
              After each turn, grammar, phrasing upgrades, and pronunciation tips appear here.
            </p>
          )}
          {log.map((entry, i) => (
            <TurnBlock key={entry.id} entry={entry} index={i} />
          ))}
          <div ref={endRef} />
        </div>
      </aside>
    </>
  )
}
