import { useTheme } from '../theme/ThemeContext'

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const night = theme === 'night'

  return (
    <button
      type="button"
      onClick={toggle}
      title={night ? 'Switch to gold studio' : 'Switch to night mode'}
      aria-label={night ? 'Switch to gold studio' : 'Switch to night mode'}
      className="theme-toggle"
    >
      {night ? (
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
          <circle cx="7" cy="7" r="2.4" fill="currentColor" />
          <path
            d="M7 1.2v1.4M7 11.4v1.4M1.2 7h1.4M11.4 7h1.4M2.8 2.8l1 1M10.2 10.2l1 1M2.8 11.2l1-1M10.2 3.8l1-1"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
          <path
            d="M12.2 8.4A5.4 5.4 0 0 1 5.6 1.8 5.5 5.5 0 1 0 12.2 8.4Z"
            fill="currentColor"
          />
        </svg>
      )}
    </button>
  )
}
