'use client'

import { useEffect, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import { ChevronLeftIcon, ChevronRightIcon } from './Icons'
import { sqQuotes } from '@/app/lib/typography'

// "1 borac", "3 borca", "5 boraca", with the matching participle
export function countBorci(n: number) {
  const mod10 = n % 10
  const mod100 = n % 100
  const formatted = n.toLocaleString('sr-Latn')
  if (mod10 === 1 && mod100 !== 11) return { verb: 'Pronađen', text: `${formatted} borac` }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return { verb: 'Pronađena', text: `${formatted} borca` }
  return { verb: 'Pronađeno', text: `${formatted} boraca` }
}

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
}

const PAGE_SIZES = [50, 100, 200]

export default function SoldierResults({ results, showUnit, onSelect, scrollTargetId }: SoldierResultsProps) {
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(50)

  useEffect(() => setPage(1), [results])

  const totalPages = Math.max(1, Math.ceil(results.length / perPage))
  const start = (page - 1) * perPage
  const shown = results.slice(start, start + perPage)
  const count = countBorci(results.length)

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
          {count.verb} {count.text}
          {totalPages > 1 && <span> · strana {page} od {totalPages}</span>}
        </p>
        {results.length > PAGE_SIZES[0] && (
          <label className="per-page">
            Po strani
            <select
              id="per-page"
              value={perPage}
              onChange={(e) => { setPerPage(Number(e.target.value)); setPage(1) }}
            >
              {PAGE_SIZES.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
        )}
      </div>

      <ul className="result-list">
        {shown.map((soldier) => (
          <li className="result" key={soldier.soldier_id}>
            <button type="button" className="result-button" onClick={() => onSelect(soldier)}>
              <span className="result-name"><SoldierName soldier={soldier} /></span>
              {soldier.additional_info && <span className="result-info">{soldier.additional_info}</span>}
              {showUnit && soldier.unit && (
                <span className="result-unit">{[soldier.unit, ...(soldier.also_units ?? [])].map(sqQuotes).join(' · ')}</span>
              )}
            </button>
          </li>
        ))}
      </ul>

      {totalPages > 1 && (
        <nav className="pagination" aria-label="Strane rezultata">
          <button className="page-button" onClick={() => goTo(page - 1)} disabled={page === 1}>
            <ChevronLeftIcon /> Prethodna
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
            Sledeća <ChevronRightIcon />
          </button>
        </nav>
      )}
    </div>
  )
}
