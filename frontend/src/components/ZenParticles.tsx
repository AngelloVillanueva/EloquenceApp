import { useEffect, useRef } from 'react'
import { useTheme } from '../theme/ThemeContext'

interface Particle {
  x: number
  y: number
  size: number
  speedX: number
  speedY: number
  baseAlpha: number
}

/** Mouse-aware amber dust from gold / night standard screens. */
export function ZenParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { theme } = useTheme()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let width = 0
    let height = 0
    let raf = 0
    const particles: Particle[] = []
    const mouse = { x: -999, y: -999 }
    const color = theme === 'night' ? '224, 176, 128' : '232, 168, 124'

    const resize = () => {
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }
    resize()

    particles.length = 0
    for (let i = 0; i < 48; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        size: Math.random() * 1.5,
        speedX: Math.random() * 0.5 - 0.25,
        speedY: Math.random() * 0.5 - 0.25,
        baseAlpha: Math.random() * 0.45 + 0.08,
      })
    }

    const onMove = (e: MouseEvent) => {
      mouse.x = e.clientX
      mouse.y = e.clientY
    }

    const tick = () => {
      ctx.clearRect(0, 0, width, height)
      for (const p of particles) {
        p.x += p.speedX
        p.y += p.speedY
        if (p.x > width) p.x = 0
        if (p.x < 0) p.x = width
        if (p.y > height) p.y = 0
        if (p.y < 0) p.y = height
        const dx = mouse.x - p.x
        const dy = mouse.y - p.y
        const dist = Math.hypot(dx, dy)
        if (dist < 150) {
          p.x -= dx * 0.01
          p.y -= dy * 0.01
        }
        ctx.fillStyle = `rgba(${color}, ${p.baseAlpha})`
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fill()
      }
      raf = requestAnimationFrame(tick)
    }

    window.addEventListener('resize', resize)
    window.addEventListener('mousemove', onMove)
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMove)
    }
  }, [theme])

  return <canvas ref={canvasRef} className="zen-particles" aria-hidden />
}
