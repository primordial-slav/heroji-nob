import fs from 'fs'
import path from 'path'
import zlib from 'zlib'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { normalizeForSearch } from './diacritics'
import { createSoldierIndex, mergeHits, searchFields, searchSoldiers, type SearchHits, type SoldierIndex } from './soldierSearch'
import { decodeRow, eachListedOnce, encodeKinRow, encodeRow, type IndexRow } from './searchIndex'
import { deathDay, subunitPath } from './relations'
import { FATES, birthYear, entryWords, narrows, placeNeedle, type SearchFilters } from './searchFilters'
import type { Soldier } from './types'

// Server only: the search that app/api/search/route.ts answers, over every unit's soldiers at once, so a page asks
// for one page of results instead of loading every soldier. The search (soldierSearch.ts) and the filters
// (searchFilters.ts) over the rows the lists show (encodeRow), and a record's kin in his unit (kinPage).
//
// scripts/prepare-data.ts builds it from the data files and writes it to search-data/, before the site is built and
// under `next dev` whenever a data file changes; the route's function carries it (next.config.js) and reads it once
// per instance.

export interface SearchData {
  index: SoldierIndex
  /** Each soldier's unit (its place in `units`) and his place in the unit's data file */
  unitAt: Uint16Array
  position: Int32Array
  /** 1 for a soldier the home page doesn't list: one linked across units is listed once, in his first unit */
  away: Uint8Array
  /** The other units a soldier the home page lists is in (listOnce) */
  also: Map<number, string[]>
  /** Each soldier's row (encodeRow) as JSON: rows[rowAt[i] .. rowAt[i + 1]] */
  rows: Buffer
  rowAt: Int32Array
  /** Each unit's soldiers are unitStart[u] .. unitStart[u + 1] */
  unitStart: Int32Array
  /**
   * What the place filter looks in for each soldier (entryWords): filterText()[filterAt[i] .. filterAt[i + 1]]; read
   * from its file the first time a place is asked for, not when the function starts
   */
  filterText: () => Buffer
  filterAt: Int32Array
  /** What the year and fate filters read: the birth year as a number (NaN if none), how he died (deathTypes) */
  born: Float64Array
  deathType: Uint16Array
  deathTypes: string[]
}

/** `make`'s value, made the first time it is asked for */
function once<T>(make: () => T): () => T {
  let value: T | undefined
  return () => (value ??= make())
}

/** Every unit's soldiers, in the order of `units` and of each unit's data file */
export function buildSearchData(read: (unit: Unit) => Soldier[]): SearchData {
  const lists = units.map((unit) => read(unit).map((soldier) => ({ ...soldier, unit: unit.name })))
  const all = lists.flat()
  const unitAt = new Uint16Array(all.length)
  const position = new Int32Array(all.length)
  const unitStart = new Int32Array(units.length + 1)
  lists.forEach((list, u) => {
    unitStart[u + 1] = unitStart[u] + list.length
    list.forEach((_, p) => {
      unitAt[unitStart[u] + p] = u
      position[unitStart[u] + p] = p
    })
  })
  const away = new Uint8Array(all.length).fill(1)
  const also = new Map<number, string[]>()
  eachListedOnce(lists, (_, alsoIn, at) => {
    away[at] = 0
    if (alsoIn.length) also.set(at, alsoIn)
  })
  const texts = all.map((soldier) => Buffer.from(JSON.stringify(encodeRow(soldier))))
  const rowAt = new Int32Array(all.length + 1)
  texts.forEach((text, i) => { rowAt[i + 1] = rowAt[i] + text.length })
  const filterTexts = all.map((soldier) => Buffer.from(entryWords(soldier)))
  const filterAt = new Int32Array(all.length + 1)
  filterTexts.forEach((text, i) => { filterAt[i + 1] = filterAt[i] + text.length })
  const born = Float64Array.from(all, (soldier) => parseInt(soldier.birth_year ?? '', 10))
  const deathTypes: string[] = []
  const deathType = Uint16Array.from(all, (soldier) => {
    const type = soldier.death_type ?? ''
    const k = deathTypes.indexOf(type)
    return k >= 0 ? k : deathTypes.push(type) - 1
  })
  return {
    index: createSoldierIndex(all.map(searchFields)),
    unitAt, position, away, also, rows: Buffer.concat(texts), rowAt, unitStart,
    filterText: once(() => Buffer.concat(filterTexts)), filterAt, born, deathType, deathTypes,
  }
}

