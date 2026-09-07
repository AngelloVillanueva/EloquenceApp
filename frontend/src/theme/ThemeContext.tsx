import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useState,
  type ReactNode,
} from 'react'

export type ThemeVariant = 'gold' | 'night' | 'ember' | 'verdigris' | 'daylight'

export interface ThemeMeta {
  id: ThemeVariant
  label: string
  sub: string
}

/** Order shown in the picker. Palettes live in globals.css, not here. */
export const THEMES: ThemeMeta[] = [
  { id: 'gold',      label: 'Studio Gold',     sub: 'Amber on near-black' },
  { id: 'night',     label: 'Porcelain Night', sub: 'Cool shell, champagne light' },
  { id: 'ember',     label: 'Ember',           sub: 'Rust on charcoal' },
  { id: 'verdigris', label: 'Verdigris',       sub: 'Oxidised copper' },
  { id: 'daylight',  label: 'Daylight',        sub: 'Warm paper, light' },
]

const IDS = new Set<string>(THEMES.map((t) => t.id))
const STORAGE_KEY = 'eloquence-theme'
const LEGACY_STORAGE_KEY = 'elevate-theme'

interface ThemeCtx {
  theme: ThemeVariant
  setTheme: (theme: ThemeVariant) => void
}

const Ctx = createContext<ThemeCtx | null>(null)

function readStored(): ThemeVariant {
  try {
    const raw = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(LEGACY_STORAGE_KEY)
    return raw && IDS.has(raw) ? (raw as ThemeVariant) : 'gold'
  } catch {
    return 'gold'
  }
}

/**
 * The `data-theme` attribute is the source of truth; React state only
 * mirrors it. Writing the DOM before the re-render matters because
 * VoiceOrb and ZenParticles read their colours from computed styles —
 * if we waited for an effect they would sample the outgoing theme.
 */
function applyTheme(theme: ThemeVariant): void {
  document.documentElement.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    /* private mode */
  }
}

const initialTheme = readStored()
if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('data-theme', initialTheme)
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeVariant>(initialTheme)

  useLayoutEffect(() => { applyTheme(theme) }, [theme])

  const setTheme = useCallback((next: ThemeVariant) => {
    applyTheme(next)
    setThemeState(next)
  }, [])

  return <Ctx.Provider value={{ theme, setTheme }}>{children}</Ctx.Provider>
}

export function useTheme(): ThemeCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
