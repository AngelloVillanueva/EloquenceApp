export function BrandMark() {
  return (
    <div className="flex items-baseline gap-1 select-none">
      <span
        style={{
          fontFamily: 'var(--font-brand)',
          fontWeight: 600,
          fontSize: 22,
          letterSpacing: '-0.02em',
          color: 'var(--text)',
        }}
      >
        Elevate
      </span>
      <span
        style={{
          fontFamily: 'var(--font-brand)',
          fontWeight: 600,
          fontSize: 22,
          letterSpacing: '-0.02em',
          color: 'var(--accent)',
        }}
      >
        AI
      </span>
    </div>
  )
}
