import { useEffect, useState } from 'react'

/**
 * Orb diameter that tracks the viewport: a presence on desktop, a badge on a
 * phone. Height matters as much as width — a short laptop window would
 * otherwise push the controls below the fold.
 */
export function useOrbSize(max: number): number {
  const [size, setSize] = useState(max)

  useEffect(() => {
    const apply = () => {
      const w = window.innerWidth
      const h = window.innerHeight
      if (w < 640 || h < 620) setSize(Math.round(max * 0.62))
      else if (w < 1024) setSize(Math.round(max * 0.78))
      else setSize(Math.round(max * (h < 820 ? 0.86 : 1)))
    }
    apply()
    window.addEventListener('resize', apply)
    return () => window.removeEventListener('resize', apply)
  }, [max])

  return size
}
