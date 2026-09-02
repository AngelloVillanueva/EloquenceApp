/* ── WebSocket protocol types (mirrors app/ws/protocol.py) ── */

export type OrbState = 'idle' | 'listening' | 'thinking' | 'speaking'

export interface FeedbackPayload {
  grammar: Array<Record<string, unknown>>
  phrasing: Array<Record<string, unknown>>
  pronunciation: Array<Record<string, unknown>>
  notes: string
}

export type WsServerEvent =
  | { type: 'READY'; session_id: string; state: OrbState }
  | { type: 'STATE'; state: OrbState }
  | { type: 'TRANSCRIPT'; role: 'user' | 'assistant'; text: string }
  | { type: 'TOKEN'; delta?: string; text?: string }
  | { type: 'SENTENCE'; text: string }
  | { type: 'FEEDBACK'; feedback: FeedbackPayload }
  | { type: 'AUDIO_META'; sample_rate: number; engine: string; tts_s?: number }
  | { type: 'TURN_DONE'; timings: TurnTimings; has_feedback?: boolean }
  | { type: 'CANCELLED' }
  | { type: 'ERROR'; message: string }
  | { type: 'PONG' }

export interface TurnTimings {
  stt_s: number
  llm_s: number
  tts_s: number
  time_to_first_audio_s: number
  total_s: number
}

export interface TranscriptLine {
  role: 'user' | 'assistant'
  text: string
  id: string
}
