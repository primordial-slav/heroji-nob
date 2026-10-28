import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import type { Soldier } from './types'
import { PORTRAIT_PEOPLE_PATH, RECORDS_PER_PART, onThisDayPath, recordsPath } from './dataFiles'

export { RECORDS_PER_PART, recordsPath }

// The data the pages load: a search, a page at a time, from the server (app/api/search/route.ts, lib/searchData.ts),
// and the files scripts/prepare-data.ts writes from the unit files (lib/dataFiles.ts): a soldier's full record in a
// slice of RECORDS_PER_PART records of the unit's data file, "Na današnji dan", the home page's portraits' soldiers.
// The rows in a list are short (encodeRow): per soldier only what the results, "Na današnji dan" and the dialog use,
// as an array rather than an object. A record's kin (the dialog's previous and next and its comrades tree) and a link
// to one record are answered by the server too, for that record alone (loadKin).
//
// What has loaded stays for the rest of the visit, so going back to a page or opening a record again shows it at once.
// Rows on the first page of a results list; a unit page's HTML has its unit's first page
export const FIRST_PAGE = 50
/** The page sizes a results list offers */
export const PAGE_SIZES = [FIRST_PAGE, 100, 200]

// A soldier's fields in an index row, then his other_sources (0 if none), then full_name if it isn't
// "last middle first". fathers_name is there only where it isn't middle_name (the father in the nominative, which
// search finds as well as the case the book prints). Empty fields at the end of a row are left out.
const FIELDS = [
  'soldier_id', 'last_name', 'middle_name', 'first_name', 'additional_info',
  'birth_year', 'death_date', 'death_type', 'death_place', 'unit_detail', 'fathers_name',
] as const
const SOURCE_FIELDS = ['soldier_id', 'name', 'additional_info', 'unit_file'] as const

type Cell = string | number | Cell[]
export type IndexRow = Cell[]
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
  const row: IndexRow = FIELDS.map((f) =>
    f === 'fathers_name' && soldier.fathers_name === soldier.middle_name ? '' : soldier[f] ?? '')
  const sources = (soldier.other_sources ?? []).map((o) => withoutTrailingEmpties(SOURCE_FIELDS.map((f) => o[f] ?? '')))
  row.push(sources.length ? sources : 0)
  row.push(soldier.full_name === joinedName(soldier) ? '' : soldier.full_name)
  return withoutTrailingEmpties(row)
}

/**
 * A soldier's row in a record's kin (lib/searchData.ts, kinPage): what the record dialog's previous and next and its
 * comrades tree read, and the ids his merged entries had, without the entries' text
 */
export function encodeKinRow(soldier: Soldier): IndexRow {
  return encodeRow({
    ...soldier,
    additional_info: '',
    death_place: '',
    fathers_name: soldier.middle_name,
    other_sources: soldier.other_sources?.filter((o) => o.soldier_id).map((o) => ({ soldier_id: o.soldier_id, additional_info: '' })),
  })
}

export function decodeRow(row: IndexRow, unit: string): Soldier {
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
  const listed: Soldier[] = []
  eachListedOnce(lists, (soldier, also) => listed.push(also.length ? { ...soldier, also_units: also } : soldier))
  return listed
}

/** Each soldier listOnce lists, with the other units he is listed in, and his place in all the lists together */
export function eachListedOnce(lists: Soldier[][], each: (soldier: Soldier, also: string[], at: number) => void) {
  const linkedAway = new Set<string>()
  let at = -1
  for (const list of lists) {
    for (const soldier of list) {
      at++
      if (linkedAway.has(soldier.soldier_id)) continue
      const links = (soldier.other_sources ?? []).filter((o) => o.unit_file)
      links.forEach((o) => o.soldier_id && linkedAway.add(o.soldier_id))
      const also = links
        .map((o) => units.find((u) => u.dataFile === `/${o.unit_file}`)?.name)
        .filter((u, i, list): u is string => Boolean(u) && u !== soldier.unit && list.indexOf(u) === i)
      each(soldier, also, at)
    }
  }
}

