import { useCallback, useEffect, useRef, useState } from 'react'
import { downsample, floatToPcm16 } from '../audio/pcm'

const TARGET_RATE = 16000

/** RMS above this ≈ speech (calibrated for typical laptop mics). */
const SPEECH_RMS = 0.018
/** Silence must last this long after speech before END_TURN. */
const SILENCE_MS = 1500
/** Ignore tiny blips — require this much speech before arming VAD. */
const MIN_SPEECH_MS = 450

export type MicStatus = 'idle' | 'requesting' | 'capturing' | 'paused' | 'error'

interface UseMicCaptureOptions {
  onChunk: (pcm: ArrayBuffer) => void
  /** Fired once after speech → sustained silence (auto END_TURN). */
  onSpeechEnd?: () => void
  enabled: boolean
}

interface UseMicCaptureReturn {
  status: MicStatus
  error: string | null
  start: () => Promise<void>
  pause: () => void
  resume: () => void
  stop: () => void
}

function rms(samples: Float32Array): number {
  let sum = 0
  for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i]
  return Math.sqrt(sum / Math.max(samples.length, 1))
}

export function useMicCapture({
  onChunk,
  onSpeechEnd,
  enabled,
}: UseMicCaptureOptions): UseMicCaptureReturn {
  const [status, setStatus] = useState<MicStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  const ctxRef = useRef<AudioContext | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const nodeRef = useRef<AudioWorkletNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const sendingRef = useRef(false)
  const onChunkRef = useRef(onChunk)
  const onSpeechEndRef = useRef(onSpeechEnd)

  // VAD state
  const speechMsRef = useRef(0)
  const silenceMsRef = useRef(0)
  const armedRef = useRef(false)      // true after MIN_SPEECH_MS of voice
  const firedRef = useRef(false)      // prevent double END_TURN
  const lastTsRef = useRef(0)

  useEffect(() => { onChunkRef.current = onChunk }, [onChunk])
  useEffect(() => { onSpeechEndRef.current = onSpeechEnd }, [onSpeechEnd])

  const resetVad = useCallback(() => {
    speechMsRef.current = 0
    silenceMsRef.current = 0
    armedRef.current = false
    firedRef.current = false
    lastTsRef.current = 0
  }, [])

  const cleanup = useCallback(() => {
    sendingRef.current = false
    resetVad()
    nodeRef.current?.port.close()
    nodeRef.current?.disconnect()
    sourceRef.current?.disconnect()
    streamRef.current?.getTracks().forEach(t => t.stop())
    void ctxRef.current?.close().catch(() => {})
    nodeRef.current = null
    sourceRef.current = null
    streamRef.current = null
    ctxRef.current = null
  }, [resetVad])

  const start = useCallback(async () => {
    if (ctxRef.current) return
    setStatus('requesting')
    setError(null)
    resetVad()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          channelCount: 1,
        },
      })
      const ctx = new AudioContext()
      await ctx.audioWorklet.addModule('/pcm-capture-processor.js')

      const source = ctx.createMediaStreamSource(stream)
      const node = new AudioWorkletNode(ctx, 'pcm-capture-processor')

      node.port.onmessage = (ev: MessageEvent<Float32Array>) => {
        if (!sendingRef.current) return
        const samples = ev.data
        const now = performance.now()
        const dt = lastTsRef.current ? Math.min(now - lastTsRef.current, 80) : 20
        lastTsRef.current = now

        // --- energy VAD ---
        const level = rms(samples)
        if (level >= SPEECH_RMS) {
          speechMsRef.current += dt
          silenceMsRef.current = 0
          if (speechMsRef.current >= MIN_SPEECH_MS) armedRef.current = true
        } else if (armedRef.current) {
          silenceMsRef.current += dt
          if (!firedRef.current && silenceMsRef.current >= SILENCE_MS) {
            firedRef.current = true
            onSpeechEndRef.current?.()
          }
        }

        const down = downsample(samples, ctx.sampleRate, TARGET_RATE)
        onChunkRef.current(floatToPcm16(down))
      }

      source.connect(node)
      const mute = ctx.createGain()
      mute.gain.value = 0
      node.connect(mute)
      mute.connect(ctx.destination)

      streamRef.current = stream
      ctxRef.current = ctx
      sourceRef.current = source
      nodeRef.current = node
      sendingRef.current = true
      setStatus('capturing')
    } catch (err) {
      cleanup()
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
      setStatus('error')
    }
  }, [cleanup, resetVad])

  const pause = useCallback(() => {
    sendingRef.current = false
    resetVad()
    setStatus(s => (s === 'capturing' ? 'paused' : s))
  }, [resetVad])

  const resume = useCallback(() => {
    if (!ctxRef.current) return
    resetVad()
    sendingRef.current = true
    if (ctxRef.current.state === 'suspended') void ctxRef.current.resume()
    setStatus('capturing')
  }, [resetVad])

  const stop = useCallback(() => {
    cleanup()
    setStatus('idle')
  }, [cleanup])

  useEffect(() => {
    if (!enabled) stop()
  }, [enabled, stop])

  useEffect(() => () => cleanup(), [cleanup])

  return { status, error, start, pause, resume, stop }
}
