'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { cardPath, citation, recordPath } from '@/app/lib/records'
import { CopyIcon, PrintIcon, QuoteIcon, ShareIcon } from './Icons'
import { copyText as copy, shareLink } from '@/app/lib/share'

type CopyState = 'idle' | 'copied' | 'failed'

// Share the record's own link, open its memorial card, or copy a line to quote it by
export default function RecordActions({ soldier, unit }: { soldier: Soldier; unit?: Unit }) {
  const [linkState, setLinkState] = useState<CopyState>('idle')
  const [showCitation, setShowCitation] = useState(false)
  const [citationState, setCitationState] = useState<CopyState>('idle')

  if (!unit) return null

  const link = typeof window === 'undefined' ? '' : new URL(recordPath(unit, soldier.soldier_id), window.location.origin).toString()
  const quote = `${citation(soldier)} ${link}`

  const share = async () => {
    const result = await shareLink(link, `${soldier.full_name} · Knjiga boraca`)
    if (result === 'copied' || result === 'failed') setLinkState(result)
  }

  return (
    <div className="record-actions">
      <div className="record-actions-row">
        <button type="button" className="record-action" onClick={share}>
          <ShareIcon size={16} /> Podeli zapis
        </button>
        <Link className="record-action" href={cardPath(unit, soldier.soldier_id)}>
          <PrintIcon size={16} /> Spomen-kartica
        </Link>
        <button
          type="button"
          className="record-action"
          aria-expanded={showCitation}
          onClick={() => setShowCitation((v) => !v)}
        >
          <QuoteIcon size={16} /> Citiraj
        </button>
        {linkState === 'copied' && <span className="record-action-status" role="status">Link je kopiran.</span>}
      </div>

      {linkState === 'failed' && (
        <p className="record-copy-fallback">
          <label htmlFor="record-link">Link do zapisa</label>
          <input id="record-link" readOnly value={link} onFocus={(e) => e.currentTarget.select()} />
        </p>
      )}

      {showCitation && (
        <div className="record-citation">
          <p>{quote}</p>
          <button
            type="button"
            className="record-action"
            onClick={async () => setCitationState((await copy(quote)) ? 'copied' : 'failed')}
          >
            <CopyIcon size={16} /> {citationState === 'copied' ? 'Kopirano' : 'Kopiraj'}
          </button>
        </div>
      )}
    </div>
  )
}
