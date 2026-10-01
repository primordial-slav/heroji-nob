'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { cardPath, citation, recordPath } from '@/app/lib/records'
import { CopyIcon, PrintIcon, QuoteIcon, ShareIcon } from './Icons'
import { copyText as copy, shareLink } from '@/app/lib/share'
import { useLang, useT } from '@/app/i18n/LangContext'

type CopyState = 'idle' | 'copied' | 'failed'

// Share the record's own link, open its memorial card, or copy a line to quote it by
export default function RecordActions({ soldier, unit }: { soldier: Soldier; unit?: Unit }) {
  const lang = useLang()
  const t = useT()
  const [linkState, setLinkState] = useState<CopyState>('idle')
  const [showCitation, setShowCitation] = useState(false)
  const [citationState, setCitationState] = useState<CopyState>('idle')

  if (!unit) return null

  const link = typeof window === 'undefined' ? '' : new URL(recordPath(unit, soldier.soldier_id, lang), window.location.origin).toString()
  const quote = `${citation(soldier, lang)} ${link}`

  const share = async () => {
    const result = await shareLink(link, `${soldier.full_name} · ${t.site.name}`)
    if (result === 'copied' || result === 'failed') setLinkState(result)
  }

  return (
    <div className="record-actions">
      <div className="record-actions-row">
        <button type="button" className="record-action" onClick={share}>
          <ShareIcon size={16} /> {t.actions.share}
        </button>
        <Link className="record-action" href={cardPath(unit, soldier.soldier_id, lang)}>
          <PrintIcon size={16} /> {t.actions.card}
        </Link>
        <button
          type="button"
          className="record-action"
          aria-expanded={showCitation}
          onClick={() => setShowCitation((v) => !v)}
        >
          <QuoteIcon size={16} /> {t.actions.cite}
        </button>
        {linkState === 'copied' && <span className="record-action-status" role="status">{t.actions.linkCopied}</span>}
      </div>

      {linkState === 'failed' && (
        <p className="record-copy-fallback">
          <label htmlFor="record-link">{t.actions.link}</label>
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
            <CopyIcon size={16} /> {citationState === 'copied' ? t.actions.copied : t.actions.copy}
          </button>
        </div>
      )}
    </div>
  )
}
