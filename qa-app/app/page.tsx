'use client'

import { useState, useCallback } from 'react'
import StatsBar from './components/StatsBar'
import SamplePanel from './components/SamplePanel'

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0)

  const handleStatsChanged = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  return (
    <main className="app">
      <h1 className="app-title">QA Review</h1>
      <StatsBar refreshKey={refreshKey} />
      <div className="panels">
        <SamplePanel title="Suspicious Samples" type="suspicious" onStatsChanged={handleStatsChanged} />
        <SamplePanel title="Random Samples" type="random" onStatsChanged={handleStatsChanged} />
      </div>
    </main>
  )
}
