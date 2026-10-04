import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import type { Soldier } from './types'

// The home page searches every unit at once, so instead of every unit's full data file (67 MB) it loads one
// compact list, in parts, /search-index/<part>: per soldier only what search, the results, "Na današnji dan"
// and the comrades tree in the dialog use, as an array rather than an object. A unit page loads its own unit's
// rows in the same form, /lists/<unit id>, and "Na današnji dan" the day's, /on-this-day/<MM-DD>. Opening a
// soldier loads his full record from /records/<unit id>/<part>, a slice of RECORDS_PER_PART records of the unit's
// data file. All are built from the data files (app/search-index/[part]/route.ts, app/lists/[unit]/route.ts,
// app/on-this-day/[day]/route.ts, app/records/[unit]/[part]/route.ts): at build time as static files, and fresh
// on every request under `next dev`.
//
// What has loaded stays for the rest of the visit, so going back to the home page or to a unit page shows its
// list at once, without loading and reading it again.

// The search list is about 40 MB, and Vercel refuses a prerendered response over 19 MB, so it comes in parts of
// whole units, up to INDEX_PART_SOLDIERS soldiers each: about 5 MB, and 15 MB even for the wordiest books
const INDEX_PART_SOLDIERS = 30000
/** The units of each part of the search list, in the order of `units` */
export const SEARCH_INDEX_PARTS: Unit[][] = units.reduce<Unit[][]>((parts, unit) => {
  const last = parts[parts.length - 1]
  if (last && last.reduce((n, u) => n + u.soldierCount, 0) + unit.soldierCount <= INDEX_PART_SOLDIERS) last.push(unit)
  else parts.push([unit])
  return parts
}, [])
export const searchIndexPath = (part: number) => `/search-index/${part}`
export const RECORDS_PER_PART = 250
// Rows on the first page of a results list; a unit page's HTML has its unit's first page
export const FIRST_PAGE = 50

// A soldier's fields in an index row, then his other_sources (0 if none), then full_name if it isn't
// "last middle first". Empty fields at the end of a row are left out.
const FIELDS = [
  'soldier_id', 'last_name', 'middle_name', 'first_name', 'additional_info',
  'birth_year', 'death_date', 'death_type', 'death_place', 'unit_detail',
] as const
const SOURCE_FIELDS = ['soldier_id', 'name', 'additional_info', 'unit_file'] as const

type Cell = string | number | Cell[]
export type IndexRow = Cell[]
/** Each unit's rows, by the unit's dataFile, in the order of the data file */
export type SearchIndex = Record<string, IndexRow[]>

/** A soldier of a day's list: his row, his unit's id, his place in its data file and the other units he is listed in */
export interface PlacedRow {
  unit: string
  position: number
  row: IndexRow
  also?: string[]
}

function withoutTrailingEmpties<T extends Cell>(row: T[]): T[] {
  let end = row.length
  while (end > 0 && (row[end - 1] === '' || row[end - 1] === 0)) end--
  return row.slice(0, end)
}

const joinedName = (s: Partial<Soldier>) => [s.last_name, s.middle_name, s.first_name].filter(Boolean).join(' ')

export function encodeRow(soldier: Soldier): IndexRow {
  const row: IndexRow = FIELDS.map((f) => soldier[f] ?? '')
  const sources = (soldier.other_sources ?? []).map((o) => withoutTrailingEmpties(SOURCE_FIELDS.map((f) => o[f] ?? '')))
  row.push(sources.length ? sources : 0)
  row.push(soldier.full_name === joinedName(soldier) ? '' : soldier.full_name)
  return withoutTrailingEmpties(row)
}

function decodeRow(row: IndexRow, unit: string): Soldier {
  const soldier: Record<string, unknown> = { fathers_name: '', unit }
  FIELDS.forEach((f, i) => { soldier[f] = row[i] ?? '' })
  const sources = row[FIELDS.length]
  if (Array.isArray(sources)) {
    soldier.other_sources = sources.map((source) =>
      Object.fromEntries(SOURCE_FIELDS.map((f, i) => [f, (source as Cell[])[i] ?? ''])))
  }
  soldier.full_name = row[FIELDS.length + 1] || joinedName(soldier as Partial<Soldier>)
  return soldier as unknown as Soldier
}

/**
 * Every unit's soldiers in one list, in the order of `units`. A soldier linked across units (an entry from another
 * unit's book in other_sources) is listed once, in the first of his units, with the others named in also_units.
 */
export function listOnce(lists: Soldier[][]): Soldier[] {
  const linkedAway = new Set<string>()
  const listed: Soldier[] = []
  for (const soldier of lists.flat()) {
    if (linkedAway.has(soldier.soldier_id)) continue
    const links = (soldier.other_sources ?? []).filter((o) => o.unit_file)
    links.forEach((o) => o.soldier_id && linkedAway.add(o.soldier_id))
    const also = links
      .map((o) => units.find((u) => u.dataFile === `/${o.unit_file}`)?.name)
      .filter((u, i, list): u is string => Boolean(u) && u !== soldier.unit && list.indexOf(u) === i)
    listed.push(also.length ? { ...soldier, also_units: also } : soldier)
  }
  return listed
}

