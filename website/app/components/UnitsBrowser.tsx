'use client'

import { useEffect, useState } from 'react'
import { units, type Unit } from '@/app/data/units'
import { formation } from '@/app/data/formation'
import UnitsByYear, { isNoUnit } from '@/app/components/UnitsByYear'
import { SearchIcon } from '@/app/components/Icons'
import { normalizeForSearch } from '@/app/lib/diacritics'
import { unitName } from '@/app/i18n/units'
import { useLang, useT } from '@/app/i18n/LangContext'

const yearOf = (unit: Unit) => formation[unit.id]?.date.slice(0, 4)
// The years the units were formed in, oldest first
const YEARS = [...new Set(units.map(yearOf).filter((y): y is string => Boolean(y)))].sort()
const UNIT_COUNT = units.filter((u) => !isNoUnit(u)).length
const fold = (text: string) => normalizeForSearch(text).toLowerCase()

// The Jedinice page's list: every unit under the year it was formed, narrowed to one year or by words of its name.
// ?godina=1942 opens it at a year and keeps the year in the address, so it can be linked.
export default function UnitsBrowser() {
  const t = useT().unitsPage
  const lang = useLang()
  const [year, setYear] = useState('')
  const [query, setQuery] = useState('')

  const [addressRead, setAddressRead] = useState(false)
  useEffect(() => {
    const linked = new URLSearchParams(window.location.search).get('godina')
    if (linked && YEARS.includes(linked)) setYear(linked)
    setAddressRead(true)
  }, [])
  useEffect(() => {
    if (!addressRead) return
    const url = new URL(window.location.href)
    if (year) url.searchParams.set('godina', year)
    else url.searchParams.delete('godina')
    if (url.href !== window.location.href) window.history.replaceState(window.history.state, '', url)
  }, [addressRead, year])

  // every word of the query in the name as the page shows it or as the books give it, without diacritics
  const words = fold(query).split(/\s+/).filter(Boolean)
  const named = (unit: Unit) => {
    const text = fold(`${unitName(unit, lang)} ${unit.name}`)
    return words.every((w) => text.includes(w))
  }
  const shown = units.filter((u) => (!year || yearOf(u) === year) && named(u))

  return (
    <>
      <p className="units-lead">{t.lead(UNIT_COUNT)}</p>
      <div className="units-controls">
        <div className="units-years" role="group" aria-label={t.years}>
          <button type="button" aria-pressed={!year} onClick={() => setYear('')}>{t.allYears}</button>
          {YEARS.map((y) => (
            <button key={y} type="button" aria-pressed={year === y} onClick={() => setYear(y)}>
              {y} <span className="units-year-count">{units.filter((u) => yearOf(u) === y).length}</span>
            </button>
          ))}
        </div>
        <div className="units-find">
          <label htmlFor="units-find" className="visually-hidden">{t.find}</label>
          <span className="search-icon"><SearchIcon size={18} /></span>
          <input
            id="units-find"
            type="search"
            className="search-input"
            placeholder={t.find}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            maxLength={100}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
      </div>
      {shown.length > 0 ? (
        <UnitsByYear units={shown} />
      ) : (
        <div className="empty">
          <h2>{t.none(query.trim())}</h2>
          <p>{t.noneText}</p>
        </div>
      )}
    </>
  )
}
