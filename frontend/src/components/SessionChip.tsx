interface Props {
  title: string
  sub: string
}

export function SessionChip({ title, sub }: Props) {
  return (
    <div
      className="session-chip"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        minWidth: 0,
        fontFamily: 'var(--font-ui)',
      }}
    >
      <span style={{ color: 'var(--border)', flexShrink: 0 }}>|</span>
      <div style={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
        <span
          style={{
            fontSize: 'var(--fs-body-sm)',
            fontWeight: 600,
            color: 'var(--text)',
            letterSpacing: '-0.01em',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {title}
        </span>
        <span
          className="session-chip-sub"
          style={{
            fontSize: 'var(--fs-overline)',
            color: 'var(--text-subtle)',
            letterSpacing: '0.02em',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {sub}
        </span>
      </div>
    </div>
  )
}
