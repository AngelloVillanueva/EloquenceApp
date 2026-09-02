import { useCallback, useRef } from 'react'
import { pcm16ToFloat32 } from '../audio/pcm'

interface UseAudioPlaybackReturn {
  setSampleRate: (sr: number) => void
  enqueue: (pcm: ArrayBuffer) => Promise<void>
  stop: () => void
}

export function useAudioPlayback(): UseAudioPlaybackReturn {
  const ctxRef = useRef<AudioContext | null>(null)
  const nextTimeRef = useRef(0)
  const sourcesRef = useRef<AudioBufferSourceNode[]>([])
  const sampleRateRef = useRef(24000)

  const ensureCtx = useCallback(async (sampleRate: number) => {
    if (!ctxRef.current || ctxRef.current.sampleRate !== sampleRate) {
      if (ctxRef.current) await ctxRef.current.close().catch(() => {})
      ctxRef.current = new AudioContext({ sampleRate })
      nextTimeRef.current = 0
    }
    if (ctxRef.current.state === 'suspended') await ctxRef.current.resume()
    sampleRateRef.current = sampleRate
    return ctxRef.current
  }, [])

  const setSampleRate = useCallback((sr: number) => {
    sampleRateRef.current = sr
  }, [])

  const stop = useCallback(() => {
    for (const src of sourcesRef.current) {
      try { src.stop() } catch { /* already stopped */ }
    }
    sourcesRef.current = []
    nextTimeRef.current = ctxRef.current?.currentTime ?? 0
  }, [])

  const enqueue = useCallback(async (pcm: ArrayBuffer) => {
    const sr = sampleRateRef.current
    const ctx = await ensureCtx(sr)
    const float32 = pcm16ToFloat32(pcm)
    if (float32.length === 0) return

    const buf = ctx.createBuffer(1, float32.length, sr)
    buf.copyToChannel(float32, 0)

    const src = ctx.createBufferSource()
    src.buffer = buf
    src.connect(ctx.destination)

    const startAt = Math.max(ctx.currentTime + 0.02, nextTimeRef.current)
    src.start(startAt)
    nextTimeRef.current = startAt + buf.duration
    sourcesRef.current.push(src)
    src.onended = () => {
      sourcesRef.current = sourcesRef.current.filter(x => x !== src)
    }
  }, [ensureCtx])

  return { setSampleRate, enqueue, stop }
}
