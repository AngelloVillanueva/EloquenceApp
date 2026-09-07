import { useCallback, useEffect, useRef, useState } from 'react'
import { BrandMark } from '../components/BrandMark'
import { GrainOverlay } from '../components/GrainOverlay'
import { ThemePicker } from '../components/ThemePicker'
import { VoiceOrb } from '../components/VoiceOrb'
import { ZenParticles } from '../components/ZenParticles'
import { useMicCapture } from '../hooks/useMicCapture'
import { useOrbSize } from '../hooks/useOrbSize'
import type { OrbState } from '../types/ws'
import type { ShadowCoach, ShadowPrompt, ShadowResult } from '../types/memory'

interface Props {
  initialPhrase?: string | null
  onBack: () => void
}

type Phase = 'idle' | 'playing' | 'recording' | 'scoring'

const ORB_STATE: Record<Phase, OrbState> = {
  idle: 'idle',
  playing: 'speaking',
  recording: 'listening',
  scoring: 'thinking',
}

const PHASE_HINT: Record<Phase, string> = {
  idle: 'Escucha el modelo, luego repite. Las correcciones se quedan en pantalla.',
  playing: 'Eloquence está diciendo la frase — fíjate en el ritmo.',
  recording: 'Habla la frase completa — pausa ~1.5 s para enviar.',
  scoring: 'Comparando con lo que dijiste…',
}

function concatPcm(chunks: ArrayBuffer[]): ArrayBuffer {
  const total = chunks.reduce((n, c) => n + c.byteLength, 0)
  const out = new Uint8Array(total)
  let off = 0
  for (const c of chunks) {
    out.set(new Uint8Array(c), off)
    off += c.byteLength
  }
  return out.buffer
}

function toB64(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf)
  const chunk = 0x8000
  let s = ''
  for (let i = 0; i < bytes.length; i += chunk) {
    s += String.fromCharCode(...bytes.subarray(i, i + chunk))
  }
  return btoa(s)
}

function CoachBlock({ items, title }: { items: ShadowCoach[]; title: string }) {
  if (items.length === 0) return null
  return (
    <section className="hub-panel-section">
      <p className="hub-kicker">{title}</p>
      <div className="shadow-coach-list">
        {items.map((item) => (
          <div className="shadow-coach-item" key={item.word}>
            <p className="shadow-coach-word">{item.word}</p>
            {item.fixes.map((fix, i) => (
              <p className="shadow-coach-fix" key={i}>{fix}</p>
            ))}
          </div>
        ))}
      </div>
    </section>
  )
}

