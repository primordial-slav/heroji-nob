'use client'

import { useEffect, useState, type ReactNode } from 'react'
import type { Soldier } from '@/app/lib/types'
import { ChevronLeftIcon, ChevronRightIcon } from './Icons'
import { SoldierMedals } from './Medal'
import { useLang, useT } from '@/app/i18n/LangContext'
import { unitName } from '@/app/i18n/units'
import { unitByName } from '@/app/lib/records'
import { FIRST_PAGE } from '@/app/lib/searchIndex'

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
   * The whole list's length while only its first page is in (a unit page before its list has loaded): counted
   * and paged as the whole list, and the other pages wait for the rest
   */
  total?: number
}

const PAGE_SIZES = [FIRST_PAGE, 100, 200]

export default function SoldierResults({ results, showUnit, onSelect, scrollTargetId, actions, total }: SoldierResultsProps) {
  const t = useT()
  const lang = useLang()
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(PAGE_SIZES[0])

  useEffect(() => setPage(1), [results])

  const count = total ?? results.length
  const partial = count > results.length
  const totalPages = Math.max(1, Math.ceil(count / perPage))
  const start = (page - 1) * perPage
  const shown = results.slice(start, start + perPage)

  const goTo = (p: number) => {
    setPage(p)
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
          {t.found(count)}
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
                disabled={partial}
                onChange={(e) => { setPerPage(Number(e.target.value)); setPage(1) }}
              >
                {PAGE_SIZES.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          )}
        </div>
      </div>

      <ul className="result-list">
        {shown.map((soldier) => (
          <li className="result" key={soldier.soldier_id}>
            <button type="button" className="result-button" onClick={() => onSelect(soldier)}>
              <span className="result-text">
                <span className="result-name"><SoldierName soldier={soldier} /></span>
                {soldier.additional_info && <span className="result-info">{soldier.additional_info}</span>}
                {showUnit && soldier.unit && (
                  <span className="result-unit">
                    {[soldier.unit, ...(soldier.also_units ?? [])].map((name) => {
                      const unit = unitByName(name)
                      return unit ? unitName(unit, lang) : name
                    }).join(' · ')}
                  </span>
                )}
              </span>
              <SoldierMedals soldier={soldier} look="gravira" />
            </button>
          </li>
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
                disabled={partial && p !== page}
                aria-current={p === page ? 'page' : undefined}
              >
                {p}
              </button>
            )
          )}
          <button className="page-button" onClick={() => goTo(page + 1)} disabled={page === totalPages || partial}>
            {t.results.next} <ChevronRightIcon />
          </button>
        </nav>
      )}
    </div>
  )
}
