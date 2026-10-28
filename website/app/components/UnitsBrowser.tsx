'use client'

import { useEffect, useState } from 'react'
import { units, type Unit } from '@/app/data/units'
import { formation } from '@/app/data/formation'
import { UNIT_KINDS, UNIT_LANDS, unitKind, unitLands, type UnitKind, type UnitLand } from '@/app/data/unitKinds'
import UnitsByYear, { isNoUnit } from '@/app/components/UnitsByYear'
import { SearchIcon } from '@/app/components/Icons'
import { normalizeForSearch } from '@/app/lib/diacritics'
import { useLang, useT, useUnitText } from '@/app/i18n/LangContext'

const yearOf = (unit: Unit) => formation[unit.id]?.date.slice(0, 4)
// The years the units were formed in, oldest first
const YEARS = [...new Set(units.map(yearOf).filter((y): y is string => Boolean(y)))].sort()
const UNIT_COUNT = units.filter((u) => !isNoUnit(u)).length
const fold = (text: string) => normalizeForSearch(text).toLowerCase()

interface Choice {
  year: string
  kind: UnitKind | ''
  land: UnitLand | ''
}

// The address keeps the choice, so it can be linked: ?godina=1942&vrsta=brigada&republika=hrvatska
const PARAMS: Record<keyof Choice, string> = { year: 'godina', kind: 'vrsta', land: 'republika' }

// The Jedinice page's list: every unit under the year it was formed, narrowed to a year, a kind (brigades, divisions,
// odredi, the rest), the republic it came from (data/unitKinds.ts) or by words of its name. Each row's counts are
// those the other choices leave. Borci drugih jedinica, no unit, stays out once a kind or a republic is chosen.
export default function UnitsBrowser() {
  const t = useT().unitsPage
  const lang = useLang()
  const unitText = useUnitText()
  const [choice, setChoice] = useState<Choice>({ year: '', kind: '', land: '' })
  const [query, setQuery] = useState('')

  const [addressRead, setAddressRead] = useState(false)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const year = params.get(PARAMS.year) ?? ''
    const kind = params.get(PARAMS.kind) ?? ''
    const land = params.get(PARAMS.land) ?? ''
    setChoice({
      year: YEARS.includes(year) ? year : '',
      kind: (UNIT_KINDS as readonly string[]).includes(kind) ? (kind as UnitKind) : '',
      land: (UNIT_LANDS as readonly string[]).includes(land) ? (land as UnitLand) : '',
    })
    setAddressRead(true)
  }, [])
  useEffect(() => {
    if (!addressRead) return
    const url = new URL(window.location.href)
    for (const key of Object.keys(PARAMS) as (keyof Choice)[]) {
      if (choice[key]) url.searchParams.set(PARAMS[key], choice[key])
      else url.searchParams.delete(PARAMS[key])
    }
    if (url.href !== window.location.href) window.history.replaceState(window.history.state, '', url)
  }, [addressRead, choice])

  // every word of the query in the name as the page shows it or as the books give it, without diacritics
  const words = fold(query).split(/\s+/).filter(Boolean)
  const named = (unit: Unit) => {
    const text = fold(`${unitText.name(unit)} ${unit.name}`)
    return words.every((w) => text.includes(w))
  }
  // a unit passes the choice, leaving one of its parts out (for that row's counts)
  const passes = (unit: Unit, c: Choice) =>
    (!c.year || yearOf(unit) === c.year) &&
    (!c.kind || (!isNoUnit(unit) && unitKind(unit.id) === c.kind)) &&
    (!c.land || (!isNoUnit(unit) && unitLands(unit.id).includes(c.land))) &&
    named(unit)
  const shown = units.filter((u) => passes(u, choice))
  const countWith = (part: Partial<Choice>) =>
    units.filter((u) => !isNoUnit(u) && passes(u, { ...choice, ...part })).length
  const set = (part: Partial<Choice>) => setChoice((c) => ({ ...c, ...part }))

  return (
    <>
      <p className="units-lead">{t.lead(UNIT_COUNT)}</p>
      <div className="units-controls">
        <div className="units-filters">
          <div className="units-filter">
            <span className="units-filter-label" aria-hidden="true">{t.years}</span>
            <div className="units-years" role="group" aria-label={t.years}>
              <button type="button" aria-pressed={!choice.year} onClick={() => set({ year: '' })}>{t.allYears}</button>
              {YEARS.map((y) => (
                <button key={y} type="button" aria-pressed={choice.year === y} onClick={() => set({ year: y })}>
                  {y} <span className="units-year-count">{countWith({ year: y })}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="units-filter">
            <span className="units-filter-label" aria-hidden="true">{t.kinds}</span>
            <div className="units-years" role="group" aria-label={t.kinds}>
              <button type="button" aria-pressed={!choice.kind} onClick={() => set({ kind: '' })}>{t.allYears}</button>
              {UNIT_KINDS.map((k) => (
                <button key={k} type="button" aria-pressed={choice.kind === k} onClick={() => set({ kind: k })}>
                  {t.kind[k]} <span className="units-year-count">{countWith({ kind: k })}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="units-filter">
            <span className="units-filter-label" aria-hidden="true">{t.lands}</span>
            <div className="units-years" role="group" aria-label={t.lands}>
              <button type="button" aria-pressed={!choice.land} onClick={() => set({ land: '' })}>{t.allYears}</button>
              {UNIT_LANDS.map((l) => (
                <button key={l} type="button" aria-pressed={choice.land === l} onClick={() => set({ land: l })}>
                  {t.land[l]} <span className="units-year-count">{countWith({ land: l })}</span>
                </button>
              ))}
            </div>
          </div>
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
          <h2>{query.trim() ? t.none(query.trim()) : t.noneChosen}</h2>
          <p>{query.trim() ? t.noneText : t.noneChosenText}</p>
        </div>
      )}
    </>
  )
}
