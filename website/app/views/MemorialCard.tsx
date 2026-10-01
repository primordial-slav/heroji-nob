'use client'

import { useCallback, useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { photoPosition } from '@/app/data/photoFocus'
import {
  RECORD_PARAM, citation, entriesOf, findRecord, hasPage, lifeYears, recordDetails, recordPath, sourceTitle,
} from '@/app/lib/records'
import { portraitFor } from '@/app/data/portraits'
import SoldierPortrait from '@/app/components/SoldierPortrait'
import { SoldierName } from '@/app/components/SoldierResults'
import { SoldierMedals, honoursLine } from '@/app/components/Medal'
import { ArrowLeftIcon, PrintIcon } from '@/app/components/Icons'
import { useLang, useT } from '@/app/i18n/LangContext'
import { unitName } from '@/app/i18n/units'

// PDF.js only runs in the browser
const EntryCrop = dynamic(() => import('@/app/components/EntryCrop'), { ssr: false })

type State =
  | { status: 'loading' }
  | { status: 'missing' }
  | { status: 'failed' }
  | { status: 'ready'; unit: Unit; soldier: Soldier }

// A printable card for one soldier: /kartica?jedinica=<unit>&borac=<soldier id> (/en/kartica?… in English)
export default function MemorialCard() {
  const lang = useLang()
  const t = useT()
  const [state, setState] = useState<State>({ status: 'loading' })
  const [settledCrops, setSettledCrops] = useState(0)
  const onCropSettled = useCallback(() => setSettledCrops((n) => n + 1), [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const unit = units.find((u) => u.id === params.get('jedinica'))
    const id = params.get(RECORD_PARAM)
    if (!unit || !id) {
      setState({ status: 'missing' })
      return
    }
    fetch(unit.dataFile)
      .then((res) => res.json())
      .then((list: Soldier[]) => {
        const soldier = findRecord(list, id)
        setState(soldier ? { status: 'ready', unit, soldier } : { status: 'missing' })
      })
      .catch(() => setState({ status: 'failed' }))
  }, [])

  if (state.status === 'loading') {
    return <div className="container card-page"><p className="card-note">{t.card.loading}</p></div>
  }
  if (state.status !== 'ready') {
    return (
      <div className="container card-page">
        <div className="empty">
          <h2>{state.status === 'missing' ? t.card.missingTitle : t.card.failedTitle}</h2>
          <p>
            {state.status === 'missing' ? t.card.missingText : t.card.failedText}
          </p>
        </div>
      </div>
    )
  }

  const { unit, soldier } = state
  const pages = entriesOf(soldier).filter(hasPage)
  const ready = settledCrops >= pages.length
  const years = lifeYears(soldier)
  const details = recordDetails(soldier, t)
  const honours = honoursLine(soldier, t)
  const hasPhoto = !unit.image.includes('/pdf-thumbs/')
  const link = new URL(recordPath(unit, soldier.soldier_id, lang), window.location.origin).toString()
  // The soldier's photograph (from the family, a book or the gallery); without one, a stand-in outline
  const portrait = portraitFor(soldier)

  return (
    <div className="container card-page">
      <div className="card-toolbar">
        <Link href={recordPath(unit, soldier.soldier_id, lang)} className="back-link">
          <ArrowLeftIcon size={16} /> {t.card.back}
        </Link>
        <button type="button" className="btn btn-primary" onClick={() => window.print()} disabled={!ready}>
          <PrintIcon size={16} /> {ready ? t.card.print : t.card.preparing}
        </button>
      </div>

      <article className="memorial-card">
        {hasPhoto && (
          <div className="memorial-photo">
            <img src={unit.image} alt="" style={{ objectPosition: photoPosition(unit.id) }} />
          </div>
        )}
        <div className="memorial-body">
          <div className="memorial-head has-portrait">
            <SoldierPortrait soldier={soldier} unitId={unit.id} portrait={portrait} className="memorial-portrait" />
            <div>
              <p className="memorial-unit">{unitName(unit, lang)}</p>
              <h1 className="memorial-name"><SoldierName soldier={soldier} /></h1>
              {years && <p className="memorial-years">{years}</p>}
              {honours && <p className="memorial-honours">{honours}</p>}
              {portrait && <p className="memorial-portrait-credit">{t.record.photo} {t.record.photoCredit(portrait.credit)}</p>}
            </div>
            <SoldierMedals soldier={soldier} look="foto" className="memorial-medals" />
          </div>

          {details.length > 0 && (
            <dl className="memorial-details">
              {details.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          )}

          <section className="memorial-entries">
            <h2>{t.card.entry}</h2>
            {pages.map((entry, i) => (
              <figure key={i}>
                <EntryCrop entry={entry} onSettled={onCropSettled} />
                <figcaption>{sourceTitle(entry)}, {t.record.page(entry.pdf_page!)}</figcaption>
              </figure>
            ))}
            {pages.length === 0 && (
              <figure>
                <blockquote className="memorial-text">{soldier.additional_info}</blockquote>
                <figcaption>{sourceTitle(soldier)}, {t.card.webText}</figcaption>
              </figure>
            )}
          </section>

          <footer className="memorial-footer">
            <p>{citation(soldier, lang)}</p>
            <p className="memorial-link">{link}</p>
          </footer>
        </div>
      </article>
    </div>
  )
}