// The files: index.bin.gz holds a JSON header (the words, the units' words, `also`, and where each array is) and
// then the arrays; rows.bin.gz the rows; filters.bin.gz what the place filter looks in
const ARRAYS = {
  key: Float64Array, key2: Float64Array, nameAt: Int32Array, names: Int32Array, entryAt: Int32Array,
  entries: Int32Array, nameWords: Int32Array, entryWords: Int32Array, unitOf: Int32Array,
  unitAt: Uint16Array, position: Int32Array, away: Uint8Array, rowAt: Int32Array, unitStart: Int32Array,
  filterAt: Int32Array, born: Float64Array, deathType: Uint16Array,
} as const
type ArrayName = keyof typeof ARRAYS

interface Header {
  size: number
  words: string[]
  unitWords: string[][]
  also: [number, string[]][]
  deathTypes: string[]
  arrays: Record<ArrayName, [offset: number, length: number]>
}

export function writeSearchData(dir: string, data: SearchData) {
  const { index } = data
  const arrays: Record<ArrayName, ArrayLike<number> & { buffer: ArrayBufferLike; byteOffset: number; byteLength: number }> = {
    key: index.key, key2: index.key2, nameAt: index.nameAt, names: index.names, entryAt: index.entryAt,
    entries: index.entries, nameWords: index.nameWords, entryWords: index.entryWords, unitOf: index.unitOf,
    unitAt: data.unitAt, position: data.position, away: data.away, rowAt: data.rowAt, unitStart: data.unitStart,
    filterAt: data.filterAt, born: data.born, deathType: data.deathType,
  }
  const header: Header = {
    size: index.size, words: index.words, unitWords: index.unitWords, also: [...data.also], deathTypes: data.deathTypes,
    arrays: {} as Header['arrays'],
  }
  // Each array starts at a multiple of 8 bytes, so it can be read where it lies
  const chunks: Buffer[] = []
  let offset = 0
  for (const name of Object.keys(ARRAYS) as ArrayName[]) {
    const array = arrays[name]
    header.arrays[name] = [offset, array.length]
    const bytes = Buffer.from(array.buffer, array.byteOffset, array.byteLength)
    const padding = (8 - (bytes.length % 8)) % 8
    chunks.push(bytes, Buffer.alloc(padding))
    offset += bytes.length + padding
  }
  const head = Buffer.from(JSON.stringify(header))
  const headLength = Buffer.alloc(8)
  headLength.writeUInt32LE(head.length)
  const headPadding = Buffer.alloc((8 - (head.length % 8)) % 8)
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'index.bin.gz'), zlib.gzipSync(Buffer.concat([headLength, head, headPadding, ...chunks])))
  fs.writeFileSync(path.join(dir, 'rows.bin.gz'), zlib.gzipSync(data.rows))
  fs.writeFileSync(path.join(dir, 'filters.bin.gz'), zlib.gzipSync(data.filterText()))
}

export function readSearchData(dir: string): SearchData {
  const file = zlib.gunzipSync(fs.readFileSync(path.join(dir, 'index.bin.gz')))
  const headLength = file.readUInt32LE(0)
  const header: Header = JSON.parse(file.toString('utf8', 8, 8 + headLength))
  const start = 8 + headLength + ((8 - (headLength % 8)) % 8)
  // A copy of the arrays' bytes in a buffer of their own, so each array lies at a multiple of its element size
  const body = new Uint8Array(file.length - start)
  body.set(file.subarray(start))
  const get = <N extends ArrayName>(name: N) => {
    const [offset, length] = header.arrays[name]
    return new ARRAYS[name](body.buffer, offset, length) as InstanceType<(typeof ARRAYS)[N]>
  }
  const unitOf = get('unitOf')
  const unitMembers: number[][] = header.unitWords.map(() => [])
  unitOf.forEach((pos, i) => { if (pos >= 0) unitMembers[pos].push(i) })
  const index: SoldierIndex = {
    size: header.size, key: get('key'), key2: get('key2'),
    ids: new Map(header.words.map((word, w) => [word, w])), words: header.words,
    nameAt: get('nameAt'), names: get('names'), entryAt: get('entryAt'), entries: get('entries'),
    nameWords: get('nameWords'), entryWords: get('entryWords'),
    unitWords: header.unitWords, unitMembers, unitOf,
  }
  return {
    index, unitAt: get('unitAt'), position: get('position'), away: get('away'), also: new Map(header.also),
    rows: zlib.gunzipSync(fs.readFileSync(path.join(dir, 'rows.bin.gz'))), rowAt: get('rowAt'), unitStart: get('unitStart'),
    filterText: once(() => zlib.gunzipSync(fs.readFileSync(path.join(dir, 'filters.bin.gz')))), filterAt: get('filterAt'),
    born: get('born'), deathType: get('deathType'), deathTypes: header.deathTypes,
  }
}

