'use client'

import { useEffect, useState } from 'react'
import { useT } from '@/app/i18n/LangContext'

// The switch that stops the wartime portraits drifting in the home page's margins (PortraitRails.tsx), and starts
// them again: a pause icon framed like the theme's buttons, after them in the header, its words in the tooltip (a
// visitor's wish of 2026-11-19; the user chose the icon). The header is on every page, so globals.css shows it only
// where the margins hold the portraits. It marks the page (<html data-rails-still>), which stops them, and the browser
// remembers it for the next visit.

const KEY = 'rails-still'

export default function RailSwitch() {
  const t = useT().home
  const [still, setStill] = useState(false)
  useEffect(() => {
    try {
      setStill(localStorage.getItem(KEY) === '1')
    } catch {}
  }, [])
  useEffect(() => {
    document.documentElement.toggleAttribute('data-rails-still', still)
  }, [still])

  const toggle = () => {
    const next = !still
    setStill(next)
    try {
      if (next) localStorage.setItem(KEY, '1')
      else localStorage.removeItem(KEY)
    } catch {}
  }
  const label = still ? t.railsStart : t.railsStop

  return (
    <div className="theme-toggle rail-switch">
      <button type="button" className="theme-toggle-btn" onClick={toggle} title={label} aria-label={label}>
        <svg width="16" height="16" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
          {still ? <polygon points="6 4 19 12 6 20 6 4" /> : <><line x1="9" y1="5" x2="9" y2="19" /><line x1="15" y1="5" x2="15" y2="19" /></>}
        </svg>
      </button>
    </div>
  )
}
