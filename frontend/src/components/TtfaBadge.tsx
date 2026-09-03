interface Props {
  ttfa: number | null
}

export function TtfaBadge({ ttfa }: Props) {
  if (ttfa === null) return null

  const color = ttfa < 2.0 ? '#6FCF97' : ttfa < 3.0 ? 'var(--accent)' : 'var(--interrupt-hot)'

  return (
    <span
      title="Time to First Audio"
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 13,
        letterSpacing: '0.06em',
        color: 'var(--text-subtle)',
        opacity: 0.75,
      }}
    >
      TTFA{' '}
      <span style={{ color }}>{ttfa.toFixed(1)}s</span>
    </span>
  )
}
