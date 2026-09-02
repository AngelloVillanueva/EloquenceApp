interface Props {
  ttfa: number | null
}

export function TtfaBadge({ ttfa }: Props) {
  if (ttfa === null) return null

  const color = ttfa < 2.0 ? '#6FCF97' : ttfa < 3.0 ? 'var(--accent)' : '#E05B4A'

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 5,
        padding: '3px 10px',
        borderRadius: 'var(--radius-full)',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
      }}
      title="Time to First Audio — latencia pipeline completo"
    >
      <span style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        TTFA
      </span>
      <span
        style={{
          fontFamily: 'JetBrains Mono, Consolas, monospace',
          fontSize: 11,
          fontWeight: 500,
          color,
        }}
      >
        {ttfa.toFixed(1)}s
      </span>
    </div>
  )
}
