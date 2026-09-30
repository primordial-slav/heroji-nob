'use client'

import { useState, useEffect, useRef } from 'react'
import Fuse, { IFuseOptions } from 'fuse.js'
import { normalizeForSearch } from './diacritics'
import type { Soldier } from './types'

// Custom getFn that normalizes diacritics (and dj → d) during indexing
function normalizingGetFn(
  obj: Record<string, unknown>,
  path: string | string[]
): string | string[] {
  const value = Fuse.config.getFn(obj, path)
  if (Array.isArray(value)) {
    return value.map((v) => normalizeForSearch(String(v)))
  }
  if (typeof value === 'string') {
    return normalizeForSearch(value)
  }
  return value != null ? String(value) : ''
}

// full_name puts the father's name between surname and first name ("Kokalj Anrejev Rudolf"),
// so "Kokalj Rudolf" or "Rudolf Kokalj" would miss it. Index both two-name orders as well.
function nameVariants(soldier: Partial<Soldier>): string[] {
  const last = soldier.last_name?.trim()
  const first = soldier.first_name?.trim()
  if (!last || !first) return []
  return [`${last} ${first}`, `${first} ${last}`].map(normalizeForSearch)
}

const SOLDIER_KEYS = [
  { name: 'full_name', weight: 0.6 },
  { name: 'name_variants', weight: 0.6, getFn: nameVariants },
  { name: 'additional_info', weight: 0.2 },
  { name: 'birth_year', weight: 0.1 },
]
// Must stay the last key, see searchSoldiers
const UNIT_KEY = { name: 'unit', weight: 0.1 }

const FUSE_OPTIONS: IFuseOptions<Partial<Soldier>> = {
  keys: [...SOLDIER_KEYS, UNIT_KEY],
  threshold: 0.35,
  ignoreLocation: true,
  includeScore: true,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getFn: normalizingGetFn as any,
  fieldNormWeight: 1,
}

// `unit` is one of ~19 unit names, so matching it on every soldier repeats the
// same work tens of thousands of times. The soldier index skips it (its getFn
// yields nothing, but the key keeps its weight so the other keys' normalized
// weights stay the same) and the unit names are matched once in a small index.
const SOLDIER_FUSE_OPTIONS: IFuseOptions<Soldier> = {
  ...FUSE_OPTIONS,
  keys: [...SOLDIER_KEYS, { ...UNIT_KEY, getFn: () => '' }],
  shouldSort: false,
}

interface SoldierIndex {
  data: Soldier[]
  soldiers: Fuse<Soldier>
  units: Fuse<Partial<Soldier>>
  /** Soldier indices of each unit, in the order of the units index */
  unitMembers: number[][]
  /** Position of each soldier's unit in the units index, -1 if none */
  unitOf: Int32Array
  /** wordText of each soldier's full_name and additional_info, filled in as searches need them */
  nameText: (string | undefined)[]
  infoText: (string | undefined)[]
}

const NON_WORD = /[^a-z0-9À-ɏ]+/g

/** " rolic vojislava milomir ": a text's words, normalized, lowercased and space-delimited */
function wordText(text: string | undefined): string {
  return ` ${normalizeForSearch(text ?? '').toLowerCase().replace(NON_WORD, ' ').trim()} `
}

/**
 * How well one query word matches a soldier: 0 = a whole word of the name,
 * 1 = the start of a name word, 2 = the start of a word in the bio (so
 * "Gračac" also finds "u Gračacu"), 3 = inside a name word, 4 = only fuzzily.
 */
function wordRank(index: SoldierIndex, idx: number, word: string): number {
  const name = index.nameText[idx] ?? (index.nameText[idx] = wordText(index.data[idx].full_name))
  if (name.includes(` ${word} `)) return 0
  if (name.includes(` ${word}`)) return 1
  const info = index.infoText[idx] ?? (index.infoText[idx] = wordText(index.data[idx].additional_info))
  if (info.includes(` ${word}`)) return 2
  return name.includes(word) ? 3 : 4
}