/**
 * Whom the filters keep, as applyFilters (searchFilters.ts) decides, from what the data keeps of each soldier, so no
 * soldier's row is read; null if they keep everyone
 */
function filterTest(data: SearchData, filters: SearchFilters, withUnit: boolean): ((i: number) => boolean) | null {
  const year = birthYear(filters.year)
  const unitName = withUnit && filters.unit ? units.find((u) => u.id === filters.unit)?.name : undefined
  const fate = FATES.find((f) => f.value === filters.fate)
  const needle = placeNeedle(filters.place)
  if (year === null && !unitName && !fate && !needle) return null
  const fateTypes = fate ? new Set(fate.types.map((type) => data.deathTypes.indexOf(type))) : null
  // A place is looked for in every soldier's text at once
  const named = needle ? namingPlace(data, needle) : null
  return (i) => {
    if (unitName && units[data.unitAt[i]].name !== unitName && !data.also.get(i)?.includes(unitName)) return false
    if (fateTypes && !fateTypes.has(data.deathType[i])) return false
    if (year !== null && (Number.isNaN(data.born[i]) || Math.abs(data.born[i] - year) > filters.range)) return false
    if (named && !named[i]) return false
    return true
  }
}

/** 1 for each soldier whose place filter text (entryWords) holds `needle` */
function namingPlace(data: SearchData, needle: string): Uint8Array {
  const named = new Uint8Array(data.index.size)
  const bytes = Buffer.from(needle)
  const filterText = data.filterText()
  const { filterAt } = data
  let at = filterText.indexOf(bytes)
  while (at >= 0) {
    // The soldier whose text this is: the last one starting at or before it
    let lo = 0, hi = data.index.size - 1
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1
      if (filterAt[mid] <= at) lo = mid
      else hi = mid - 1
    }
    named[lo] = 1
    at = filterText.indexOf(bytes, filterAt[lo + 1])
  }
  return named
}

/** The hits of the soldiers `keep` takes, in their order */
function keepHits(hits: SearchHits, keep: (i: number) => boolean): SearchHits {
  const at: number[] = []
  hits.idx.forEach((i, k) => keep(i) && at.push(k))
  return {
    idx: Int32Array.from(at, (k) => hits.idx[k]),
    missed: Int32Array.from(at, (k) => hits.missed[k]),
    near: Uint8Array.from(at, (k) => hits.near[k]),
    score: Float64Array.from(at, (k) => hits.score[k]),
    key: Float64Array.from(at, (k) => hits.key[k]),
    key2: Float64Array.from(at, (k) => hits.key2[k]),
    terms: hits.terms,
  }
}

export interface SearchRequest {
  query: string
  filters: SearchFilters
  /** From 1 */
  page: number
  perPage: number
  /** A unit's page searches only that unit's soldiers (its position in `units`); the home page every soldier once */
  unit?: number
}

/**
 * One page of a search, as JSON: how many soldiers it found (`count`), where the similar ones start among them
 * (`firstNear`, -1 if there are none), how many it found before the filters (`unfiltered`), which page this is
 * (`page`, `perPage`), and the page's soldiers as a day's list gives them (`rows`, PlacedRow).
 */