const pad = (n: number) => String(n).padStart(2, '0')
/** A day of the year as the on-this-day lists are named: "10-01" */
export const dayKey = (month: number, day: number) => `${pad(month)}-${pad(day)}`

// Where each soldier of the loaded lists is in his unit's data file
const located = new Map<string, { unit: string; position: number }>()

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) throw new Error(`${path}: ${response.status}`)
  return response.json()
}

const dayLists = new Map<string, Soldier[]>()

/** The soldiers who fell, died or went missing on this day of the war */
export async function loadOnThisDay(month: number, day: number): Promise<Soldier[]> {
  const key = dayKey(month, day)
  const loaded = dayLists.get(key)
  if (loaded) return loaded
  const list = placedSoldiers(await fetchJson<PlacedRow[]>(onThisDayPath(key)))
  dayLists.set(key, list)
  return list
}

/** The soldiers of a day's list or of a page of search results, each with where his full record is */
export function placedSoldiers(entries: PlacedRow[]): Soldier[] {
  return entries.flatMap(({ unit: id, position, row, also }) => {
    const unit = units.find((u) => u.id === id)
    if (!unit) return []
    const soldier = decodeRow(row, unit.name)
    if (also?.length) soldier.also_units = also
    located.set(soldier.soldier_id, { unit: unit.id, position })
    return [soldier]
  })
}

// The search the server answers (app/api/search/route.ts): the page's own address parameters, and these
export const SEARCH_API = '/api/search'
export const SEARCH_PAGE = { page: 'strana', perPage: 'po' } as const
/** The unit whose soldiers alone are searched, on a unit's page */
export const UNIT_PARAM = 'u'
/** With UNIT_PARAM: one record's kin (loadKin), by his id */
export const KIN_PARAM = 'kin'
/** With UNIT_PARAM: some records' rows (loadRows), by their ids, at most MOST_IDS at a time */
export const IDS_PARAM = 'ids'
export const MOST_IDS = 500

export interface SearchResultPage {
  /** How many soldiers the search found, after the filters */
  count: number
  /** Where the similar ones start among them, -1 if there are none */
  firstNear: number
  /** How many it found before the filters */
  unfiltered: number
  /** Which page this is, from 1, and how many soldiers a page has */
  page: number
  perPage: number
  /** The page's soldiers */
  soldiers: Soldier[]
}

/** One page of a search the server answers */
export async function searchOnServer(params: URLSearchParams, signal?: AbortSignal): Promise<SearchResultPage> {
  const response = await fetch(`${SEARCH_API}?${params}`, { signal })
  if (!response.ok) throw new Error(`${SEARCH_API}: ${response.status}`)
  const page: Omit<SearchResultPage, 'soldiers'> & { rows: PlacedRow[] } = await response.json()
  const { rows, ...counts } = page
  return { ...counts, soldiers: placedSoldiers(rows) }
}

let portraitPeople: Soldier[] | null = null
let portraitLoad: Promise<Soldier[]> | null = null

/** The soldiers whose portraits are in the home page's margins */
export function loadPortraitPeople(): Promise<Soldier[]> {
  portraitLoad ??= fetchJson<PlacedRow[]>(PORTRAIT_PEOPLE_PATH)
    .then((rows) => (portraitPeople = placedSoldiers(rows)))
    .catch((error) => {
      portraitLoad = null
      throw error
    })
  return portraitLoad
}

/** Those soldiers if they have loaded in this visit */
export const loadedPortraitPeople = () => portraitPeople

/** A day's list if it has loaded in this visit */
export const loadedOnThisDay = (month: number, day: number) => dayLists.get(dayKey(month, day))

// Each slice of full records once per visit: the records opened one after another are often in the same slice
const parts = new Map<string, Promise<Soldier[]>>()

// A slice that fails to load is asked for twice more, a moment apart (the server may be restarting, or a data file
// being written), before the dialog makes do with the list's short record, which has no book page or source link
async function fetchPart(path: string): Promise<Soldier[]> {
  for (const wait of [800, 2500]) {
    try {
      return await fetchJson<Soldier[]>(path)
    } catch {
      await new Promise((resolve) => setTimeout(resolve, wait))
    }
  }
  return fetchJson<Soldier[]>(path)
}

