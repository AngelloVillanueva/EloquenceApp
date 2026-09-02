export function BrandMark() {
  return (
    <div className="flex items-baseline gap-1.5 select-none">
      <span
        style={{ fontFamily: 'Syne, system-ui', fontWeight: 700, fontSize: 17, color: 'var(--text)' }}
      >
        Elevate
      </span>
      <span
        style={{
          fontFamily: 'Syne, system-ui',
          fontWeight: 400,
          fontSize: 12,
          color: 'var(--accent)',
          letterSpacing: '0.04em',
        }}
      >
        AI
      </span>
    </div>
  )
}
