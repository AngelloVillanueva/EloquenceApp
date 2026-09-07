interface Scenario {
  id: string
  emoji: string
  title: string
  sub: string
  level: string
}

const SCENARIOS: Scenario[] = [
  { id: 'job',   emoji: '💼', title: 'Job Interview',       sub: 'Professional fluency', level: 'C1' },
  { id: 'arch',  emoji: '🏛',  title: 'Architecture Defense', sub: 'Technical depth',      level: 'C1' },
  { id: 'nego',  emoji: '🤝', title: 'Negotiation',          sub: 'Business English',     level: 'C2' },
  { id: 'free',  emoji: '💬', title: 'Free Conversation',    sub: 'Open practice',        level: 'C1+'},
  { id: 'vocab', emoji: '📚', title: 'Vocabulary Deep Dive', sub: 'Active recall',        level: 'C1' },
]

interface Props {
  selected: string
  onSelect: (id: string) => void
  onClose: () => void
  visible: boolean
}

export { SCENARIOS }

export function ScenarioSidebar({ selected, onSelect, onClose, visible }: Props) {
  return (
    <>
      {/* Backdrop (mobile only) */}
      {visible && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.55)',
            zIndex: 49,
            display: 'none',
          }}
          className="sidebar-backdrop"
        />
      )}

      <aside
        style={{
          position: 'fixed',
          top: 'var(--topbar-h)',
          left: 0,
          bottom: 0,
          width: 'var(--sidebar-w)',
          background: 'var(--bg-elevated)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 50,
          transform: visible ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.28s cubic-bezier(0.22,1,0.36,1)',
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div style={{ padding: '20px 16px 10px' }}>
          <p style={{
            fontSize: 'var(--fs-overline)',
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--accent)',
          }}>
            Scenario
          </p>
        </div>

        <div className="accent-line" style={{ margin: '0 16px' }} />

        {/* Scenario list */}
        <nav style={{ padding: '10px 10px', flex: 1 }}>
          {SCENARIOS.map(s => {
            const isActive = s.id === selected
            return (
              <button
                key={s.id}
                onClick={() => { onSelect(s.id); onClose() }}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 12px',
                  borderRadius: 10,
                  border: isActive ? '1px solid var(--border-accent)' : '1px solid transparent',
                  background: isActive ? 'var(--surface)' : 'transparent',
                  cursor: 'pointer',
                  marginBottom: 4,
                  textAlign: 'left',
                  transition: 'background 0.15s, border-color 0.15s',
                  boxShadow: isActive ? '0 0 12px var(--accent-glow)' : 'none',
                }}
                onMouseEnter={e => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'var(--surface)'
                }}
                onMouseLeave={e => {
                  if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'
                }}
              >
                <span style={{ fontSize: 18, lineHeight: 1, flexShrink: 0 }}>{s.emoji}</span>
                <div style={{ minWidth: 0 }}>
                  <div style={{
                    fontSize: 'var(--fs-body-sm)',
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? 'var(--text)' : 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>
                    {s.title}
                  </div>
                  <div style={{ fontSize: 'var(--fs-overline)', color: 'var(--text-subtle)', marginTop: 2 }}>
                    {s.sub} · {s.level}
                  </div>
                </div>
                {isActive && (
                  <div style={{
                    width: 5,
                    height: 5,
                    borderRadius: '50%',
                    background: 'var(--accent)',
                    flexShrink: 0,
                    marginLeft: 'auto',
                    boxShadow: '0 0 6px var(--accent)',
                  }} />
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: '12px 16px 20px', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: 'var(--fs-overline)', color: 'var(--text-subtle)', marginBottom: 10 }}>
            Level: <span style={{ color: 'var(--accent)' }}>B2</span>
            <span style={{ marginLeft: 8, color: 'var(--text-subtle)' }}>· Streak 7d 🔥</span>
          </div>
          <button
            onClick={onClose}
            style={{
              fontSize: 'var(--fs-body-sm)',
              color: 'var(--text-subtle)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 0',
            }}
          >
            ← Hide panel
          </button>
        </div>
      </aside>
    </>
  )
}
