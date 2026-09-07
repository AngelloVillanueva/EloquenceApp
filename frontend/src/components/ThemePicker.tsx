import { useEffect, useRef, useState } from 'react'
import { THEMES, useTheme } from '../theme/ThemeContext'

/** Preview built from the target theme's own tokens via `data-theme`. */
function Swatch({ theme }: { theme: string }) {
  return (
    <span className="theme-swatch" data-theme={theme} aria-hidden>
      <i />
      <i />
      <i />
    </span>
  )
}

export function ThemePicker() {
  const { theme, setTheme } = useTheme()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onPointerDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('pointerdown', onPointerDown)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('pointerdown', onPointerDown)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])

  const active = THEMES.find((t) => t.id === theme) ?? THEMES[0]

  return (
    <div className="theme-picker" ref={rootRef}>
      <button
        type="button"
        className="theme-toggle"
        onClick={() => setOpen((v) => !v)}
        title={`Theme: ${active.label}`}
        aria-label={`Theme: ${active.label}`}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden>
          <circle cx="7.5" cy="7.5" r="5.6" stroke="currentColor" strokeWidth="1.2" />
          <path d="M7.5 1.9a5.6 5.6 0 0 1 0 11.2Z" fill="currentColor" />
        </svg>
      </button>

      {open && (
        <div className="theme-menu" role="menu" aria-label="Themes">
          {THEMES.map((t) => {
            const isActive = t.id === theme
            return (
              <button
                key={t.id}
                type="button"
                role="menuitemradio"
                aria-checked={isActive}
                className={isActive ? 'theme-option theme-option-active' : 'theme-option'}
                onClick={() => {
                  setTheme(t.id)
                  setOpen(false)
                }}
              >
                <Swatch theme={t.id} />
                <span className="theme-option-label">{t.label}</span>
                {isActive && (
                  <svg className="theme-option-check" width="12" height="12" viewBox="0 0 12 12" aria-hidden>
                    <path d="M2 6.4l2.6 2.6L10 3.6" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" />
                  </svg>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
