import { useEffect, useState } from 'react'
import { BrandMark } from '../components/BrandMark'
import { GrainOverlay } from '../components/GrainOverlay'
import { SCENARIOS } from '../components/ScenarioSidebar'
import { ThemePicker } from '../components/ThemePicker'
import { VoiceOrb } from '../components/VoiceOrb'
import { ZenParticles } from '../components/ZenParticles'
import { useOrbSize } from '../hooks/useOrbSize'
import type { MemorySnapshot } from '../types/memory'

interface Props {
  onStart: (scenario: string) => void
  onShadow: (phrase?: string) => void
}

function greeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
}

function scenarioTitle(id: string): string {
  return SCENARIOS.find((s) => s.id === id)?.title ?? id
}

function formatMins(s: number | null | undefined): string {
  return `${Math.max(0, Math.round((s ?? 0) / 60))} min`
}

function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div>
      <span className="hub-stat-value">{value}</span>
      <span className="hub-stat-label">{label}</span>
    </div>
  )
}

export function HubPage({ onStart, onShadow }: Props) {
  const orbSize = useOrbSize(208)
  const [selected, setSelected] = useState('free')
  const [snap, setSnap] = useState<MemorySnapshot | null>(null)

  useEffect(() => {
    let cancelled = false
    void fetch('/api/memory')
      .then((r) => (r.ok ? r.json() : null))
      .then((data: MemorySnapshot | null) => {
        if (!cancelled && data) setSnap(data)
      })
      .catch(() => {})
    return () => { cancelled = true }
  }, [])

  const name = snap?.user?.display_name ?? 'Angello'
  const level = snap?.user?.level ?? 'B2'
  const last = snap?.last_session
  const focus = SCENARIOS.find((s) => s.id === selected)

  return (
    <div className="studio-shell">
      <GrainOverlay />
      <ZenParticles />

      <header className="studio-topbar">
        <BrandMark />
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {snap && snap.streak_days > 0 && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-caption)', color: 'var(--text-subtle)' }}>
              {snap.streak_days}d streak
            </span>
          )}
          <ThemePicker />
        </div>
      </header>

      <main className="hub-main">
        <section className="hub-hero">
          <VoiceOrb state="idle" size={orbSize} />

          <p className="hub-kicker">Studio ready</p>
          <h1 className="hub-hello">
            {greeting()}, {name}.
          </h1>
          <p className="hub-meta">
            Level {level} · {focus ? focus.title : 'pick a focus'}
          </p>

          <div className="hub-actions">
            <button type="button" className="btn-start hub-start" onClick={() => onStart(selected)}>
              Start Session
            </button>
            <p className="hub-start-sub">
              {focus ? `${focus.sub} · ${focus.level}` : 'Choose a session focus'}
            </p>

            <button type="button" className="hub-secondary" onClick={() => onShadow()}>
              <span>
                <span className="hub-secondary-title">Listen &amp; Repeat</span>
                <span className="hub-secondary-sub">Shadow your slips and C1 phrases</span>
              </span>
              <span className="hub-secondary-cta">Open</span>
            </button>
          </div>

          <p className="hub-last">
            {last
              ? `Last session: ${formatMins(last.duration_s)} · ${scenarioTitle(last.scenario)}${last.ttfa_avg ? ` · TTFA ${last.ttfa_avg.toFixed(1)}s` : ''}`
              : 'No sessions yet — pick a focus and start.'}
          </p>
        </section>

        <aside className="hub-panel">
          <section className="hub-panel-section">
            <p className="hub-kicker">Session focus</p>
            <div className="hub-focus-list" role="radiogroup" aria-label="Session focus">
              {SCENARIOS.map((s) => {
                const active = s.id === selected
                return (
                  <button
                    key={s.id}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    className={active ? 'hub-focus-row hub-focus-row-active' : 'hub-focus-row'}
                    onClick={() => setSelected(s.id)}
                  >
                    <span className="hub-focus-emoji">{s.emoji}</span>
                    <span className="hub-focus-label">
                      <span className="hub-focus-title">{s.title}</span>
                      <span className="hub-focus-sub">{s.sub} · {s.level}</span>
                    </span>
                    {active && <span className="hub-focus-dot" />}
                  </button>
                )
              })}
            </div>
          </section>

          <section className="hub-panel-section">
            <p className="hub-kicker">Progress</p>
            <div className="hub-stat-grid">
              <Stat value={snap?.sessions_week ?? 0} label="sessions this week" />
              <Stat value={`${snap?.minutes_week ?? 0}m`} label="minutes this week" />
              <Stat value={snap?.streak_days ?? 0} label="day streak" />
              <Stat value={snap?.slip_count ?? 0} label="slips tracked" />
            </div>
          </section>

          {snap && snap.errors.length > 0 && (
            <section className="hub-panel-section">
              <p className="hub-kicker">Words to polish</p>
              <div className="hub-chips">
                {snap.errors.slice(0, 6).map((e, i) => (
                  <button
                    key={`${e.kind}-${e.original}-${i}`}
                    type="button"
                    className="hub-chip"
                    title="Practice in Listen & Repeat"
                    onClick={() => onShadow(e.kind === 'pronunciation' ? e.original : e.correction)}
                  >
                    {e.correction || e.original}
                  </button>
                ))}
              </div>
            </section>
          )}

          {snap && snap.vocab.length > 0 && (
            <section className="hub-panel-section">
              <p className="hub-kicker">Recent targets</p>
              <div className="hub-chips">
                {snap.vocab.slice(0, 5).map((v) => (
                  <span key={v.word_or_phrase} className="hub-chip hub-chip-static">
                    {v.word_or_phrase}
                  </span>
                ))}
              </div>
            </section>
          )}
        </aside>
      </main>
    </div>
  )
}
