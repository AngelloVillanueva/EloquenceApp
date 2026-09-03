import { useCallback, useEffect, useRef, useState } from 'react'
import { BrandMark } from '../components/BrandMark'
import { FeedbackPanel } from '../components/FeedbackPanel'
import { GrainOverlay } from '../components/GrainOverlay'
import { InterruptButton } from '../components/InterruptButton'
import { LiveTranscriptBox } from '../components/LiveTranscriptBox'
import { SCENARIOS, ScenarioSidebar } from '../components/ScenarioSidebar'
import { SessionTimer } from '../components/SessionTimer'
import { ThemeToggle } from '../components/ThemeToggle'
import { TtfaBadge } from '../components/TtfaBadge'
import { VoiceOrb } from '../components/VoiceOrb'
import { ZenParticles } from '../components/ZenParticles'
import { useAudioPlayback } from '../hooks/useAudioPlayback'
import { useMicCapture } from '../hooks/useMicCapture'
import { useWebSocket } from '../hooks/useWebSocket'
import { useTheme } from '../theme/ThemeContext'

const STATE_LABEL: Record<string, string> = {
  idle:      'Ready to speak',
  listening: 'Listening…',
  thinking:  'Thinking…',
  speaking:  'Speaking…',
}

const STATE_TELEM: Record<string, string> = {
  idle:      'Studio ready',
  listening: 'Acoustic analysis',
  thinking:  'Processing',
  speaking:  'Voice output',
}

function useOrbSize(): number {
  const [size, setSize] = useState(360)

  useEffect(() => {
    const apply = () => {
      setSize(window.innerWidth < 640 ? 220 : 360)
    }
    apply()
    window.addEventListener('resize', apply)
    return () => window.removeEventListener('resize', apply)
  }, [])

  return size
}

