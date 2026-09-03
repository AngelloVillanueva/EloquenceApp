import { AppLayout } from './pages/AppLayout'
import { ThemeProvider } from './theme/ThemeContext'

export default function App() {
  return (
    <ThemeProvider>
      <AppLayout />
    </ThemeProvider>
  )
}
