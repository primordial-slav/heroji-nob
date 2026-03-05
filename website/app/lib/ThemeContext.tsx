'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

type ThemeChoice = 'light' | 'dark' | 'system'

interface ThemeContextType {
  theme: ThemeChoice
  setTheme: (theme: ThemeChoice) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(choice: ThemeChoice) {
  const resolved = choice === 'system' ? getSystemTheme() : choice
  document.documentElement.setAttribute('data-theme', resolved)
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeChoice>('system')
  const [mounted, setMounted] = useState(false)

  // Read from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('theme') as ThemeChoice | null
    if (stored && ['light', 'dark', 'system'].includes(stored)) {
      setThemeState(stored)
      applyTheme(stored)
    } else {
      applyTheme('system')
    }
    setMounted(true)
  }, [])

  // Apply theme whenever it changes
  useEffect(() => {
    if (!mounted) return
    applyTheme(theme)
  }, [theme, mounted])

  // Listen for system preference changes when in 'system' mode
  useEffect(() => {
    if (!mounted) return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      if (theme === 'system') {
        applyTheme('system')
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme, mounted])

  const setTheme = (newTheme: ThemeChoice) => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
