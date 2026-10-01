'use client'

import { useTheme } from '@/app/lib/ThemeContext'
import { useT } from '@/app/i18n/LangContext'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const t = useT().theme

  return (
    <div className="theme-toggle" role="group" aria-label={t.label}>
      <button
        className={`theme-toggle-btn ${theme === 'light' ? 'active' : ''}`}
        onClick={() => setTheme('light')} aria-pressed={theme === 'light'}
        title={t.light}
        aria-label={t.light}
      >
        <svg width="16" height="16" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      </button>
      <button
        className={`theme-toggle-btn ${theme === 'dark' ? 'active' : ''}`}
        onClick={() => setTheme('dark')} aria-pressed={theme === 'dark'}
        title={t.dark}
        aria-label={t.dark}
      >
        <svg width="16" height="16" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>
      <button
        className={`theme-toggle-btn ${theme === 'system' ? 'active' : ''}`}
        onClick={() => setTheme('system')} aria-pressed={theme === 'system'}
        title={t.system}
        aria-label={t.system}
      >
        <svg width="16" height="16" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
      </button>
    </div>
  )
}
