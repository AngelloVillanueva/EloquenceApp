import { useEffect, useRef } from 'react'

/* Renders a canvas-based film-grain texture fixed over the whole app.
   Opacity is very low (0.035) — barely perceptible, just enough to kill the flatness. */
export function GrainOverlay() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current!
    const ctx    = canvas.getContext('2d')!
    let rafId    = 0
    let frame    = 0

    function resize() {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    function drawGrain() {
      frame++
      /* Refresh noise every 3 frames to keep it subtle & animated */
      if (frame % 3 !== 0) { rafId = requestAnimationFrame(drawGrain); return }

      const { width, height } = canvas
      const imageData = ctx.createImageData(width, height)
      const buf = imageData.data
      for (let i = 0; i < buf.length; i += 4) {
        const v = Math.random() > 0.5 ? 255 : 0
        buf[i]     = v
        buf[i + 1] = v
        buf[i + 2] = v
        buf[i + 3] = Math.random() * 18   /* very low alpha */
      }
      ctx.putImageData(imageData, 0, 0)
      rafId = requestAnimationFrame(drawGrain)
    }

    rafId = requestAnimationFrame(drawGrain)
    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 999,
        opacity: 0.035,
        mixBlendMode: 'overlay',
      }}
      aria-hidden
    />
  )
}
