import { useEffect, useRef } from 'react'
import { FRAG_BY_FORM, VERT } from '../orb/shaders'
import { useOrbPalette } from '../theme/palette'
import type { OrbState } from '../types/ws'

interface Props {
  state: OrbState
  size?: number
}

const STATE_U: Record<OrbState, { intensity: number; speed: number; glow: number }> = {
  idle:      { intensity: 0.42, speed: 0.32, glow: 0.70 },
  listening: { intensity: 0.88, speed: 0.82, glow: 1.15 },
  thinking:  { intensity: 0.62, speed: 0.48, glow: 0.95 },
  speaking:  { intensity: 1.20, speed: 1.18, glow: 1.55 },
}

function compile(gl: WebGLRenderingContext, type: number, src: string): WebGLShader {
  const shader = gl.createShader(type)!
  gl.shaderSource(shader, src)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error('[VoiceOrb]', gl.getShaderInfoLog(shader))
  }
  return shader
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

export function VoiceOrb({ state, size = 240 }: Props) {
  const palette = useOrbPalette()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const stateRef = useRef(state)
  const rafRef = useRef(0)
  const curRef = useRef({ intensity: 0.42, speed: 0.32, glow: 0.70 })
  const mouseRef = useRef({ x: 0.5, y: 0.5 })

  useEffect(() => { stateRef.current = state }, [state])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl', {
      alpha: false,
      antialias: true,
      premultipliedAlpha: false,
    })
    if (!gl) return

    const prog = gl.createProgram()!
    const frag = FRAG_BY_FORM[palette.form]
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VERT))
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, frag))
    gl.linkProgram(prog)
    gl.useProgram(prog)

    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(prog, 'a_position')
    gl.enableVertexAttribArray(loc)
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

    const uTime = gl.getUniformLocation(prog, 'u_time')
    const uRes = gl.getUniformLocation(prog, 'u_resolution')
    const uMouse = gl.getUniformLocation(prog, 'u_mouse')
    const uIntensity = gl.getUniformLocation(prog, 'u_intensity')
    const uSpeed = gl.getUniformLocation(prog, 'u_speed')
    const uGlow = gl.getUniformLocation(prog, 'u_glow')

    // Colours change only with the theme, which re-runs this effect.
    gl.uniform3fv(gl.getUniformLocation(prog, 'u_core'), palette.core)
    gl.uniform3fv(gl.getUniformLocation(prog, 'u_glow1'), palette.glow1)
    gl.uniform3fv(gl.getUniformLocation(prog, 'u_glow2'), palette.glow2)

    const syncSize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const px = Math.round(size * dpr)
      if (canvas.width !== px || canvas.height !== px) {
        canvas.width = px
        canvas.height = px
      }
      gl.viewport(0, 0, canvas.width, canvas.height)
    }
    syncSize()

    const onMove = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      if (!rect.width || !rect.height) return
      mouseRef.current = {
        x: (event.clientX - rect.left) / rect.width,
        y: 1 - (event.clientY - rect.top) / rect.height,
      }
    }
    window.addEventListener('mousemove', onMove)

    const t0 = performance.now()

    const frame = (now: number) => {
      const tgt = STATE_U[stateRef.current] ?? STATE_U.idle
      const c = curRef.current
      c.intensity = lerp(c.intensity, tgt.intensity, 0.06)
      c.speed = lerp(c.speed, tgt.speed, 0.05)
      c.glow = lerp(c.glow, tgt.glow, 0.06)

      gl.uniform1f(uTime, (now - t0) * 0.001)
      gl.uniform2f(uRes, canvas.width, canvas.height)
      gl.uniform2f(uMouse, mouseRef.current.x * canvas.width, mouseRef.current.y * canvas.height)
      gl.uniform1f(uIntensity, c.intensity)
      gl.uniform1f(uSpeed, c.speed)
      gl.uniform1f(uGlow, c.glow)
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      rafRef.current = requestAnimationFrame(frame)
    }

    rafRef.current = requestAnimationFrame(frame)
    return () => {
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('mousemove', onMove)
    }
  }, [size, palette])

  const stage = size + 80
  const live = state === 'speaking' || state === 'listening'

  return (
    <div
      className="orb-stage"
      style={{ width: stage, height: stage }}
      aria-label={`Voice orb — ${state}`}
    >
      <div className="orb-ring orb-ring-a" />
      <div className="orb-ring orb-ring-b" />
      <svg className="orb-ticks orb-ticks-outer" viewBox="0 0 100 100" aria-hidden>
        <circle cx="50" cy="50" fill="none" r="48" stroke="currentColor" strokeDasharray="1 3" strokeWidth="0.5" />
      </svg>
      <svg className="orb-ticks orb-ticks-inner" viewBox="0 0 100 100" aria-hidden>
        <circle cx="50" cy="50" fill="none" r="48" stroke="currentColor" strokeDasharray="2 4" strokeWidth="0.3" />
      </svg>
      <div
        className="orb-shader"
        style={{
          width: size,
          height: size,
          boxShadow: live
            ? '0 0 80px var(--orb-shadow-live)'
            : '0 0 48px var(--orb-shadow-idle)',
        }}
      >
        <canvas
          ref={canvasRef}
          style={{ width: size, height: size, display: 'block' }}
        />
        <div className="orb-fallback-glow" />
      </div>
    </div>
  )
}