export function searchPage(data: SearchData, { query, filters, page, perPage, unit }: SearchRequest): string {
  const home = unit === undefined
  const { listed, nearFrom, unfiltered } = searchList(data, query, filters, unit)
  const start = (page - 1) * perPage
  const rows = Array.from(listed.slice(start, start + perPage), (i) => {
    const also = data.also.get(i)
    return `{"unit":${JSON.stringify(units[data.unitAt[i]].id)},"position":${data.position[i]},"row":${
      data.rows.toString('utf8', data.rowAt[i], data.rowAt[i + 1])}${also && home ? `,"also":${JSON.stringify(also)}` : ''}}`
  })
  const firstNear = nearFrom < listed.length ? nearFrom : -1
  return `{"count":${listed.length},"firstNear":${firstNear},"unfiltered":${unfiltered},"page":${page},"perPage":${perPage},"rows":[${rows.join(',')}]}`
}

interface Listed {
  /** The soldiers found, filtered, best first */
  listed: Int32Array
  /** Where the similar ones start */
  nearFrom: number
  /** How many were found before the filters */
  unfiltered: number
}

// The last searches' lists, so another page of one, or the same search again, is only cut from its list
const KEPT_SEARCHES = 100
const searches = new WeakMap<SearchData, Map<string, Listed>>()

function searchList(data: SearchData, query: string, filters: SearchFilters, unit?: number): Listed {
  const typed = normalizeForSearch(query.trim())
  const key = JSON.stringify([typed.toLowerCase(), filters, unit ?? null])
  let kept = searches.get(data)
  if (!kept) searches.set(data, (kept = new Map()))
  const known = kept.get(key)
  if (known) {
    // Last used last
    kept.delete(key)
    kept.set(key, known)
    return known
  }
  const listed = runSearch(data, typed, filters, unit)
  kept.set(key, listed)
  if (kept.size > KEPT_SEARCHES) kept.delete(kept.keys().next().value!)
  return listed
}

function runSearch(data: SearchData, typed: string, filters: SearchFilters, unit?: number): Listed {
  const home = unit === undefined
  const inScope = home ? (i: number) => !data.away[i] : (i: number) => data.unitAt[i] === unit
  let found: ArrayLike<number>
  let nearFrom: number
  if (typed) {
    const merged = mergeHits([{ hits: keepHits(searchSoldiers(data.index, typed, filters.wholeWords), inScope), start: 0 }])
    found = merged.positions
    nearFrom = merged.nearFrom
  } else if (!home) {
    // A unit's whole list, in the order of its book
    found = Int32Array.from({ length: data.unitStart[unit + 1] - data.unitStart[unit] }, (_, k) => data.unitStart[unit] + k)
    nearFrom = found.length
  } else if (narrows(filters)) {
    // A place, year, unit or fate alone lists everyone who matches it
    const everyone: number[] = []
    for (let i = 0; i < data.index.size; i++) if (inScope(i)) everyone.push(i)
    found = everyone
    nearFrom = everyone.length
  } else {
    found = []
    nearFrom = 0
  }
  const unfiltered = found.length

  let listed: number[] = Array.from(found)
  const keep = filterTest(data, filters, home)
  if (keep) {
    nearFrom = listed.slice(0, nearFrom).filter(keep).length
    listed = listed.filter(keep)
  }
  return { listed: Int32Array.from(listed), nearFrom, unfiltered }
}

// ── One record's kin ─────────────────────────────────────────
// The record dialog's previous and next and its comrades tree, and a link to one record (?borac=), are answered
// here for the one soldier asked for, so a page doesn't load the unit's whole list for them

/** A soldier's row as a day's list gives it (PlacedRow): his unit's id, his place in its data file, the row */
function placed(data: SearchData, i: number, row: string): string {
  return `{"unit":${JSON.stringify(units[data.unitAt[i]].id)},"position":${data.position[i]},"row":${row}}`
}

const rowOf = (data: SearchData, i: number) => data.rows.toString('utf8', data.rowAt[i], data.rowAt[i + 1])

// The kin list's row (encodeKinRow): without the entries' text
function kinRow(data: SearchData, i: number): string {
  const unit = units[data.unitAt[i]]
  return JSON.stringify(encodeKinRow(decodeRow(JSON.parse(rowOf(data, i)) as IndexRow, unit.name)))
}

interface UnitKin {
  /** Each soldier's sub-unit path, as its levels' keys ("b1", "c2"), by his place in the unit */
  paths: string[][]
  /** His day of death ("1943-06-13"), where the record gives one in the war */
  days: (string | null)[]
  /** His place in the unit by his id, or by an id one of his merged or linked entries had, so old links keep working */
  byId: Map<string, number>
}

