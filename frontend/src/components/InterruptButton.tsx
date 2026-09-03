import { useEffect } from 'react'

interface Props {
  onInterrupt: () => void
  active: boolean
}

export function InterruptButton({ onInterrupt, active }: Props) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.key === 'Escape' || e.key === ' ') && active) {
        e.preventDefault()
        onInterrupt()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [active, onInterrupt])

  return (
    <button
      onClick={onInterrupt}
      disabled={!active}
      title="Interrupt (Esc)"
      aria-label="Interrupt AI response"
      style={{
        width: 32,
        height: 32,
        borderRadius: 4,
        border: 'none',
        cursor: active ? 'pointer' : 'default',
        background: active ? 'var(--interrupt)' : 'var(--interrupt-dim)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'background 0.2s, transform 0.1s',
        flexShrink: 0,
      }}
      onMouseEnter={(e) => {
        if (active) (e.currentTarget as HTMLButtonElement).style.background = 'var(--interrupt-hot)'
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.background = active
          ? 'var(--interrupt)'
          : 'var(--interrupt-dim)'
      }}
      onMouseDown={(e) => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(0.92)' }}
      onMouseUp={(e) => { (e.currentTarget as HTMLButtonElement).style.transform = 'scale(1)' }}
    >
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <rect x="1.5" y="1.5" width="9" height="9" rx="1" fill="white" fillOpacity={active ? 0.95 : 0.4} />
      </svg>
    </button>
  )
}
