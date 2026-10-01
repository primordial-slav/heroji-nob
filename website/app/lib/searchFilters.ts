import { units } from '@/app/data/units'
import { normalizeForSearch } from './diacritics'
import type { Soldier } from './types'

// Narrowing a search down to one soldier among many with the same name: birth year, a place in the entry,
// the unit and how he died. The search and its filters live in the page address, so a search can be sent
// as a link: ?q=Petrović&mesto=Gračac&godina=1920&raspon=2&jedinica=prva-licka-brigada&sudbina=poginuli&cele=1

export type Fate = 'poginuli' | 'umrli' | 'nestali'

export interface SearchFilters {
  /** Birth year as typed; only a four-digit year filters */
  year: string
  /** How many years either side of `year` still count */
  range: number
  /** A village or town anywhere in the entry */
  place: string
  /** A unit's id (home page only) */
  unit: string
  fate: Fate | ''
  /** Every query word must be a whole word of the name or the entry */
  wholeWords: boolean
}

export const NO_FILTERS: SearchFilters = { year: '', range: 0, place: '', unit: '', fate: '', wholeWords: false }

export const RANGES = [0, 2, 5]

// death_type as scripts/extract_structured_fields.py reads it from the entry; the labels are t.filters.fates
export const FATES: { value: Fate; types: string[] }[] = [
  { value: 'poginuli', types: ['poginuo', 'poginula', 'streljan', 'streljana', 'ubijen', 'ubijena'] },
  { value: 'umrli', types: ['umro', 'umrla'] },
  { value: 'nestali', types: ['nestao', 'nestala'] },
]

const PARAM = {
  query: 'q', year: 'godina', range: 'raspon', place: 'mesto', unit: 'jedinica', fate: 'sudbina', wholeWords: 'cele',
} as const

const birthYear = (year: string) => (/^\d{4}$/.test(year.trim()) ? Number(year.trim()) : null)

/** Filters that narrow the list by themselves; whole words only changes how the query matches */
export function narrows(filters: SearchFilters, withUnit = true): boolean {
  return birthYear(filters.year) !== null || filters.place.trim() !== '' || (withUnit && filters.unit !== '') || filters.fate !== ''
}

/** How many filters are set, for the count on the Filteri button */
export function filterCount(filters: SearchFilters, withUnit = true): number {
  return [birthYear(filters.year) !== null, filters.place.trim() !== '', withUnit && filters.unit !== '', filters.fate !== '', filters.wholeWords]
    .filter(Boolean).length
}

// " gracac sumarina donji lapac ": an entry's words, normalized, between spaces
const entryText = new WeakMap<Soldier, string>()
function entryWords(soldier: Soldier): string {
  let text = entryText.get(soldier)
  if (text === undefined) {
    const parts = [soldier.additional_info, soldier.death_place, ...(soldier.other_sources ?? []).map((o) => o.additional_info)]
    text = ` ${words(parts.filter(Boolean).join(' '))} `
    entryText.set(soldier, text)
  }
  return text
}

const words = (text: string) => normalizeForSearch(text).toLowerCase().replace(/[^a-z0-9À-ɏ]+/g, ' ').trim()

export function applyFilters(list: Soldier[], filters: SearchFilters, withUnit = true): Soldier[] {
  const year = birthYear(filters.year)
  const unitName = withUnit && filters.unit ? units.find((u) => u.id === filters.unit)?.name : undefined
  const fate = FATES.find((f) => f.value === filters.fate)
  // Matched at the start of a word of the entry, so "Gračac" also finds "u Gračacu"
  const place = words(filters.place)
  if (year === null && !unitName && !fate && !place) return list

  return list.filter((soldier) => {
    if (unitName && soldier.unit !== unitName && !soldier.also_units?.includes(unitName)) return false
    if (fate && !fate.types.includes(soldier.death_type ?? '')) return false
    if (year !== null) {
      const born = parseInt(soldier.birth_year ?? '', 10)
      if (Number.isNaN(born) || Math.abs(born - year) > filters.range) return false
    }
    if (place && !entryWords(soldier).includes(` ${place}`)) return false
    return true
  })
}

/** The search and filters from a page address */
export function readSearch(params: URLSearchParams): { query: string; filters: SearchFilters } {
  const range = Number(params.get(PARAM.range))
  const fate = params.get(PARAM.fate) ?? ''
  return {
    query: params.get(PARAM.query) ?? '',
    filters: {
      year: params.get(PARAM.year) ?? '',
      range: RANGES.includes(range) ? range : 0,
      place: params.get(PARAM.place) ?? '',
      unit: units.some((u) => u.id === params.get(PARAM.unit)) ? params.get(PARAM.unit)! : '',
      fate: FATES.some((f) => f.value === fate) ? (fate as Fate) : '',
      wholeWords: params.get(PARAM.wholeWords) === '1',
    },
  }
}

/** Puts the search and its filters in `url`, leaving its other parameters (an open record) as they are */
export function writeSearch(url: URL, query: string, filters: SearchFilters, withUnit = true) {
  const year = birthYear(filters.year)
  const values: [string, string][] = [
    [PARAM.query, query.trim()],
    [PARAM.place, filters.place.trim()],
    [PARAM.year, year !== null ? String(year) : ''],
    [PARAM.range, year !== null && filters.range ? String(filters.range) : ''],
    [PARAM.unit, withUnit ? filters.unit : ''],
    [PARAM.fate, filters.fate],
    [PARAM.wholeWords, filters.wholeWords ? '1' : ''],
  ]
  for (const [key, value] of values) {
    if (value) url.searchParams.set(key, value)
    else url.searchParams.delete(key)
  }
}