// The units last asked about
const KEPT_UNITS = 12
const unitKins = new WeakMap<SearchData, Map<number, UnitKin>>()

function unitKin(data: SearchData, unit: number): UnitKin {
  let kept = unitKins.get(data)
  if (!kept) unitKins.set(data, (kept = new Map()))
  const known = kept.get(unit)
  if (known) {
    kept.delete(unit)
    kept.set(unit, known)
    return known
  }
  const start = data.unitStart[unit]
  const soldiers = Array.from({ length: data.unitStart[unit + 1] - start }, (_, k) =>
    decodeRow(JSON.parse(rowOf(data, start + k)) as IndexRow, units[unit].name))
  const byId = new Map<string, number>()
  soldiers.forEach((s, k) => byId.set(s.soldier_id, k))
  soldiers.forEach((s, k) => s.other_sources?.forEach((o) => o.soldier_id && !byId.has(o.soldier_id) && byId.set(o.soldier_id, k)))
  const kin: UnitKin = {
    paths: soldiers.map((s) => subunitPath(s.unit_detail).map((level) => level.key)),
    days: soldiers.map((s) => deathDay(s)),
    byId,
  }
  kept.set(unit, kin)
  if (kept.size > KEPT_UNITS) kept.delete(kept.keys().next().value!)
  return kin
}

/**
 * A record's kin in his unit, as JSON, or null if the unit has no soldier of that id: the unit's id (`unit`), the
 * record (`self`), the ones before and after it in the unit's list (`previous`, `next`, null at its ends), and the
 * soldiers of each level of his sub-unit (`levels`) and those who fell the same day (`sameDay`), as places in `rows`.
 * Each soldier is [his place in the unit's data file, his row (encodeKinRow)].
 */
export function kinPage(data: SearchData, unit: number, id: string): string | null {
  const kin = unitKin(data, unit)
  const k = kin.byId.get(id)
  if (k === undefined) return null
  const start = data.unitStart[unit]
  const size = data.unitStart[unit + 1] - start
  const row = (j: number) => `[${data.position[start + j]},${kinRow(data, start + j)}]`
  // Borci drugih jedinica and the census's parts gather men of every unit: a sub-unit is a group of comrades there only
  // under the brigade or odred it names (relations.ts, HIGHER), and the same day is no one's comrade (2026-10-30)
  const ostali = units[unit].id.startsWith('ostali-borci')
  const path = ostali && !kin.paths[k][0]?.startsWith('g:') ? [] : kin.paths[k]
  const levels = path.map((_, depth) => {
    const members: number[] = []
    kin.paths.forEach((p, j) => {
      if (p.length > depth && p.slice(0, depth + 1).every((key, d) => key === path[d])) members.push(j)
    })
    return members
  })
  const day = ostali ? null : kin.days[k]
  const sameDay: number[] = []
  if (day) kin.days.forEach((d, j) => d === day && sameDay.push(j))
  // each soldier's row once, however many groups he is in
  const shown = new Map<number, number>()
  const at = (j: number) => {
    let n = shown.get(j)
    if (n === undefined) shown.set(j, (n = shown.size))
    return n
  }
  const levelsAt = levels.map((members) => members.map(at))
  const sameDayAt = sameDay.length > 1 ? sameDay.map(at) : []
  const rows = Array.from(shown.keys(), row)
  return `{"unit":${JSON.stringify(units[unit].id)},"self":${row(k)},"previous":${k > 0 ? row(k - 1) : 'null'},"next":${k + 1 < size ? row(k + 1) : 'null'},` +
    `"rows":[${rows.join(',')}],"levels":${JSON.stringify(levelsAt)},"sameDay":${JSON.stringify(sameDayAt)}}`
}

/** The rows of these soldiers of a unit (found as kinPage finds one), as JSON: `rows`, PlacedRow, in the order asked */
export function rowsPage(data: SearchData, unit: number, ids: string[]): string {
  const kin = unitKin(data, unit)
  const start = data.unitStart[unit]
  const rows = ids.flatMap((id) => {
    const k = kin.byId.get(id)
    return k === undefined ? [] : [placed(data, start + k, rowOf(data, start + k))]
  })
  return `{"rows":[${rows.join(',')}]}`
}