export function createSoldierIndex(data: Soldier[]): SoldierIndex {
  const unitPos = new Map<string, number>()
  const unitMembers: number[][] = []
  const unitOf = new Int32Array(data.length).fill(-1)
  data.forEach((soldier, i) => {
    if (!soldier.unit) return
    let pos = unitPos.get(soldier.unit)
    if (pos === undefined) {
      pos = unitMembers.push([]) - 1
      unitPos.set(soldier.unit, pos)
    }
    unitMembers[pos].push(i)
    unitOf[i] = pos
  })
  return {
    data,
    soldiers: new Fuse(data, SOLDIER_FUSE_OPTIONS),
    units: new Fuse(Array.from(unitPos.keys(), (unit) => ({ unit })), FUSE_OPTIONS),
    unitMembers,
    unitOf,
    nameText: new Array(data.length),
    infoText: new Array(data.length),
  }
}

/**
 * The results of a single Fuse over FUSE_OPTIONS, best word matches first.
 *
 * Fuse scores every exact substring match alike and then prefers shorter
 * fields, so for "rolic" Korolić Stojan came before Rolić Vojislava Milomir,
 * and for "Gračac" people named Gravac or Gračan came before everyone from
 * Gračac. Results are therefore sorted by the sum of each query word's
 * wordRank, and in Fuse's order within the same sum.
 *
 * Fuse scores a soldier as the product of one factor per matching key, taken
 * in key order, so the `unit` factor (last key) multiplies the product of the
 * others, and a soldier matching by unit alone scores just that factor. The
 * units index has the same keys and only `unit` filled in, so its score is
 * that factor.
 */
export function searchSoldiers(index: SoldierIndex, query: string): Soldier[] {
  const { data, unitMembers, unitOf } = index
  const words = query.toLowerCase().split(NON_WORD).filter(Boolean)
  const rankOf = (idx: number) =>
    words.reduce((sum, word) => sum + wordRank(index, idx, word), 0)

  // 0 = no match; a unit factor is always > 0
  const unitFactor = new Float64Array(unitMembers.length)
  for (const hit of index.units.search(query)) {
    unitFactor[hit.refIndex] = hit.score!
  }

  const results: { idx: number; rank: number; score: number }[] = []
  const found = new Uint8Array(data.length)
  for (const { refIndex: idx, score } of index.soldiers.search(query)) {
    const factor = unitOf[idx] >= 0 ? unitFactor[unitOf[idx]] : 0
    results.push({ idx, rank: rankOf(idx), score: factor ? score! * factor : score! })
    found[idx] = 1
  }
  unitFactor.forEach((factor, pos) => {
    if (!factor) return
    for (const idx of unitMembers[pos]) {
      if (!found[idx]) results.push({ idx, rank: rankOf(idx), score: factor })
    }
  })

  // Within a rank, Fuse's default order: by score, then by position in data
  results.sort((a, b) => a.rank - b.rank || a.score - b.score || a.idx - b.idx)
  return results.map((r) => data[r.idx])
}

const DEBOUNCE_MS = 250

interface UseFuseSearchOptions {
  /** When true, an empty query returns all data. When false, returns empty array. */
  showAllOnEmpty: boolean
}

interface UseFuseSearchReturn {
  results: Soldier[]
  searchTerm: string
  setSearchTerm: (term: string) => void
  isSearching: boolean
}

export function useFuseSearch(
  data: Soldier[],
  options: UseFuseSearchOptions
): UseFuseSearchReturn {
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedTerm, setDebouncedTerm] = useState('')
  const [results, setResults] = useState<Soldier[]>([])
  const indexRef = useRef<SoldierIndex | null>(null)

  // Build search index when data changes
  useEffect(() => {
    if (data.length === 0) {
      indexRef.current = null
      return
    }
    indexRef.current = createSoldierIndex(data)
  }, [data])

  // Debounce the search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTerm(searchTerm)
    }, DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Execute search when debounced term changes
  useEffect(() => {
    if (!debouncedTerm.trim()) {
      setResults(options.showAllOnEmpty ? data : [])
      return
    }

    if (!indexRef.current) {
      setResults([])
      return
    }

    const normalizedQuery = normalizeForSearch(debouncedTerm.trim())
    setResults(searchSoldiers(indexRef.current, normalizedQuery))
  }, [debouncedTerm, data, options.showAllOnEmpty])

  const isSearching = searchTerm.trim().length > 0

  return { results, searchTerm, setSearchTerm, isSearching }
}
