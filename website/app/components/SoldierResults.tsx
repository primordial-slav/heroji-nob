'use client'

import { Fragment, useEffect, useState, type ReactNode } from 'react'
import type { Soldier } from '@/app/lib/types'
import { ChevronLeftIcon, ChevronRightIcon } from './Icons'
import { SoldierMedals } from './Medal'
import { useLang, useT, useUnitText } from '@/app/i18n/LangContext'
import { formatNumber } from '@/app/i18n/format'
import { unitByName } from '@/app/lib/records'
import { PAGE_SIZES } from '@/app/lib/searchIndex'

// Surname first, as the books print it; the surname carries the weight
export function SoldierName({ soldier }: { soldier: Soldier }) {
  const rest = [soldier.middle_name, soldier.first_name].filter(Boolean).join(' ')
  return (
    <>
      <b>{soldier.last_name}</b>
      {rest && ` ${rest}`}
    </>
  )
}

interface SoldierResultsProps {
  results: Soldier[]
  showUnit?: boolean
  onSelect: (soldier: Soldier) => void
  scrollTargetId: string
  /** Shown beside the count, e.g. sharing the search */
  actions?: ReactNode
  /**
   * A list the server pages (useServerSearch): `results` is only the page shown, and this says where it is in the
   * whole list; a change of page or of page size goes to `onPage`
   */
  paged?: { count: number; firstNear: number; page: number; perPage: number; onPage: (page: number, perPage: number) => void }
}

export default function SoldierResults({ results, showUnit, onSelect, scrollTargetId, actions, paged }: SoldierResultsProps) {
  const t = useT()
  const lang = useLang()
  const unitText = useUnitText()
  const [ownPage, setOwnPage] = useState(1)
  const [ownPerPage, setOwnPerPage] = useState(PAGE_SIZES[0])

  useEffect(() => setOwnPage(1), [results])

  const page = paged?.page ?? ownPage
  const perPage = paged?.perPage ?? ownPerPage
  const count = paged?.count ?? results.length
  // Where the similar results start, -1 if there are none
  const firstNear = paged ? paged.firstNear : -1
  const totalPages = Math.max(1, Math.ceil(count / perPage))
  const start = (page - 1) * perPage
  const shown = paged ? results : results.slice(start, start + perPage)

  const goTo = (p: number) => {
    if (paged) paged.onPage(p, perPage)
    else setOwnPage(p)
    document.getElementById(scrollTargetId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // First, last, and the pages around the current one
  const pages: (number | 'gap')[] = []
  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || Math.abs(p - page) <= 1) pages.push(p)
    else if (pages[pages.length - 1] !== 'gap') pages.push('gap')
  }

  return (
    <div>
      <div className="results-bar">
        <p className="results-count" aria-live="polite">
          {firstNear < 0 ? t.found(count) : firstNear === 0 ? t.results.noExact : t.found(firstNear)}
          {firstNear >= 0 && <span> · {t.results.similar(count - firstNear, firstNear > 0)}</span>}
          {totalPages > 1 && <span> · {t.results.pageOf(page, totalPages)}</span>}
        </p>
        <div className="results-tools">
          {actions}
          {count > PAGE_SIZES[0] && (
            <label className="per-page">
              {t.results.perPage}
              <select
                id="per-page"
                value={perPage}
                onChange={(e) => {
                  const n = Number(e.target.value)
                  if (paged) paged.onPage(1, n)
                  else { setOwnPerPage(n); setOwnPage(1) }
                }}
              >
                {PAGE_SIZES.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          )}
        </div>
      </div>

      <ul className="result-list">
        {shown.map((soldier, k) => (
          <Fragment key={soldier.soldier_id}>
          {start + k === firstNear && (
            <li className="result-similar">
              <span className="result-similar-title">
                {t.results.similarTitle} <span className="result-similar-count">· {formatNumber(lang, count - firstNear)}</span>
              </span>
            </li>
          )}
          <li className="result">
            <button type="button" className="result-button" onClick={() => onSelect(soldier)}>
              <span className="result-text">
                <span className="result-name"><SoldierName soldier={soldier} /></span>
                {soldier.additional_info && <span className="result-info">{soldier.additional_info}</span>}
                {showUnit && soldier.unit && (
                  <span className="result-unit">
                    {[soldier.unit, ...(soldier.also_units ?? [])].map((name) => {
                      const unit = unitByName(name)
                      return unit ? unitText.name(unit) : name
                    }).join(' · ')}
                  </span>
                )}
              </span>
              <SoldierMedals soldier={soldier} look="gravira" />
            </button>
          </li>
          </Fragment>
        ))}
      </ul>

      {totalPages > 1 && (
        <nav className="pagination" aria-label={t.results.pages}>
          <button className="page-button" onClick={() => goTo(page - 1)} disabled={page === 1}>
            <ChevronLeftIcon /> {t.results.previous}
          </button>
          {pages.map((p, i) =>
            p === 'gap' ? (
              <span key={`gap-${i}`} className="page-gap">…</span>
            ) : (
              <button
                key={p}
                className={p === page ? 'page-button active' : 'page-button'}
                onClick={() => goTo(p)}
                aria-current={p === page ? 'page' : undefined}
              >
                {p}
              </button>
            )
          )}
          <button className="page-button" onClick={() => goTo(page + 1)} disabled={page === totalPages}>
            {t.results.next} <ChevronRightIcon />
          </button>
        </nav>
      )}
    </div>
  )
}
