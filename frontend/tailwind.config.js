/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0E0C0A',
        'bg-elevated': '#151210',
        surface: '#1C1916',
        'surface-high': '#242018',
        text: '#F2EDE5',
        muted: '#9C9288',
        subtle: '#5A5450',
        accent: '#D4A574',
        'accent-warm': '#C4925E',
        interrupt: '#B85A48',
        border: 'rgba(242,237,229,0.07)',
      },
      fontFamily: {
        brand: ['Syne', 'system-ui', 'sans-serif'],
        ui: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        md: '12px',
        lg: '20px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 4s linear infinite',
      },
    },
  },
  plugins: [],
}
