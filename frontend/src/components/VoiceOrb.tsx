import { useEffect, useRef } from 'react'
import type { OrbState } from '../types/ws'

interface Props {
  state: OrbState
  size?: number
}

/** Intensity / motion driven by session state — feeds WebGL uniforms. */
const STATE_U: Record<OrbState, { intensity: number; speed: number; glow: number }> = {
  idle:      { intensity: 0.35, speed: 0.35, glow: 0.55 },
  listening: { intensity: 0.75, speed: 0.90, glow: 1.10 },
  thinking:  { intensity: 0.55, speed: 0.55, glow: 0.95 },
  speaking:  { intensity: 1.20, speed: 1.35, glow: 1.55 },
}

const VERT = `
attribute vec2 a_position;
varying vec2 v_uv;
void main() {
  v_uv = a_position;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`

const FRAG = `
precision highp float;
varying vec2 v_uv;
uniform float u_time;
uniform float u_intensity;
uniform float u_speed;
uniform float u_glow;
uniform vec2  u_resolution;

vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                 + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
                          dot(x12.zw,x12.zw)), 0.0);
  m = m*m; m = m*m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 a0 = x - floor(x + 0.5);
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
  vec3 g;
  g.x  = a0.x * x0.x  + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 uv = v_uv;
  uv.x *= u_resolution.x / u_resolution.y;

  float t = u_time * u_speed;

  // Organic fluid mesh (Stitch-style simplex)
  float n1 = snoise(uv * 1.4 + t * 0.35);
  float n2 = snoise(uv * 2.6 - t * 0.22);
  float noise = n1 * 0.7 + n2 * 0.3;

  float radius = 0.42 + 0.07 * noise * u_intensity;
  float d = length(uv) - radius;

  // Soft body fill (warm amber core)
  float body = smoothstep(0.04, -0.12, d);
  float pulse = 0.55 + 0.45 * sin(t * 1.8);
  vec3 amber = vec3(0.91, 0.66, 0.49);
  vec3 core  = vec3(1.00, 0.92, 0.78);
  vec3 fill  = mix(amber * 0.35, core, body * pulse * 0.55) * body * u_glow;

  // Edge glow / neon bloom
  float edge = 0.018 / max(abs(d + 0.01), 0.001);
  edge *= (0.75 + 0.25 * pulse) * u_glow;
  fill += amber * edge * u_intensity;

  // Concentric ripple rings (booth-a1)
  float rings = 0.0;
  for (int i = 1; i <= 4; i++) {
    float ri = 0.48 + float(i) * 0.085;
    float rd = abs(length(uv) - ri - 0.01 * sin(t * 1.2 + float(i)));
    rings += smoothstep(0.012, 0.0, rd) * (0.18 / float(i)) * u_intensity;
  }
  fill += amber * rings;

  // Soft vignette atmosphere
  fill += vec3(0.06, 0.05, 0.04) * (1.0 - length(uv) * 0.55) * 0.5;

  // Discard far field for circular canvas look
  float alpha = smoothstep(0.95, 0.55, length(uv));
  gl_FragColor = vec4(fill, alpha);
}`

function compile(gl: WebGLRenderingContext, type: number, src: string) {
  const s = gl.createShader(type)!
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.error(gl.getShaderInfoLog(s))
  }
  return s
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t
}

export function VoiceOrb({ state, size = 280 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const stateRef = useRef(state)
  const rafRef = useRef(0)
  const curRef = useRef({ intensity: 0.35, speed: 0.35, glow: 0.55 })

  useEffect(() => { stateRef.current = state }, [state])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl', {
      alpha: true,
      antialias: true,
      premultipliedAlpha: false,
    })
    if (!gl) return

    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const px = Math.round(size * dpr)
    canvas.width = px
    canvas.height = px
    canvas.style.width = `${size}px`
    canvas.style.height = `${size}px`

    const prog = gl.createProgram()!
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VERT))
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FRAG))
    gl.linkProgram(prog)
    gl.useProgram(prog)

    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(prog, 'a_position')
    gl.enableVertexAttribArray(loc)
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

    const uTime = gl.getUniformLocation(prog, 'u_time')
    const uIntensity = gl.getUniformLocation(prog, 'u_intensity')
    const uSpeed = gl.getUniformLocation(prog, 'u_speed')
    const uGlow = gl.getUniformLocation(prog, 'u_glow')
    const uRes = gl.getUniformLocation(prog, 'u_resolution')

    gl.enable(gl.BLEND)
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
    gl.viewport(0, 0, px, px)

    const t0 = performance.now()

    function frame(now: number) {
      const tgt = STATE_U[stateRef.current]
      const c = curRef.current
      c.intensity = lerp(c.intensity, tgt.intensity, 0.06)
      c.speed = lerp(c.speed, tgt.speed, 0.05)
      c.glow = lerp(c.glow, tgt.glow, 0.06)

      gl!.clearColor(0, 0, 0, 0)
      gl!.clear(gl!.COLOR_BUFFER_BIT)
      gl!.uniform1f(uTime, (now - t0) * 0.001)
      gl!.uniform1f(uIntensity, c.intensity)
      gl!.uniform1f(uSpeed, c.speed)
      gl!.uniform1f(uGlow, c.glow)
      gl!.uniform2f(uRes, px, px)
      gl!.drawArrays(gl!.TRIANGLE_STRIP, 0, 4)

      rafRef.current = requestAnimationFrame(frame)
    }

    rafRef.current = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(rafRef.current)
  }, [size])

  return (
    <canvas
      ref={canvasRef}
      style={{
        display: 'block',
        borderRadius: '50%',
        filter: state === 'speaking' || state === 'listening'
          ? 'drop-shadow(0 0 32px rgba(232,168,124,0.35))'
          : 'drop-shadow(0 0 16px rgba(232,168,124,0.12))',
        transition: 'filter 0.5s',
      }}
      aria-label={`Voice orb — ${state}`}
    />
  )
}