export function AppLayout() {
  const { theme } = useTheme()
  const orbSize = useOrbSize()

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth > 768 : true,
  )
  const [scenario, setScenario] = useState('free')
  const [sessionStarted, setSessionStarted] = useState(false)

  const playback = useAudioPlayback()

  const resumeMicRef = useRef<() => void>(() => {})
  const setListeningRef = useRef<() => void>(() => {})
  const endTurnRef = useRef<() => void>(() => {})

  const ws = useWebSocket({
    onPcm: (pcm) => { void playback.enqueue(pcm) },
    onAudioMeta: (sr) => playback.setSampleRate(sr),
    onCancelled: () => {
      playback.stop()
      resumeMicRef.current()
      setListeningRef.current()
    },
    onTurnDone: () => {
      resumeMicRef.current()
      setListeningRef.current()
    },
  })

  const handleSpeechEnd = useCallback(() => {
    endTurnRef.current()
  }, [])

  const mic = useMicCapture({
    onChunk: ws.sendAudioChunk,
    onSpeechEnd: handleSpeechEnd,
    enabled: sessionStarted,
  })

  const handleDoneSpeaking = useCallback(() => {
    mic.pause()
    playback.stop()
    ws.sendEndTurn()
  }, [mic, playback, ws])

  useEffect(() => {
    resumeMicRef.current = mic.resume
    setListeningRef.current = () => ws.setOrbState('listening')
    endTurnRef.current = handleDoneSpeaking
  }, [mic.resume, ws.setOrbState, handleDoneSpeaking])

  const isConnected  = ws.status === 'connected'
  const isProcessing = ws.orbState === 'thinking' || ws.orbState === 'speaking'
  const isListening  = mic.status === 'capturing' && !isProcessing
  const displayState = isListening ? 'listening' as const : ws.orbState

  const scenarioLabel = SCENARIOS.find(s => s.id === scenario)?.title ?? 'Scenario'

  const handleScenario = useCallback((id: string) => {
    setScenario(id)
    if (sessionStarted && ws.status === 'connected') {
      ws.sendConfig({ scenario: id })
    }
  }, [sessionStarted, ws])

  const handleStart = useCallback(async () => {
    setSessionStarted(true)
    ws.connect({ scenario })
    await mic.start()
    ws.setOrbState('listening')
  }, [ws, mic, scenario])

  const handleInterrupt = useCallback(() => {
    playback.stop()
    ws.sendCancel()
  }, [playback, ws])

  const handleEnd = useCallback(() => {
    playback.stop()
    mic.stop()
    ws.disconnect()
    setSessionStarted(false)
  }, [playback, mic, ws])

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
      <GrainOverlay />

      <header className="studio-topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={() => setSidebarOpen(v => !v)}
            title={sidebarOpen ? 'Hide panel' : 'Scenarios'}
            style={{
              width: 30, height: 30,
              borderRadius: 8,
              border: sidebarOpen ? '1px solid var(--border-accent)' : '1px solid var(--border)',
              background: sidebarOpen ? 'var(--surface)' : 'transparent',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
              boxShadow: sidebarOpen ? '0 0 8px var(--accent-glow)' : 'none',
              transition: 'all 0.2s',
            }}
          >
            <svg width="14" height="11" viewBox="0 0 14 11" fill="none">
              <rect y="0"  width="14" height="1.5" rx="0.75" fill="var(--text-muted)" />
              <rect y="4.75" width="10" height="1.5" rx="0.75" fill="var(--text-muted)" />
              <rect y="9.5" width="14" height="1.5" rx="0.75" fill="var(--text-muted)" />
            </svg>
          </button>

          <BrandMark />

          <div className="scenario-label" style={{
            fontSize: 13,
            color: 'var(--text-subtle)',
            display: 'flex', alignItems: 'center', gap: 8,
            fontFamily: 'var(--font-mono)',
            letterSpacing: '0.04em',
          }}>
            <span style={{ color: 'var(--border)' }}>|</span>
            <span style={{ color: 'var(--accent)', opacity: 0.9 }}>{scenarioLabel}</span>
          </div>
        </div>

        <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
          <SessionTimer running={isConnected} orbState={displayState} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <TtfaBadge ttfa={ws.ttfa} />
          <ThemeToggle />
          <InterruptButton onInterrupt={handleInterrupt} active={isProcessing} />
        </div>
      </header>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        <ScenarioSidebar
          selected={scenario}
          onSelect={handleScenario}
          onClose={() => setSidebarOpen(false)}
          visible={sidebarOpen}
        />

        <FeedbackPanel
          feedback={ws.feedback}
          open={feedbackOpen}
          onToggle={() => setFeedbackOpen(v => !v)}
        />

        <main
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            overflow: 'hidden',
            background: 'var(--bg)',
          }}
          onClick={() => { if (sidebarOpen) setSidebarOpen(false) }}
        >
          <ZenParticles />

          <div
            style={{
              position: 'relative',
              zIndex: 10,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginTop: sessionStarted && ws.transcript.length > 0 ? -48 : -24,
            }}
          >
            <VoiceOrb state={displayState} size={orbSize} variant={theme} />

            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: 'var(--accent)',
                opacity: 0.7,
              }}>
                {STATE_TELEM[displayState] ?? 'Studio'}
              </div>
              <p style={{
                fontFamily: 'var(--font-ui)',
                fontSize: 16,
                color: isConnected ? 'var(--text)' : 'var(--text-subtle)',
                letterSpacing: '0.04em',
                opacity: 0.9,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: isListening || isProcessing ? 'orb-pulse 1.6s ease-in-out infinite' : 'none',
                }} />
                {STATE_LABEL[displayState] ?? displayState}
              </p>
            </div>

            {!sessionStarted && (
              <button
                className="btn-start"
                style={{ marginTop: 28 }}
                onClick={() => void handleStart()}
              >
                {ws.status === 'connecting' || mic.status === 'requesting'
                  ? 'Connecting…'
                  : 'Start Session'}
              </button>
            )}

            {sessionStarted && ws.transcript.length === 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, marginTop: 16 }}>
                {mic.status === 'capturing' && !isProcessing && (
                  <p style={{ fontSize: 12, color: 'var(--text-subtle)', textAlign: 'center' }}>
                    Speak naturally — pause ~1.5s to send
                    <button
                      onClick={handleDoneSpeaking}
                      style={{
                        display: 'block',
                        margin: '8px auto 0',
                        fontSize: 11,
                        color: 'var(--accent)',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        textDecoration: 'underline',
                        textUnderlineOffset: 2,
                      }}
                    >
                      or send now
                    </button>
                  </p>
                )}
                {isProcessing && (
                  <p style={{ fontSize: 12, color: 'var(--text-subtle)' }}>
                    Esc / Space to interrupt
                  </p>
                )}
              </div>
            )}

            {sessionStarted && (
              <button
                onClick={handleEnd}
                style={{
                  fontSize: 11,
                  color: 'var(--text-subtle)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  marginTop: 8,
                  textDecoration: 'underline',
                  textUnderlineOffset: 3,
                }}
              >
                End session
              </button>
            )}

            {mic.error && (
              <p style={{ fontSize: 11, color: 'var(--interrupt-hot)', marginTop: 12, textAlign: 'center' }}>
                Mic error: {mic.error}
              </p>
            )}
            {ws.status === 'error' && (
              <p style={{ fontSize: 11, color: 'var(--interrupt-hot)', marginTop: 12, textAlign: 'center' }}>
                Connection error — start the backend on port 8000
              </p>
            )}
          </div>

          <div
            className="transcript-dock"
            style={{
              position: 'absolute',
              bottom: 32,
              zIndex: 20,
              left: '50%',
              transform: 'translateX(-50%)',
            }}
          >
            <LiveTranscriptBox
              lines={ws.transcript}
              thinking={ws.orbState === 'thinking'}
            />
          </div>
        </main>
      </div>
    </div>
  )
}
