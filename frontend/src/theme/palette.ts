import { useMemo } from 'react'
import { useTheme } from './ThemeContext'

export type Rgb01 = [number, number, number]

/** Orb form: which shader draws the orb. Themes pick one via `--orb-form`. */
export type OrbForm = 'liquid' | 'core'

export interface OrbPalette {
  core: Rgb01
  glow1: Rgb01
  glow2: Rgb01
  form: OrbForm
}

const FALLBACK: Rgb01 = [0.91, 0.66, 0.49]

export function readVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

/** `#E8A87C` / `#e8a` → [0..1, 0..1, 0..1] for WebGL uniforms. */
export function hexToRgb01(hex: string): Rgb01 {
  const raw = hex.trim().replace('#', '')
  const full = raw.length === 3 ? raw.replace(/./g, (c) => c + c) : raw
  if (full.length !== 6 || /[^0-9a-f]/i.test(full)) return FALLBACK
  const n = parseInt(full, 16)
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]
}

/** `#E8A87C` → `232, 168, 124`, ready for a canvas `rgba()` string. */
export function hexToRgbChannels(hex: string): string {
  return hexToRgb01(hex)
    .map((v) => Math.round(v * 255))
    .join(', ')
}

function readOrbPalette(): OrbPalette {
  const form = readVar('--orb-form')
  return {
    core: hexToRgb01(readVar('--orb-core')),
    glow1: hexToRgb01(readVar('--orb-glow-1')),
    glow2: hexToRgb01(readVar('--orb-glow-2')),
    form: form === 'core' ? 'core' : 'liquid',
  }
}

/** Orb colours follow the active theme's tokens rather than the shader source. */
export function useOrbPalette(): OrbPalette {
  const { theme } = useTheme()
  // Safe to read during render: ThemeContext writes `data-theme` before
  // the re-render that changes `theme`.
  return useMemo(readOrbPalette, [theme])
}
