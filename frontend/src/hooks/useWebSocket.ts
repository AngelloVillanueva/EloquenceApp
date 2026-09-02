import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  FeedbackPayload,
  OrbState,
  TranscriptLine,
  TurnTimings,
  WsServerEvent,
} from '../types/ws'

/** Prefer Vite proxy (/ws → :8000) when on same host; override with VITE_WS_URL. */
const WS_URL =
  import.meta.env.VITE_WS_URL ??
  `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/audio`

export type WsStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

interface UseWebSocketOptions {
  onPcm?: (pcm: ArrayBuffer) => void
  onAudioMeta?: (sampleRate: number) => void
  onCancelled?: () => void
  onTurnDone?: () => void
}

interface UseWebSocketReturn {
  status: WsStatus
  orbState: OrbState
  transcript: TranscriptLine[]
  feedback: FeedbackPayload | null
  ttfa: number | null
  connect: () => void
  disconnect: () => void
  sendEndTurn: () => void
  sendCancel: () => void
  sendAudioChunk: (pcm: ArrayBuffer) => void
  setOrbState: (s: OrbState) => void
}

export function useWebSocket(opts: UseWebSocketOptions = {}): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null)
  const optsRef = useRef(opts)
  useEffect(() => { optsRef.current = opts }, [opts])

  const [status, setStatus] = useState<WsStatus>('disconnected')
  const [orbState, setOrbState] = useState<OrbState>('idle')
  const [transcript, setTranscript] = useState<TranscriptLine[]>([])
  const [feedback, setFeedback] = useState<FeedbackPayload | null>(null)
  const [ttfa, setTtfa] = useState<number | null>(null)

  const handleMessage = useCallback((event: MessageEvent) => {
    if (typeof event.data !== 'string') {
      optsRef.current.onPcm?.(event.data as ArrayBuffer)
      return
    }

    let msg: WsServerEvent
    try { msg = JSON.parse(event.data) } catch { return }

    switch (msg.type) {
      case 'READY':
        setOrbState(msg.state)
        break
      case 'STATE': {
        const s = msg.state === 'transcribing' ? 'thinking' : msg.state
        setOrbState(s as OrbState)
        break
      }
      case 'TRANSCRIPT':
        setTranscript(prev => [
          ...prev,
          { role: msg.role, text: msg.text, id: crypto.randomUUID() },
        ])
        break
      case 'FEEDBACK':
        setFeedback(msg.feedback)
        break
      case 'AUDIO_META':
        optsRef.current.onAudioMeta?.(msg.sample_rate)
        break
      case 'TURN_DONE':
        setTtfa((msg.timings as TurnTimings).time_to_first_audio_s)
        setOrbState('idle')
        optsRef.current.onTurnDone?.()
        break
      case 'CANCELLED':
        setOrbState('idle')
        optsRef.current.onCancelled?.()
        break
      case 'ERROR':
        console.error('[ws]', msg.message)
        break
    }
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    setStatus('connecting')
    setTranscript([])
    setFeedback(null)
    setTtfa(null)

    const ws = new WebSocket(WS_URL)
    ws.binaryType = 'arraybuffer'
    ws.onopen = () => {
      setStatus('connected')
      ws.send(JSON.stringify({ type: 'CONFIG', sample_rate: 16000 }))
    }
    ws.onmessage = handleMessage
    ws.onclose = () => {
      setStatus('disconnected')
      setOrbState('idle')
    }
    ws.onerror = () => setStatus('error')
    wsRef.current = ws
  }, [handleMessage])

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    setStatus('disconnected')
    setOrbState('idle')
  }, [])

  const sendJson = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
    }
  }, [])

  const sendEndTurn = useCallback(() => sendJson({ type: 'END_TURN' }), [sendJson])
  const sendCancel = useCallback(() => sendJson({ type: 'CANCEL_AUDIO' }), [sendJson])

  const sendAudioChunk = useCallback((pcm: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(pcm)
    }
  }, [])

  useEffect(() => () => { wsRef.current?.close() }, [])

  return {
    status,
    orbState,
    transcript,
    feedback,
    ttfa,
    connect,
    disconnect,
    sendEndTurn,
    sendCancel,
    sendAudioChunk,
    setOrbState,
  }
}
