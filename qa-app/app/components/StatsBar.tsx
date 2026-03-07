'use client'

import { useState, useEffect, useCallback } from 'react'
import type { ReviewStats } from '../lib/types'

interface StatsBarProps {
  refreshKey: number
}

export default function StatsBar({ refreshKey }: StatsBarProps) {
  const [stats, setStats] = useState<ReviewStats | null>(null)

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/stats')
      const data = await res.json()
      setStats(data)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    fetchStats()
  }, [fetchStats, refreshKey])

  if (!stats) return null

  return (
    <div className="stats-bar">
      <div className="stat">
        <span className="stat-value">{stats.total_soldiers.toLocaleString()}</span>
        <span className="stat-label">Total soldiers</span>
      </div>
      <div className="stat">
        <span className="stat-value">{stats.total_reviewed}</span>
        <span className="stat-label">Reviewed</span>
      </div>
      <div className="stat stat-issues">
        <span className="stat-value">{stats.issues}</span>
        <span className="stat-label">Issues</span>
      </div>
      <div className="stat stat-correct">
        <span className="stat-value">{stats.correct}</span>
        <span className="stat-label">Correct</span>
      </div>
      <div className="stat stat-dismissed">
        <span className="stat-value">{stats.dismissed}</span>
        <span className="stat-label">Dismissed</span>
      </div>
    </div>
  )
}
