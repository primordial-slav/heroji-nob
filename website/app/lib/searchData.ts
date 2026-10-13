import fs from 'fs'
import path from 'path'
import zlib from 'zlib'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { normalizeForSearch } from './diacritics'
import { createSoldierIndex, mergeHits, searchFields, searchSoldiers, type SearchHits, type SoldierIndex } from './soldierSearch'
import { decodeRow, eachListedOnce, encodeRow } from './searchIndex'
import { applyFilters, narrows, type SearchFilters } from './searchFilters'
import type { Soldier } from './types'

// Server only: the search that app/api/search/route.ts answers, over every unit's soldiers at once, so a page asks
// for one page of results instead of loading every soldier (searchIndex.ts). The same search as in the browser
// (soldierSearch.ts) and the same filters (searchFilters.ts), over the same rows (encodeRow).
//
// scripts/prepare-search.ts builds it while the site is built and writes it to search-data/, which the route's
// function carries (next.config.js) and reads once per instance; under `next dev` the route builds it from the
// data files instead, again when one changes.

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
  return {
    index: createSoldierIndex(all.map(searchFields)),
    unitAt, position, away, also, rows: Buffer.concat(texts), rowAt, unitStart,
  }
}

// The files: index.bin.gz holds a JSON header (the words, the units' words, `also`, and where each array is) and
// then the arrays; rows.bin.gz the rows
const ARRAYS = {
  key: Float64Array, key2: Float64Array, nameAt: Int32Array, names: Int32Array, entryAt: Int32Array,
  entries: Int32Array, nameWords: Int32Array, entryWords: Int32Array, unitOf: Int32Array,
  unitAt: Uint16Array, position: Int32Array, away: Uint8Array, rowAt: Int32Array, unitStart: Int32Array,
} as const
type ArrayName = keyof typeof ARRAYS

interface Header {
  size: number
  words: string[]
  unitWords: string[][]
  also: [number, string[]][]
  arrays: Record<ArrayName, [offset: number, length: number]>
}

export function writeSearchData(dir: string, data: SearchData) {
  const { index } = data
  const arrays: Record<ArrayName, ArrayLike<number> & { buffer: ArrayBufferLike; byteOffset: number; byteLength: number }> = {
    key: index.key, key2: index.key2, nameAt: index.nameAt, names: index.names, entryAt: index.entryAt,
    entries: index.entries, nameWords: index.nameWords, entryWords: index.entryWords, unitOf: index.unitOf,
    unitAt: data.unitAt, position: data.position, away: data.away, rowAt: data.rowAt, unitStart: data.unitStart,
  }
  const header: Header = {
    size: index.size, words: index.words, unitWords: index.unitWords, also: [...data.also], arrays: {} as Header['arrays'],
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
  }
}

// Soldiers read from their rows, for the filters; kept, as the same soldiers are asked for search after search
const decoded = new WeakMap<SearchData, (Soldier | undefined)[]>()

function soldierAt(data: SearchData, i: number): Soldier {
  let cache = decoded.get(data)
  if (!cache) decoded.set(data, (cache = []))
  let soldier = cache[i]
  if (!soldier) {
    soldier = decodeRow(JSON.parse(data.rows.toString('utf8', data.rowAt[i], data.rowAt[i + 1])), units[data.unitAt[i]].name)
    const also = data.also.get(i)
    if (also) soldier.also_units = also
    cache[i] = soldier
  }
  return soldier
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
  if (narrows(filters, home)) {
    const kept = new Set(applyFilters(listed.map((i) => soldierAt(data, i)), filters, home))
    const exact = listed.slice(0, nearFrom).filter((i) => kept.has(soldierAt(data, i))).length
    listed = listed.filter((i) => kept.has(soldierAt(data, i)))
    nearFrom = exact
  }
  return { listed: Int32Array.from(listed), nearFrom, unfiltered }
}
