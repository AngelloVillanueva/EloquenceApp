import { useState } from 'react'
import { ThemeProvider } from './theme/ThemeContext'
import { AppLayout } from './pages/AppLayout'
import { HubPage } from './pages/HubPage'
import { ShadowPage } from './pages/ShadowPage'

type View = 'hub' | 'session' | 'shadow'

export default function App() {
  const [view, setView] = useState<View>('hub')
  const [scenario, setScenario] = useState('free')
  const [shadowPhrase, setShadowPhrase] = useState<string | null>(null)

  return (
    <ThemeProvider>
      {view === 'hub' && (
        <HubPage
          onStart={(id) => {
            setScenario(id)
            setView('session')
          }}
          onShadow={(phrase) => {
            setShadowPhrase(phrase ?? null)
            setView('shadow')
          }}
        />
      )}
      {view === 'session' && (
        <AppLayout
          initialScenario={scenario}
          onBackHub={() => setView('hub')}
          onOpenShadow={(phrase) => {
            setShadowPhrase(phrase)
            setView('shadow')
          }}
        />
      )}
      {view === 'shadow' && (
        <ShadowPage
          initialPhrase={shadowPhrase}
          onBack={() => {
            setShadowPhrase(null)
            setView('hub')
          }}
        />
      )}
    </ThemeProvider>
  )
}
