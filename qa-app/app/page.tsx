'use client'

import { useState, useCallback, useEffect } from 'react'
import StatsBar from './components/StatsBar'
import SamplePanel from './components/SamplePanel'

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [dark, setDark] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('qa-dark-mode')
    if (saved === 'true') setDark(true)
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    localStorage.setItem('qa-dark-mode', String(dark))
  }, [dark])

  const handleStatsChanged = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  return (
    <main className="app">
      <div className="app-header">
        <h1 className="app-title">QA Review</h1>
        <button className="btn-theme" onClick={() => setDark(d => !d)} title="Toggle dark mode">
          {dark ? '\u2600' : '\u263E'}
        </button>
      </div>
      <StatsBar refreshKey={refreshKey} />
      <div className="panels">
        <SamplePanel title="Suspicious Samples" type="suspicious" onStatsChanged={handleStatsChanged} />
        <SamplePanel title="Random Samples" type="random" onStatsChanged={handleStatsChanged} />
      </div>
    </main>
  )
}
