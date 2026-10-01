'use client'

import { useCallback, useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import {
  RECORD_PARAM, citation, entriesOf, findRecord, hasPage, lifeYears, recordDetails, recordPath, sourceTitle,
} from '@/app/lib/records'
import { sqQuotes } from '@/app/lib/typography'
import { contributionsFor } from '@/app/data/family'
import { SoldierName } from '@/app/components/SoldierResults'
import { ArrowLeftIcon, PrintIcon } from '@/app/components/Icons'

// PDF.js only runs in the browser
const EntryCrop = dynamic(() => import('@/app/components/EntryCrop'), { ssr: false })

type State =
  | { status: 'loading' }
  | { status: 'missing' }
  | { status: 'failed' }
  | { status: 'ready'; unit: Unit; soldier: Soldier }

// A printable card for one soldier: /kartica?jedinica=<unit>&borac=<soldier id>
export default function MemorialCard() {
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
    return <div className="container card-page"><p className="card-note">Učitava se zapis…</p></div>
  }
  if (state.status !== 'ready') {
    return (
      <div className="container card-page">
        <div className="empty">
          <h2>{state.status === 'missing' ? 'Ovaj zapis ne postoji' : 'Zapis se nije učitao'}</h2>
          <p>
            {state.status === 'missing'
              ? 'Link je možda nepotpun. Potražite borca na početnoj stranici.'
              : 'Proverite vezu sa internetom i osvežite stranicu.'}
          </p>
        </div>
      </div>
    )
  }

  const { unit, soldier } = state
  const pages = entriesOf(soldier).filter(hasPage)
  const ready = settledCrops >= pages.length
  const years = lifeYears(soldier)
  const details = recordDetails(soldier)
  const hasPhoto = !unit.image.includes('/pdf-thumbs/')
  const link = new URL(recordPath(unit, soldier.soldier_id), window.location.origin).toString()
  // A photograph the family sent and allowed to be published
  const portrait = contributionsFor(soldier.soldier_id, (soldier.other_sources ?? []).map((o) => o.soldier_id))
    .find((c) => c.photo)

  return (
    <div className="container card-page">
      <div className="card-toolbar">
        <Link href={recordPath(unit, soldier.soldier_id)} className="back-link">
          <ArrowLeftIcon size={16} /> Nazad na zapis
        </Link>
        <button type="button" className="btn btn-primary" onClick={() => window.print()} disabled={!ready}>
          <PrintIcon size={16} /> {ready ? 'Odštampaj ili sačuvaj kao PDF' : 'Priprema se isečak iz knjige…'}
        </button>
      </div>

      <article className="memorial-card">
        {hasPhoto && (
          <div className="memorial-photo">
            <img src={unit.image} alt="" />
          </div>
        )}
        <div className="memorial-body">
          <div className={portrait ? 'memorial-head has-portrait' : 'memorial-head'}>
            <div>
              <p className="memorial-unit">{sqQuotes(unit.name)}</p>
              <h1 className="memorial-name"><SoldierName soldier={soldier} /></h1>
              {years && <p className="memorial-years">{years}</p>}
            </div>
            {portrait && (
              <figure className="memorial-portrait">
                <img src={`/porodica/${portrait.photo}`} alt={portrait.photoCaption ?? ''} />
                <figcaption>Fotografija: {portrait.from}</figcaption>
              </figure>
            )}
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
            <h2>Zapis u knjizi</h2>
            {pages.map((entry, i) => (
              <figure key={i}>
                <EntryCrop entry={entry} onSettled={onCropSettled} />
                <figcaption>{sourceTitle(entry)}, str. {entry.pdf_page}</figcaption>
              </figure>
            ))}
            {pages.length === 0 && (
              <figure>
                <blockquote className="memorial-text">{soldier.additional_info}</blockquote>
                <figcaption>{sourceTitle(soldier)}, tekst objavljen na znaci.org</figcaption>
              </figure>
            )}
          </section>

          <footer className="memorial-footer">
            <p>{citation(soldier)}</p>
            <p className="memorial-link">{link}</p>
          </footer>
        </div>
      </article>
    </div>
  )
}
