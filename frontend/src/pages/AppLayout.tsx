import { useCallback, useEffect, useRef, useState } from 'react'
import { BrandMark } from '../components/BrandMark'
import { FeedbackPanel, slipCount } from '../components/FeedbackPanel'
import { GrainOverlay } from '../components/GrainOverlay'
import { InterruptButton } from '../components/InterruptButton'
import { LiveTranscriptBox } from '../components/LiveTranscriptBox'
import { SCENARIOS, ScenarioSidebar } from '../components/ScenarioSidebar'
import { SessionChip } from '../components/SessionChip'
import { SessionTimer } from '../components/SessionTimer'
import { ThemePicker } from '../components/ThemePicker'
import { TtfaBadge } from '../components/TtfaBadge'
import { VoiceOrb } from '../components/VoiceOrb'
import { ZenParticles } from '../components/ZenParticles'
import { useAudioPlayback } from '../hooks/useAudioPlayback'
import { useMicCapture } from '../hooks/useMicCapture'
import { useOrbSize } from '../hooks/useOrbSize'
import { useWebSocket } from '../hooks/useWebSocket'

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

interface AppLayoutProps {
  initialScenario?: string
  onBackHub?: () => void
  onOpenShadow?: (phrase: string) => void
}

export function AppLayout({
  initialScenario = 'free',
  onBackHub,
  onOpenShadow,
}: AppLayoutProps) {
  const orbSize = useOrbSize(360)

  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth > 768 : true,
  )
  const [scenario, setScenario] = useState(initialScenario)
  const [sessionStarted, setSessionStarted] = useState(false)
  const [recap, setRecap] = useState<{
    durationS: number
    turns: number
    slips: number
    scenario: string
  } | null>(null)
  const sessionStartedAt = useRef<number | null>(null)

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

  const scenarioMeta = SCENARIOS.find(s => s.id === scenario)
  const scenarioLabel = scenarioMeta?.title ?? 'Scenario'
  const scenarioSub = scenarioMeta?.sub ?? ''

  const handleScenario = useCallback((id: string) => {
    setScenario(id)
    if (sessionStarted && ws.status === 'connected') {
      ws.sendConfig({ scenario: id })
    }
  }, [sessionStarted, ws])

  const handleStart = useCallback(async () => {
    setRecap(null)
    sessionStartedAt.current = Date.now()
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
    const durationS = sessionStartedAt.current
      ? Math.round((Date.now() - sessionStartedAt.current) / 1000)
      : 0
    const turns = ws.transcript.filter((l) => l.role === 'user').length
    const slips = slipCount(ws.feedbackLog)
    playback.stop()
    mic.stop()
    ws.disconnect()
    setSessionStarted(false)
    sessionStartedAt.current = null
    setRecap({ durationS, turns, slips, scenario: scenarioLabel })
  }, [playback, mic, ws, scenarioLabel])

  return (
    <div className="studio-shell" style={{ overflow: 'hidden' }}>
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

          <button
            type="button"
            onClick={() => {
              if (sessionStarted) handleEnd()
              onBackHub?.()
            }}
            title="Back to Hub"
            style={{ background: 'none', border: 'none', padding: 0, cursor: onBackHub ? 'pointer' : 'default' }}
          >
            <BrandMark />
          </button>
          <SessionChip title={scenarioLabel} sub={scenarioSub} />
        </div>

        <div className="session-timer-slot">
          <SessionTimer running={isConnected} orbState={displayState} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {onBackHub && (
            <button
              type="button"
              className="btn-end"
              onClick={() => {
                if (sessionStarted) handleEnd()
                onBackHub()
              }}
            >
              Hub
            </button>
          )}
          <TtfaBadge ttfa={ws.ttfa} />
          <ThemePicker />
          {sessionStarted && (
            <button
              type="button"
              className="btn-end"
              onClick={handleEnd}
              title="End session"
            >
              End
            </button>
          )}
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
          log={ws.feedbackLog}
          open={feedbackOpen}
          onToggle={() => setFeedbackOpen(v => !v)}
          onPractice={onOpenShadow
            ? (phrase) => {
                if (sessionStarted) handleEnd()
                onOpenShadow(phrase)
              }
            : undefined}
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
              marginTop: recap ? 0 : sessionStarted && ws.transcript.length > 0 ? -48 : -24,
            }}
          >
            <VoiceOrb state={displayState} size={recap ? Math.min(orbSize, 240) : orbSize} />

            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 'var(--fs-caption)',
                letterSpacing: '0.18em',
                textTransform: 'uppercase',
                color: 'var(--accent)',
                opacity: 0.7,
              }}>
                {STATE_TELEM[displayState] ?? 'Studio'}
              </div>
              <p style={{
                fontFamily: 'var(--font-ui)',
                fontSize: 'var(--fs-title)',
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

            {!sessionStarted && !recap && (
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

            {!sessionStarted && recap && (
              <div
                className="session-recap animate-fade-in"
                style={{
                  marginTop: 20,
                  width: 'min(320px, calc(100vw - 48px))',
                  padding: '20px 22px',
                  borderRadius: 14,
                  border: '1px solid var(--border)',
                  background: 'var(--surface)',
                  textAlign: 'center',
                  position: 'relative',
                  zIndex: 25,
                }}
              >
                <p
                  style={{
                    fontSize: 'var(--fs-overline)',
                    fontWeight: 600,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    color: 'var(--accent)',
                    marginBottom: 8,
                  }}
                >
                  Session closed
                </p>
                <p style={{ fontSize: 'var(--fs-title)', fontWeight: 600, color: 'var(--text)', marginBottom: 14 }}>
                  {recap.scenario}
                </p>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: 12,
                    fontFamily: 'var(--font-mono)',
                    fontSize: 'var(--fs-body-sm)',
                    letterSpacing: '0.04em',
                    color: 'var(--text-subtle)',
                    marginBottom: 18,
                  }}
                >
                  <span>
                    {String(Math.floor(recap.durationS / 60)).padStart(2, '0')}:
                    {String(recap.durationS % 60).padStart(2, '0')}
                  </span>
                  <span>
                    {recap.turns} {recap.turns === 1 ? 'turn' : 'turns'}
                  </span>
                  <span>
                    {recap.slips} {recap.slips === 1 ? 'slip' : 'slips'}
                  </span>
                </div>
                <button className="btn-start" onClick={() => void handleStart()}>
                  Start Session
                </button>
                {onBackHub && (
                  <button
                    type="button"
                    className="btn-end"
                    style={{ marginTop: 10 }}
                    onClick={onBackHub}
                  >
                    Back to Hub
                  </button>
                )}
              </div>
            )}

            {sessionStarted && ws.transcript.length === 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, marginTop: 16 }}>
                {mic.status === 'capturing' && !isProcessing && (
                  <p style={{ fontSize: 'var(--fs-body-sm)', color: 'var(--text-subtle)', textAlign: 'center' }}>
                    Speak naturally — pause ~1.5s to send
                    <button
                      onClick={handleDoneSpeaking}
                      style={{
                        display: 'block',
                        margin: '8px auto 0',
                        fontSize: 'var(--fs-body-sm)',
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
                  <p style={{ fontSize: 'var(--fs-body-sm)', color: 'var(--text-subtle)' }}>
                    Esc / Space to interrupt
                  </p>
                )}
              </div>
            )}

            {mic.error && (
              <p style={{ fontSize: 'var(--fs-body-sm)', color: 'var(--interrupt-hot)', marginTop: 12, textAlign: 'center' }}>
                Mic error: {mic.error}
              </p>
            )}
            {ws.status === 'error' && (
              <p style={{ fontSize: 'var(--fs-body-sm)', color: 'var(--interrupt-hot)', marginTop: 12, textAlign: 'center' }}>
                Connection error — start the backend on port 8000
              </p>
            )}
          </div>

          {!recap && (
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
          )}
        </main>
      </div>
    </div>
  )
}