/**
 * The full record of a soldier from a loaded list, with the fields the page set on him. One the page has not loaded
 * (a neighbour from the places index: an id, a name and his unit) is found through his kin first.
 */
export async function fullRecord(soldier: Soldier): Promise<Soldier> {
  let at = located.get(soldier.soldier_id)
  const unit = at ? undefined : units.find((u) => u.name === soldier.unit)
  if (unit) {
    const kin = await loadKin(unit, soldier.soldier_id).catch(() => null)
    if (kin) {
      soldier = { ...kin.self, also_units: soldier.also_units }
      at = located.get(soldier.soldier_id)
    }
  }
  if (!at) return soldier
  const path = recordsPath(at.unit, Math.floor(at.position / RECORDS_PER_PART))
  let part = parts.get(path)
  if (!part) {
    part = fetchPart(path)
    part.catch(() => parts.delete(path))
    parts.set(path, part)
  }
  const full = (await part).find((r) => r.soldier_id === soldier.soldier_id)
  return full ? { ...full, unit: soldier.unit, also_units: soldier.also_units } : soldier
}

/** A record's kin in his unit (lib/searchData.ts, kinPage) */
export interface Kin {
  /** The record, found by its id or by an id one of its merged or linked entries had */
  self: Soldier
  /** The records before and after it in the unit's list, which is in the order of the books */
  previous?: Soldier
  next?: Soldier
  /** The soldiers of each level of his sub-unit, from the battalion down, himself among them */
  levels: Soldier[][]
  /** The unit's soldiers who fell the day he did, himself among them; none if he alone did */
  sameDay: Soldier[]
}

/** A soldier of a record's kin: his place in the unit's data file and his row */
type KinRow = [number, IndexRow]

interface KinAnswer {
  unit: string
  self: KinRow
  previous: KinRow | null
  next: KinRow | null
  rows: KinRow[]
  levels: number[][]
  sameDay: number[]
}

const kins = new Map<string, Promise<Kin | null>>()

/** A record's kin, null if the unit has no record of that id */
export function loadKin(unit: Unit, id: string): Promise<Kin | null> {
  const key = `${unit.id}/${id}`
  let load = kins.get(key)
  if (!load) {
    const params = new URLSearchParams({ [UNIT_PARAM]: unit.id, [KIN_PARAM]: id })
    load = fetch(`${SEARCH_API}?${params}`)
      .then(async (response): Promise<Kin | null> => {
        if (response.status === 404) return null
        if (!response.ok) throw new Error(`${SEARCH_API}: ${response.status}`)
        const answer: KinAnswer = await response.json()
        const placed = ([position, row]: KinRow): PlacedRow => ({ unit: answer.unit, position, row })
        const rows = placedSoldiers(answer.rows.map(placed))
        const one = (row: KinRow | null) => (row ? placedSoldiers([placed(row)])[0] : undefined)
        return {
          self: one(answer.self)!,
          previous: one(answer.previous),
          next: one(answer.next),
          levels: answer.levels.map((level) => level.map((k) => rows[k])),
          sameDay: answer.sameDay.map((k) => rows[k]),
        }
      })
      .catch((error) => {
        kins.delete(key)
        throw error
      })
    kins.set(key, load)
  }
  return load
}

/** Some records of a unit in the short form a list shows them (lib/searchData.ts, rowsPage), in the order asked */
export async function loadRows(unit: Unit, ids: string[]): Promise<Soldier[]> {
  const found: Soldier[] = []
  for (let start = 0; start < ids.length; start += MOST_IDS) {
    const params = new URLSearchParams({ [UNIT_PARAM]: unit.id, [IDS_PARAM]: ids.slice(start, start + MOST_IDS).join(',') })
    const answer = await fetchJson<{ rows: PlacedRow[] }>(`${SEARCH_API}?${params}`)
    found.push(...placedSoldiers(answer.rows))
  }
  return found
}
