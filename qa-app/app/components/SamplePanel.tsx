'use client'

import { useState, useCallback } from 'react'
import type { SoldierSample } from '../lib/types'
import SampleCard from './SampleCard'

interface SamplePanelProps {
  title: string
  type: 'suspicious' | 'random'
  onStatsChanged: () => void
}

export default function SamplePanel({ title, type, onStatsChanged }: SamplePanelProps) {
  const [samples, setSamples] = useState<SoldierSample[]>([])
  const [count, setCount] = useState(10)
  const [loading, setLoading] = useState(false)
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  const fetchSamples = useCallback(async (n: number) => {
    setLoading(true)
    setDismissed(new Set())
    try {
      const res = await fetch(`/api/samples?type=${type}&count=${n}`)
      const data = await res.json()
      setSamples(data.samples)
    } catch {
      alert('Failed to load samples')
    } finally {
      setLoading(false)
    }
  }, [type])

  const handleCountClick = (n: number) => {
    setCount(n)
    fetchSamples(n)
  }

  const handleRefresh = () => fetchSamples(count)

  const handleDismiss = (soldierId: string) => {
    setDismissed(prev => new Set(prev).add(soldierId))
    onStatsChanged()
  }

  const visibleSamples = samples.filter(s => !dismissed.has(s.soldier.soldier_id))

  return (
    <div className="sample-panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <div className="panel-controls">
          {[5, 10, 20].map(n => (
            <button
              key={n}
              className={`btn-count ${count === n && samples.length > 0 ? 'active' : ''}`}
              onClick={() => handleCountClick(n)}
            >
              {n}
            </button>
          ))}
          <button className="btn-refresh" onClick={handleRefresh} disabled={loading}>
            &#8635;
          </button>
        </div>
      </div>
      <div className="panel-body">
        {loading && <div className="panel-loading">Loading samples...</div>}
        {!loading && samples.length === 0 && (
          <div className="panel-empty">Click a number to load samples</div>
        )}
        {visibleSamples.map(sample => (
          <SampleCard
            key={sample.soldier.soldier_id}
            sample={sample}
            detection={type}
            onDismiss={handleDismiss}
            onReviewed={onStatsChanged}
          />
        ))}
        {!loading && samples.length > 0 && visibleSamples.length === 0 && (
          <div className="panel-empty">All samples reviewed. Click refresh for more.</div>
        )}
      </div>
    </div>
  )
}
