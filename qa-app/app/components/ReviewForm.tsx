'use client'

import { useState } from 'react'
import { ISSUE_TYPES, type IssueTypeKey } from '../lib/types'

interface ReviewFormProps {
  soldierId: string
  brigadeCode: number
  soldierData: string
  detection: 'suspicious' | 'random'
  flagsDetail: string
  onSaved: () => void
}

export default function ReviewForm({ soldierId, brigadeCode, soldierData, detection, flagsDetail, onSaved }: ReviewFormProps) {
  const [checks, setChecks] = useState<Record<string, boolean>>({})
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState<string | null>(null)

  const toggle = (key: string) => {
    setChecks(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const submit = async (status: 'issue' | 'correct') => {
    setSaving(true)
    try {
      await fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          soldier_id: soldierId,
          brigade_code: brigadeCode,
          status,
          ...Object.fromEntries(ISSUE_TYPES.map(t => [t.key, checks[t.key] ? 1 : 0])),
          description,
          detection,
          flags_detail: flagsDetail,
          soldier_data: soldierData,
        }),
      })
      setSaved(status)
      onSaved()
    } catch {
      alert('Failed to save review')
    } finally {
      setSaving(false)
    }
  }

  if (saved) {
    return (
      <div className={`review-saved ${saved === 'correct' ? 'review-saved-ok' : 'review-saved-issue'}`}>
        {saved === 'correct' ? 'Marked correct' : 'Issue reported'}
      </div>
    )
  }

  return (
    <div className="review-form">
      <div className="review-checks">
        {ISSUE_TYPES.map(t => (
          <label key={t.key} className="review-check-label">
            <input
              type="checkbox"
              checked={!!checks[t.key]}
              onChange={() => toggle(t.key)}
            />
            {t.label}
          </label>
        ))}
      </div>
      <textarea
        className="review-textarea"
        placeholder="Describe the issue..."
        value={description}
        onChange={e => setDescription(e.target.value)}
        rows={2}
      />
      <div className="review-actions">
        <button
          className="btn-issue"
          onClick={() => submit('issue')}
          disabled={saving}
        >
          Report Issue
        </button>
        <button
          className="btn-correct"
          onClick={() => submit('correct')}
          disabled={saving}
        >
          Mark Correct
        </button>
      </div>
    </div>
  )
}
