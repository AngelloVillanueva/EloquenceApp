import type { FeedbackPayload } from '../types/ws'

interface Props {
  feedback: FeedbackPayload | null
  open: boolean
  onToggle: () => void
}

function Item({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        color: 'var(--accent)',
        marginBottom: 6,
      }}>
        {label}
      </div>
      {children}
    </div>
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: '10px 12px',
      marginBottom: 6,
      fontSize: 13,
      lineHeight: 1.45,
      color: 'var(--text-muted)',
    }}>
      {children}
    </div>
  )
}

export function FeedbackPanel({ feedback, open, onToggle }: Props) {
  const empty =
    !feedback ||
    (
      feedback.grammar.length === 0 &&
      feedback.phrasing.length === 0 &&
      feedback.pronunciation.length === 0 &&
      !feedback.notes
    )

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
        {open ? 'Hide notes' : 'Coach notes'}
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
          <p style={{
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--accent)',
          }}>
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

          {feedback && feedback.grammar.length > 0 && (
            <Item label="Grammar">
              {feedback.grammar.map((g, i) => (
                <Card key={i}>
                  <div style={{ color: 'var(--text-subtle)', textDecoration: 'line-through', marginBottom: 4 }}>
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

          {feedback && feedback.phrasing.length > 0 && (
                <Item label="Phrasing">
              {feedback.phrasing.map((p, i) => (
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

          {feedback && feedback.pronunciation.length > 0 && (
            <Item label="Pronunciation">
              {feedback.pronunciation.map((p, i) => (
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

          {feedback?.notes && (
            <Item label="Note">
              <Card>{feedback.notes}</Card>
            </Item>
          )}
        </div>
      </aside>
    </>
  )
}
