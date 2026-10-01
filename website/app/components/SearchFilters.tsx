'use client'

import { useEffect, useState } from 'react'
import { units } from '@/app/data/units'
import { formation, formationKey } from '@/app/data/formation'
import { FATES, NO_FILTERS, RANGES, filterCount, type SearchFilters as Filters } from '@/app/lib/searchFilters'
import { shareLink } from '@/app/lib/share'
import { useLang, useT } from '@/app/i18n/LangContext'
import { unitName } from '@/app/i18n/units'
import { FilterIcon, ShareIcon } from './Icons'

// The units in the order the home page lists them: by formation date, undated last
const UNIT_OPTIONS = [...units].sort((a, b) =>
  (formation[a.id] ? formationKey(formation[a.id].date) : Infinity) - (formation[b.id] ? formationKey(formation[b.id].date) : Infinity))

/** The button at the end of a search field that opens the filters, with how many are set */
export function FilterToggle({ open, count, controls, onClick }: {
  open: boolean
  count: number
  controls: string
  onClick: () => void
}) {
  const t = useT().filters
  return (
    <button type="button" className="filter-toggle" aria-expanded={open} aria-controls={controls} onClick={onClick}>
      <FilterIcon size={16} />
      {t.toggle}
      {count > 0 && <span className="filter-count" aria-label={t.active(count)}>{count}</span>}
    </button>
  )
}

interface SearchFiltersProps {
  id: string
  filters: Filters
  onChange: (filters: Filters) => void
  /** The unit choice, on the home page only */
  withUnit?: boolean
}

export default function SearchFilters({ id, filters, onChange, withUnit = false }: SearchFiltersProps) {
  const t = useT().filters
  const lang = useLang()
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch })

  return (
    <div className="filters" id={id}>
      <div className="filter filter-year">
        <label htmlFor={`${id}-year`}>{t.birthYear}</label>
        <div className="filter-pair">
          <input
            id={`${id}-year`}
            type="text"
            inputMode="numeric"
            maxLength={4}
            placeholder="1920"
            value={filters.year}
            onChange={(e) => set({ year: e.target.value.replace(/\D/g, '') })}
            autoComplete="off"
          />
          <select
            aria-label={t.range}
            value={filters.range}
            onChange={(e) => set({ range: Number(e.target.value) })}
          >
            {RANGES.map((r) => <option key={r} value={r}>{r ? `± ${r}` : t.exact}</option>)}
          </select>
        </div>
      </div>

      <div className="filter filter-place">
        <label htmlFor={`${id}-place`}>{t.place}</label>
        <input
          id={`${id}-place`}
          type="text"
          placeholder={t.placeHint}
          value={filters.place}
          onChange={(e) => set({ place: e.target.value })}
          autoComplete="off"
          spellCheck={false}
        />
      </div>

      {withUnit && (
        <div className="filter filter-unit">
          <label htmlFor={`${id}-unit`}>{t.unit}</label>
          <select id={`${id}-unit`} value={filters.unit} onChange={(e) => set({ unit: e.target.value })}>
            <option value="">{t.allUnits}</option>
            {UNIT_OPTIONS.map((u) => <option key={u.id} value={u.id}>{unitName(u, lang)}</option>)}
          </select>
        </div>
      )}

      <div className="filter filter-fate">
        <label htmlFor={`${id}-fate`}>{t.fate}</label>
        <select id={`${id}-fate`} value={filters.fate} onChange={(e) => set({ fate: e.target.value as Filters['fate'] })}>
          <option value="">{t.allFates}</option>
          {FATES.map((f) => <option key={f.value} value={f.value}>{t.fates[f.value]}</option>)}
        </select>
      </div>

      <div className="filter-end">
        <label className="filter-check">
          <input type="checkbox" checked={filters.wholeWords} onChange={(e) => set({ wholeWords: e.target.checked })} />
          {t.wholeWords}
        </label>
        {filterCount(filters, withUnit) > 0 && (
          <button type="button" className="filter-clear" onClick={() => onChange(NO_FILTERS)}>
            {t.clear}
          </button>
        )}
      </div>
    </div>
  )
}

/** Shares the page address, which holds the search and its filters */
export function ShareSearch() {
  const t = useT().share
  const [state, setState] = useState<'idle' | 'copied' | 'failed'>('idle')

  useEffect(() => {
    if (state === 'idle') return
    const timer = setTimeout(() => setState('idle'), 4000)
    return () => clearTimeout(timer)
  }, [state])

  const share = async () => {
    const result = await shareLink(window.location.href, `${document.title}`)
    if (result === 'copied' || result === 'failed') setState(result)
  }

  return (
    <button type="button" className="share-search" onClick={share} aria-live="polite">
      <ShareIcon size={15} />
      {state === 'copied' ? t.copied : state === 'failed' ? t.failed : t.search}
    </button>
  )
}
