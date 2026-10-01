import Fuse, { IFuseOptions } from 'fuse.js'
import { normalizeForSearch } from './diacritics'
import type { Soldier } from './types'

// The search itself, without React. useFuseSearch runs it off the page's thread, in search.worker.ts, each worker
// on a slice of the soldiers, and merges the slices' hits.

/** What search reads of a soldier: a worker is sent only this */
export interface SearchFields {
  full_name: string
  last_name: string
  first_name: string
  additional_info: string
  birth_year: string
  unit?: string
  other_sources?: { name?: string; additional_info: string }[]
}

export function searchFields(soldier: Soldier): SearchFields {
  return {
    full_name: soldier.full_name,
    last_name: soldier.last_name,
    first_name: soldier.first_name,
    additional_info: soldier.additional_info,
    birth_year: soldier.birth_year,
    unit: soldier.unit,
    other_sources: soldier.other_sources?.map((o) => ({ name: o.name, additional_info: o.additional_info })),
  }
}

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

// The name a bio gives as "zvani Muta" / "zvana Mica": families often know a soldier only by it
const NICKNAME = /\bzvan[aio]\s+[„"»]?([A-ZČĆŽŠĐ][a-zčćžšđ'-]+)/g

function nicknames(soldier: Partial<SearchFields>): string[] {
  const bios = [soldier.additional_info, ...(soldier.other_sources ?? []).map((o) => o.additional_info)]
  const found: string[] = []
  for (const bio of bios) {
    for (const m of (bio ?? '').matchAll(NICKNAME)) if (!found.includes(m[1])) found.push(m[1])
  }
  return found
}

// full_name puts the father's name between surname and first name ("Kokalj Anrejev Rudolf"),
// so "Kokalj Rudolf" or "Rudolf Kokalj" would miss it. Index both two-name orders as well,
// the name as the soldier's other books print it ("Belić Momćilo" for Belić Momčilo),
// and the surname with a nickname from the bio.
function nameVariants(soldier: Partial<SearchFields>): string[] {
  const last = soldier.last_name?.trim()
  const first = soldier.first_name?.trim()
  const printed = (soldier.other_sources ?? []).map((o) => o.name).filter((n): n is string => !!n)
  if (!last) return printed.map(normalizeForSearch)
  const given = [first, ...nicknames(soldier)].filter((n): n is string => !!n)
  return [...given.flatMap((g) => [`${last} ${g}`, `${g} ${last}`]), ...printed].map(normalizeForSearch)
}

/** The soldier's names as words: full_name, the names other books print, and nicknames */
function nameWords(soldier: SearchFields): string {
  return [soldier.full_name, ...(soldier.other_sources ?? []).map((o) => o.name ?? ''), ...nicknames(soldier)].join(' ')
}

/** The soldier's bios as words: own, and those of other books */
function infoWords(soldier: SearchFields): string {
  return [soldier.additional_info, ...(soldier.other_sources ?? []).map((o) => o.additional_info)].join(' ')
}

const SOLDIER_KEYS = [
  { name: 'full_name', weight: 0.6 },
  { name: 'name_variants', weight: 0.6, getFn: nameVariants },
  { name: 'additional_info', weight: 0.2 },
  { name: 'birth_year', weight: 0.1 },
]
// Must stay the last key, see searchSoldiers
const UNIT_KEY = { name: 'unit', weight: 0.1 }

const FUSE_OPTIONS: IFuseOptions<Partial<SearchFields>> = {
  keys: [...SOLDIER_KEYS, UNIT_KEY],
  threshold: 0.35,
  ignoreLocation: true,
  includeScore: true,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getFn: normalizingGetFn as any,
  fieldNormWeight: 1,
}

// `unit` is one of a few dozen unit names, so matching it on every soldier repeats the
// same work tens of thousands of times. The soldier index skips it (its getFn
// yields nothing, but the key keeps its weight so the other keys' normalized
// weights stay the same) and the unit names are matched once in a small index.
const SOLDIER_FUSE_OPTIONS: IFuseOptions<SearchFields> = {
  ...FUSE_OPTIONS,
  keys: [...SOLDIER_KEYS, { ...UNIT_KEY, getFn: () => '' }],
  shouldSort: false,
}

export interface SoldierIndex {
  data: SearchFields[]
  soldiers: Fuse<SearchFields>
  units: Fuse<Partial<SearchFields>>
  /** Soldier indices of each unit, in the order of the units index */
  unitMembers: number[][]
  /** Position of each soldier's unit in the units index, -1 if none */
  unitOf: Int32Array
  /** wordText of each soldier's full_name and additional_info, filled in as searches need them */
  nameText: (string | undefined)[]
  infoText: (string | undefined)[]
}

/** Search results as positions in the searched list, best first, with what they are ordered by */
export interface SearchHits {
  idx: Int32Array
  rank: Int32Array
  score: Float64Array
}

const NON_WORD = /[^a-z0-9À-ɏ]+/g

/** " rolic vojislava milomir ": a text's words, normalized, lowercased and space-delimited */
function wordText(text: string | undefined): string {
  return ` ${normalizeForSearch(text ?? '').toLowerCase().replace(NON_WORD, ' ').trim()} `
}

// Case endings of nouns and adjectives, folded as wordText folds them: "u Gračacu", "iz Divosela", "v Trbovljah"
const ENDINGS = 'a|e|i|o|u|om|em|im|ih|oj|og|ah|ama|ima|oga|ega|omu|emu'

type QueryWord = { word: string; inBio: RegExp }

/**
 * A query word, and the bio words that are it in another case. A final vowel
 * is the ending itself, so "Divoselo" also finds "iz Divosela".
 */
function queryWord(word: string): QueryWord {
  const stem = word.length >= 4 && /[aeiou]$/.test(word) ? word.slice(0, -1) : word
  return { word, inBio: new RegExp(` (?:${word}|${stem})(?:${ENDINGS})? `) }
}

/**
 * How well one query word matches a soldier: 0 = a whole word of the name,
 * 1 = the start of a name word, 2 = a word of the bio, in any case ("Gračac"
 * also finds "u Gračacu"), 3 = the start of another bio word (Divoš, then
 * Divoselo), 4 = inside a name word, 5 = only fuzzily.
 */
function wordRank(index: SoldierIndex, idx: number, { word, inBio }: QueryWord): number {
  const name = index.nameText[idx] ?? (index.nameText[idx] = wordText(nameWords(index.data[idx])))
  if (name.includes(` ${word} `)) return 0
  if (name.includes(` ${word}`)) return 1
  const info = index.infoText[idx] ?? (index.infoText[idx] = wordText(infoWords(index.data[idx])))
  if (inBio.test(info)) return 2
  if (info.includes(` ${word}`)) return 3
  return name.includes(word) ? 4 : 5
}

/** For "whole words only": 0 = a whole word of the name, 1 = a whole word of the bio, -1 = neither */
function wholeWordRank(index: SoldierIndex, idx: number, word: string): number {
  const name = index.nameText[idx] ?? (index.nameText[idx] = wordText(nameWords(index.data[idx])))
  if (name.includes(` ${word} `)) return 0
  const info = index.infoText[idx] ?? (index.infoText[idx] = wordText(infoWords(index.data[idx])))
  return info.includes(` ${word} `) ? 1 : -1
}

type Hit = { idx: number; rank: number; score: number }

function toHits(results: Hit[]): SearchHits {
  results.sort((a, b) => a.rank - b.rank || a.score - b.score || a.idx - b.idx)
  const hits = {
    idx: new Int32Array(results.length),
    rank: new Int32Array(results.length),
    score: new Float64Array(results.length),
  }
  results.forEach((r, i) => {
    hits.idx[i] = r.idx
    hits.rank[i] = r.rank
    hits.score[i] = r.score
  })
  return hits
}

/** Soldiers whose name or bio has every query word as a whole word, name matches first, in data order */
function searchWholeWords(index: SoldierIndex, words: string[]): SearchHits {
  const results: Hit[] = []
  for (let idx = 0; idx < index.data.length; idx++) {
    let rank = 0
    for (const word of words) {
      const r = wholeWordRank(index, idx, word)
      if (r < 0) { rank = -1; break }
      rank += r
    }
    if (rank >= 0) results.push({ idx, rank, score: 0 })
  }
  return toHits(results)
}

export function createSoldierIndex(data: SearchFields[]): SoldierIndex {
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
 *
 * A soldier's rank and score depend on him alone, so searching slices of the
 * list and merging the hits by (rank, score, position) gives the same order.
 */
export function searchSoldiers(index: SoldierIndex, query: string, wholeWords = false): SearchHits {
  const { data, unitMembers, unitOf } = index
  const words = query.toLowerCase().split(NON_WORD).filter(Boolean)
  if (wholeWords) return searchWholeWords(index, words)
  const queryWords = words.map(queryWord)
  const rankOf = (idx: number) =>
    queryWords.reduce((sum, word) => sum + wordRank(index, idx, word), 0)

  // 0 = no match; a unit factor is always > 0
  const unitFactor = new Float64Array(unitMembers.length)
  for (const hit of index.units.search(query)) {
    unitFactor[hit.refIndex] = hit.score!
  }

  const results: Hit[] = []
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
  return toHits(results)
}

/** Hits of consecutive slices of a list (each with the position its slice starts at) as one list's positions, in order */
export function mergeHits(slices: { hits: SearchHits; start: number }[]): Int32Array {
  const at = slices.map(() => 0)
  const merged = new Int32Array(slices.reduce((n, s) => n + s.hits.idx.length, 0))
  for (let k = 0; k < merged.length; k++) {
    let best = -1
    for (let s = 0; s < slices.length; s++) {
      if (at[s] === slices[s].hits.idx.length) continue
      if (best < 0) { best = s; continue }
      const a = slices[s].hits, i = at[s], b = slices[best].hits, j = at[best]
      // Equal rank and score: the earlier slice's soldier comes first, as in a single list
      if (a.rank[i] < b.rank[j] || (a.rank[i] === b.rank[j] && a.score[i] < b.score[j])) best = s
    }
    merged[k] = slices[best].start + slices[best].hits.idx[at[best]++]
  }
  return merged
}
