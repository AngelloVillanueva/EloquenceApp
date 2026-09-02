import { useCallback, useEffect, useRef, useState } from 'react'
import { BrandMark } from '../components/BrandMark'
import { FeedbackPanel } from '../components/FeedbackPanel'
import { GrainOverlay } from '../components/GrainOverlay'
import { InterruptButton } from '../components/InterruptButton'
import { LiveTranscriptBox } from '../components/LiveTranscriptBox'
import { SCENARIOS, ScenarioSidebar } from '../components/ScenarioSidebar'
import { SessionTimer } from '../components/SessionTimer'
import { TtfaBadge } from '../components/TtfaBadge'
import { VoiceOrb } from '../components/VoiceOrb'
import { useAudioPlayback } from '../hooks/useAudioPlayback'
import { useMicCapture } from '../hooks/useMicCapture'
import { useWebSocket } from '../hooks/useWebSocket'

const STATE_LABEL: Record<string, string> = {
  idle:      'Ready to speak',
  listening: 'Listening\u2026',
  thinking:  'Thinking\u2026',
  speaking:  'Speaking\u2026',
}

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(true)
  const [scenario, setScenario] = useState('job')
  const [sessionStarted, setSessionStarted] = useState(false)

  const playback = useAudioPlayback()

  // Stable refs so WS / VAD callbacks never go stale
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

      <header style={{
        height: 'var(--topbar-h)',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        borderBottom: '1px solid var(--border)',
        position: 'relative',
        zIndex: 60,
        background: 'var(--bg)',
      }}>
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

          <div style={{
            fontSize: 11,
            color: 'var(--text-subtle)',
            display: 'flex', alignItems: 'center', gap: 5,
          }}>
            <span style={{ color: 'var(--border)' }}>|</span>
            <span style={{ color: 'var(--accent)', opacity: 0.75 }}>{scenarioLabel}</span>
          </div>
        </div>

        <div style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
          <SessionTimer running={isConnected} orbState={displayState} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TtfaBadge ttfa={ws.ttfa} />
          <InterruptButton onInterrupt={handleInterrupt} active={isProcessing} />
        </div>
      </header>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        <ScenarioSidebar
          selected={scenario}
          onSelect={setScenario}
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
            padding: '24px 20px 32px',
            overflowY: 'auto',
            background: `radial-gradient(ellipse 60% 50% at 50% 46%, rgba(180,130,60,0.07) 0%, transparent 70%), var(--bg)`,
          }}
          onClick={() => { if (sidebarOpen) setSidebarOpen(false) }}
        >
          <div style={{
            position: 'relative',
            marginBottom: 16,
            filter: isProcessing || isListening
              ? 'drop-shadow(0 0 28px rgba(212,164,96,0.25))'
              : 'none',
            transition: 'filter 0.6s',
          }}>
            <VoiceOrb state={displayState} size={260} />
          </div>

          <p style={{
            fontSize: 13,
            color: isConnected ? 'var(--text-muted)' : 'var(--text-subtle)',
            letterSpacing: '0.04em',
            height: 20,
            marginBottom: 24,
          }}>
            {STATE_LABEL[displayState] ?? displayState}
          </p>

          {ws.transcript.length > 0 && (
            <div style={{ width: '100%', maxWidth: 640, marginBottom: 20 }} className="animate-slide-up">
              <LiveTranscriptBox lines={ws.transcript} />
            </div>
          )}

          {!sessionStarted ? (
            <button
              onClick={() => void handleStart()}
              style={{
                padding: '13px 44px',
                borderRadius: 9999,
                background: 'var(--accent)',
                color: '#0D0B09',
                fontFamily: 'Inter, system-ui',
                fontWeight: 600,
                fontSize: 14,
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 0 24px rgba(212,164,96,0.35), 0 2px 8px rgba(0,0,0,0.4)',
                transition: 'transform 0.15s, box-shadow 0.2s',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1.03)'
                ;(e.currentTarget as HTMLElement).style.boxShadow = '0 0 32px rgba(240,188,110,0.5), 0 2px 8px rgba(0,0,0,0.4)'
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1)'
                ;(e.currentTarget as HTMLElement).style.boxShadow = '0 0 24px rgba(212,164,96,0.35), 0 2px 8px rgba(0,0,0,0.4)'
              }}
            >
              {ws.status === 'connecting' || mic.status === 'requesting'
                ? 'Connecting…'
                : 'Start Session'}
            </button>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
              {mic.status === 'capturing' && !isProcessing && (
                <p style={{ fontSize: 12, color: 'var(--text-subtle)', textAlign: 'center' }}>
                  Speak naturally — pause ~0.7s to send
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

              <button
                onClick={handleEnd}
                style={{
                  fontSize: 11,
                  color: 'var(--text-subtle)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  textDecoration: 'underline',
                  textUnderlineOffset: 3,
                }}
              >
                End session
              </button>
            </div>
          )}

          {mic.error && (
            <p style={{ fontSize: 11, color: 'var(--interrupt)', marginTop: 12, textAlign: 'center' }}>
              Mic error: {mic.error}
            </p>
          )}

          {ws.status === 'error' && (
            <p style={{ fontSize: 11, color: 'var(--interrupt)', marginTop: 12, textAlign: 'center' }}>
              Connection error — start the backend on port 8000
            </p>
          )}
        </main>
      </div>
    </div>
  )
}
