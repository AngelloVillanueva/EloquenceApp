export interface MemoryError {
  kind: string
  original: string
  correction: string
  note?: string
  count: number
}

export interface MemoryVocab {
  word_or_phrase: string
  context?: string
}

export interface MemorySession {
  scenario: string
  duration_s: number | null
  ttfa_avg: number | null
  started_at?: string
  ended_at: string | null
}

export interface MemorySnapshot {
  user: { display_name: string; level: string } | null
  sessions: number
  sessions_week: number
  minutes_total: number
  minutes_week: number
  streak_days: number
  slip_count: number
  last_session: MemorySession | null
  recent_sessions: MemorySession[]
  errors: MemoryError[]
  vocab: MemoryVocab[]
  brief: string
}

export interface ShadowCoach {
  word: string
  fixes: string[]
}

export interface ShadowPrompt {
  id: string
  text: string
  tip: string
  /** Spanish meaning: curated for the bank, LLM gloss for your own slips. */
  es?: string
  kind: 'pronunciation' | 'bank' | string
  coach?: ShadowCoach[]
}

export interface ShadowWord {
  word: string
  ok: boolean
}

export interface ShadowResult {
  heard: string
  target: string
  hits: number
  total: number
  ratio: number
  close: boolean
  words: ShadowWord[]
  coach: ShadowCoach[]
}
