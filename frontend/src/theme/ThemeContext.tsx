import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useState,
  type ReactNode,
} from 'react'

export type ThemeVariant = 'gold' | 'night'

const STORAGE_KEY = 'elevate-theme'

interface ThemeCtx {
  theme: ThemeVariant
  setTheme: (theme: ThemeVariant) => void
  toggle: () => void
}

const Ctx = createContext<ThemeCtx | null>(null)

function readStored(): ThemeVariant {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'night' ? 'night' : 'gold'
  } catch {
    return 'gold'
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeVariant>(readStored)

  useLayoutEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      /* private mode */
    }
  }, [theme])

  const setTheme = useCallback((next: ThemeVariant) => setThemeState(next), [])
  const toggle = useCallback(
    () => setThemeState((current) => (current === 'gold' ? 'night' : 'gold')),
    [],
  )

  return <Ctx.Provider value={{ theme, setTheme, toggle }}>{children}</Ctx.Provider>
}

export function useTheme(): ThemeCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