export const recordsPath = (unitId: string, part: number) => `/records/${unitId}/${part}`
export const listPath = (unit: Unit) => `/lists/${unit.id}`
const pad = (n: number) => String(n).padStart(2, '0')
/** A day of the year as the on-this-day lists are named: "10-01" */
export const dayKey = (month: number, day: number) => `${pad(month)}-${pad(day)}`

// Where each soldier of the loaded lists is in his unit's data file
const located = new Map<string, { unit: string; position: number }>()

function decodeList(rows: IndexRow[], unit: Unit): Soldier[] {
  return rows.map((row, position) => {
    const soldier = decodeRow(row, unit.name)
    located.set(soldier.soldier_id, { unit: unit.id, position })
    return soldier
  })
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`${path}: ${response.status}`)
  return response.json()
}

// Each unit's list by unit id, from the search index or the unit's own list, whichever came first: the home
// page and the unit's page then share one list, and its search workers (useFuseSearch)
const unitLists = new Map<string, Soldier[]>()
const unitLoads = new Map<string, Promise<Soldier[]>>()

function keepList(unit: Unit, rows: IndexRow[]): Soldier[] {
  let list = unitLists.get(unit.id)
  if (!list) {
    list = decodeList(rows, unit)
    unitLists.set(unit.id, list)
  }
  return list
}

export interface HomeLists {
  /** Each unit's whole list, linked soldiers included, by the unit's name */
  byUnit: Map<string, Soldier[]>
  /** Every soldier once (listOnce) */
  listed: Soldier[]
}

let homeLists: HomeLists | null = null
let homeLoad: Promise<HomeLists> | null = null

/** Every unit's soldiers from the search index, with `unit` set to the unit's name */
export function loadHomeLists(): Promise<HomeLists> {
  homeLoad ??= Promise.all(SEARCH_INDEX_PARTS.map((_, part) => fetchJson<SearchIndex>(searchIndexPath(part))))
    .then((parts) => {
      const index: SearchIndex = Object.assign({}, ...parts)
      const lists = units.map((unit) => keepList(unit, index[unit.dataFile] ?? []))
      homeLists = { byUnit: new Map(units.map((unit, i) => [unit.name, lists[i]])), listed: listOnce(lists) }
      return homeLists
    })
    .catch((error) => {
      homeLoad = null
      throw error
    })
  return homeLoad
}

/** The home page's lists if they have loaded in this visit */
export const loadedHomeLists = () => homeLists

/** One unit's soldiers in the search index's form, with `unit` set to the unit's name */
export function loadUnitList(unit: Unit): Promise<Soldier[]> {
  const loaded = unitLists.get(unit.id)
  if (loaded) return Promise.resolve(loaded)
  let load = unitLoads.get(unit.id)
  if (!load) {
    load = fetchJson<IndexRow[]>(listPath(unit))
      .then((rows) => keepList(unit, rows))
      .catch((error) => {
        unitLoads.delete(unit.id)
        throw error
      })
    unitLoads.set(unit.id, load)
  }
  return load
}

/** A unit's list if it has loaded in this visit */
export const loadedUnitList = (unit: Unit) => unitLists.get(unit.id)

const dayLists = new Map<string, Soldier[]>()

/** The soldiers who fell, died or went missing on this day of the war (app/on-this-day/[day]/route.ts) */
export async function loadOnThisDay(month: number, day: number): Promise<Soldier[]> {
  const key = dayKey(month, day)
  const loaded = dayLists.get(key)
  if (loaded) return loaded
  const entries = await fetchJson<PlacedRow[]>(`/on-this-day/${key}`)
  const list = entries.flatMap(({ unit: id, position, row, also }) => {
    const unit = units.find((u) => u.id === id)
    if (!unit) return []
    const soldier = decodeRow(row, unit.name)
    if (also?.length) soldier.also_units = also
    located.set(soldier.soldier_id, { unit: unit.id, position })
    return [soldier]
  })
  dayLists.set(key, list)
  return list
}

/** A day's list if it has loaded in this visit */
export const loadedOnThisDay = (month: number, day: number) => dayLists.get(dayKey(month, day))

// Each slice of full records once per visit: the records opened one after another are often in the same slice
const parts = new Map<string, Promise<Soldier[]>>()

/** The full record of a soldier from a loaded list, with the fields the page set on him */
export async function fullRecord(soldier: Soldier): Promise<Soldier> {
  const at = located.get(soldier.soldier_id)
  if (!at) return soldier
  const path = recordsPath(at.unit, Math.floor(at.position / RECORDS_PER_PART))
  let part = parts.get(path)
  if (!part) {
    part = fetchJson<Soldier[]>(path)
    part.catch(() => parts.delete(path))
    parts.set(path, part)
  }
  const full = (await part).find((r) => r.soldier_id === soldier.soldier_id)
  return full ? { ...full, unit: soldier.unit, also_units: soldier.also_units } : soldier
}