export function ShadowPage({ initialPhrase, onBack }: Props) {
  const [prompts, setPrompts] = useState<ShadowPrompt[]>([])
  const [index, setIndex] = useState(0)
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<ShadowResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [glosses, setGlosses] = useState<Record<string, string>>({})
  const chunksRef = useRef<ArrayBuffer[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const glossAskedRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    let cancelled = false
    void fetch('/api/shadow/prompts')
      .then((r) => (r.ok ? r.json() : { prompts: [] }))
      .then((data: { prompts?: ShadowPrompt[] }) => {
        if (cancelled) return
        const list = data.prompts ?? []
        const seed = initialPhrase?.trim()
        if (seed) {
          const existing = list.findIndex(
            (p) => p.text.toLowerCase() === seed.toLowerCase(),
          )
          if (existing >= 0) {
            setPrompts(list)
            setIndex(existing)
            return
          }
          setPrompts([
            {
              id: 'seed',
              text: seed,
              tip: 'From your last notes — listen, then repeat.',
              kind: 'pronunciation',
            },
            ...list,
          ])
          setIndex(0)
        } else {
          setPrompts(list)
        }
      })
      .catch(() => {
        const seed = initialPhrase?.trim()
        if (!cancelled && seed) {
          setPrompts([{ id: 'seed', text: seed, tip: 'Listen once, then repeat.', kind: 'pronunciation' }])
        }
      })
    return () => { cancelled = true }
  }, [initialPhrase])

  const current = prompts[index] ?? null
  const spanish = current ? (current.es?.trim() || glosses[current.text] || '') : ''

  /** Curated Spanish for the bank; local Ollama gloss for your own slips. */
  useEffect(() => {
    const text = current?.text
    if (!text || current?.es?.trim() || glossAskedRef.current.has(text)) return
    glossAskedRef.current.add(text)
    let cancelled = false
    void fetch('/api/shadow/gloss', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
      .then((r) => (r.ok ? r.json() : { es: '' }))
      .then((data: { es?: string }) => {
        if (!cancelled && data.es) {
          setGlosses((prev) => ({ ...prev, [text]: data.es as string }))
        }
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [current])

  const evaluate = useCallback(async () => {
    if (!current) return
    const pcm = concatPcm(chunksRef.current)
    chunksRef.current = []
    if (pcm.byteLength < 3200) {
      setError('Muy corto — di la frase completa.')
      setPhase('idle')
      return
    }
    setPhase('scoring')
    setError(null)
    try {
      const res = await fetch('/api/shadow/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: current.text,
          pcm_b64: toB64(pcm),
          sample_rate: 16000,
        }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error((detail as { detail?: string }).detail || 'Evaluate failed')
      }
      setResult((await res.json()) as ShadowResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No pude evaluar ese intento')
    } finally {
      setPhase('idle')
    }
  }, [current])

  const pauseMicRef = useRef<() => void>(() => {})

  const handleSpeechEnd = useCallback(() => {
    pauseMicRef.current()
    void evaluate()
  }, [evaluate])

  const mic = useMicCapture({
    onChunk: (pcm) => { chunksRef.current.push(pcm) },
    onSpeechEnd: handleSpeechEnd,
    enabled: phase === 'recording',
  })

  useEffect(() => {
    pauseMicRef.current = mic.pause
  }, [mic.pause])

  useEffect(() => {
    if (phase === 'recording') {
      chunksRef.current = []
      void mic.start()
    }
  }, [phase, mic.start])

  const play = useCallback(async () => {
    if (!current) return
    audioRef.current?.pause()
    setPhase('playing')
    setError(null)
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: current.text }),
      })
      if (!res.ok) throw new Error('TTS failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => {
        URL.revokeObjectURL(url)
        setPhase('idle')
      }
      await audio.play()
    } catch {
      setError('No pude reproducir la voz modelo — ¿está el backend arriba?')
      setPhase('idle')
    }
  }, [current])

  const startRecord = useCallback(() => {
    audioRef.current?.pause()
    setResult(null)
    setError(null)
    setPhase('recording')
  }, [])

  const move = useCallback((delta: number) => {
    audioRef.current?.pause()
    setResult(null)
    setError(null)
    setPhase('idle')
    setIndex((i) => {
      const n = prompts.length
      if (!n) return 0
      return (i + delta + n) % n
    })
  }, [prompts.length])

  const orbState = ORB_STATE[phase]
  const orbSize = useOrbSize(176)
  const howTo = current?.coach ?? []

  return (
    <div className="studio-shell">
      <GrainOverlay />
      <ZenParticles />

      <header className="studio-topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <BrandMark />
          <span style={{ color: 'var(--text-subtle)', fontSize: 'var(--fs-body-sm)' }}>
            Listen &amp; Repeat
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <ThemePicker />
          <button type="button" className="btn-end" onClick={onBack}>
            Hub
          </button>
        </div>
      </header>

      <main className="shadow-main">
        <section className="shadow-stage">
          <VoiceOrb state={orbState} size={orbSize} />

          {current ? (
            <>
              <p className="hub-kicker">
                Phrase {index + 1} / {prompts.length || 1}
                {current.kind === 'pronunciation' ? ' · from your notes' : ''}
              </p>

              <p className="shadow-phrase">
                {result
                  ? result.words.map((w, i) => (
                      <span key={`${w.word}-${i}`} className={w.ok ? 'shadow-word-ok' : 'shadow-word-miss'}>
                        {w.word}{' '}
                      </span>
                    ))
                  : current.text}
              </p>

              {spanish && <p className="shadow-es">{spanish}</p>}

              <p className="shadow-tip">{current.tip}</p>

              <div className="shadow-actions">
                <button
                  type="button"
                  className="btn-end"
                  onClick={() => move(-1)}
                  disabled={prompts.length < 2}
                  aria-label="Previous phrase"
                >
                  ← Prev
                </button>
                <button type="button" className="btn-end" onClick={() => void play()} disabled={phase === 'playing'}>
                  {phase === 'playing' ? 'Playing…' : 'Listen'}
                </button>
                <button
                  type="button"
                  className="btn-start"
                  onClick={startRecord}
                  disabled={phase === 'recording' || phase === 'scoring'}
                >
                  {phase === 'recording' ? 'Listening…' : phase === 'scoring' ? 'Checking…' : 'Repeat'}
                </button>
                <button
                  type="button"
                  className="btn-end"
                  onClick={() => move(1)}
                  disabled={prompts.length < 2}
                  aria-label="Next phrase"
                >
                  Next →
                </button>
              </div>

              <p className="shadow-hint">{PHASE_HINT[phase]}</p>
            </>
          ) : (
            <p className="hub-meta">Loading phrases…</p>
          )}

          {error && <p className="shadow-error">{error}</p>}
          {mic.error && <p className="shadow-error">Mic: {mic.error}</p>}
        </section>

        <aside className="hub-panel">
          {result && (
            <section className="hub-panel-section">
              <p className="hub-kicker">Tu intento</p>
              <p className={`shadow-score ${result.close ? 'shadow-score-ok' : 'shadow-score-warn'}`}>
                {result.hits} / {result.total} palabras
              </p>
              <p className="shadow-score-note">
                {result.heard ? `Dijiste “${result.heard}”` : 'No escuché nada.'}
                {result.close ? ' Va bien, sigue cuando quieras.' : ' Intenta una vez más.'}
              </p>
            </section>
          )}

          {result && result.coach.length > 0 && (
            <CoachBlock items={result.coach} title="Cómo corregirlo" />
          )}

          <CoachBlock items={howTo} title="Cómo pronunciarla" />

          {!result && howTo.length === 0 && (
            <section className="hub-panel-section">
              <p className="hub-kicker">Cómo funciona</p>
              <ol className="shadow-steps">
                <li>Pulsa <strong>Listen</strong> y escucha el ritmo del modelo.</li>
                <li>Pulsa <strong>Repeat</strong> y di la frase completa.</li>
                <li>Las palabras que falten quedan subrayadas, con la corrección aquí.</li>
              </ol>
            </section>
          )}

          {prompts.length > 1 && (
            <section className="hub-panel-section">
              <p className="hub-kicker">En la cola</p>
              <div className="hub-focus-list">
                {prompts.map((p, i) => {
                  const active = i === index
                  return (
                    <button
                      key={p.id}
                      type="button"
                      className={active ? 'hub-focus-row hub-focus-row-active' : 'hub-focus-row'}
                      onClick={() => move(i - index)}
                    >
                      <span className="hub-focus-label">
                        <span className="hub-focus-title">{p.text}</span>
                        <span className="hub-focus-sub">
                          {p.kind === 'pronunciation' ? 'De tus notas' : 'Banco C1'}
                        </span>
                      </span>
                      {active && <span className="hub-focus-dot" />}
                    </button>
                  )
                })}
              </div>
            </section>
          )}
        </aside>
      </main>
    </div>
  )
}
