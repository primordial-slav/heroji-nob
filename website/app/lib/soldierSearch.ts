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
  /** The words of each unit's name, folded as wordText folds them */
  unitWords: Set<string>[]
  /** Position of each soldier's unit in unitWords, -1 if none */
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
  const unitOf = new Int32Array(data.length).fill(-1)
  data.forEach((soldier, i) => {
    if (!soldier.unit) return
    let pos = unitPos.get(soldier.unit)
    if (pos === undefined) {
      pos = unitPos.size
      unitPos.set(soldier.unit, pos)
    }
    unitOf[i] = pos
  })
  return {
    data,
    soldiers: new Fuse(data, SOLDIER_FUSE_OPTIONS),
    unitWords: Array.from(unitPos.keys(), (unit) => new Set(wordText(unit).trim().split(' '))),
    unitOf,
    nameText: new Array(data.length),
    infoText: new Array(data.length),
  }
}

// A hit where some query word is only inside a name word or only fuzzily matched (wordRank 4 or 5) ranks this much
// lower; mergeHits drops such hits when any hit matches every word properly. "Ana" otherwise found every bio with
// "Ivana" or "bataljona", and "Petrović" every "Kalauzović".
const LOOSE = 1000
// A soldier found through his unit's name ranks after those whose own words match and before the loose ones
const UNIT_HIT = 500
// A query word that names a kind of unit by itself: "kozaračka", "lička", "užički", "proleterska"
const UNIT_WORD = /^[a-z]{3,}(?:sk|ck|nsk)[aieo]$/

/**
 * The units a query names: every query word a whole word of the unit's name, and the query a unit's name rather
 * than a person's: a number ("13. proleterska"), two words or more ("Rade Končar", "Prva lička"), or a word that
 * names a kind of unit ("Kozaračka"). "Rade", "Marko" or "Ana" alone name no unit, though "Rade Končar" and "Marko
 * Orešković" are brigades' honorary names (and "Ana" is inside "Banijska").
 */
function unitsNamed(index: SoldierIndex, words: string[]): boolean[] {
  const named = words.length >= 2 || words.some((w) => /\d/.test(w)) || (words.length === 1 && UNIT_WORD.test(words[0]))
  return index.unitWords.map((unitWords) => named && words.every((w) => unitWords.has(w)))
}

/**
 * The soldiers a query finds, best word matches first.
 *
 * A soldier is found when each query word is a word of his names or his bio, or the start of one (wordRank 0 to
 * 3), whatever the order of the words: "Marko Petrović" and "Petrović Marko" find the same people. The hits are
 * sorted by the sum of each word's wordRank (Fuse's own scores mix fields, so for "rolic" Korolić Stojan came
 * before Rolić Vojislava Milomir), then in the list's order. The soldiers of a unit the query names
 * (unitsNamed) are found too, at UNIT_HIT unless their own words match better.
 *
 * Only when no soldier matches every word (a misspelled name) are Fuse's fuzzy hits shown, LOOSE lower, in
 * Fuse's order within the same sum; mergeHits leaves them out when another slice has proper hits.
 *
 * A soldier's rank and score depend on him alone, so searching slices of the list and merging the hits by
 * (rank, score, position) gives the same order.
 */
export function searchSoldiers(index: SoldierIndex, query: string, wholeWords = false): SearchHits {
  const { data, unitOf } = index
  const words = query.toLowerCase().split(NON_WORD).filter(Boolean)
  if (!words.length) return toHits([])
  if (wholeWords) return searchWholeWords(index, words)
  const queryWords = words.map(queryWord)
  const rankOf = (idx: number) => {
    let sum = 0
    let loose = false
    for (const word of queryWords) {
      const r = wordRank(index, idx, word)
      sum += r
      if (r >= 4) loose = true
    }
    return loose ? sum + LOOSE : sum
  }
  const named = unitsNamed(index, words)

  const results: Hit[] = []
  for (let idx = 0; idx < data.length; idx++) {
    const rank = rankOf(idx)
    if (rank < LOOSE) results.push({ idx, rank, score: 0 })
    else if (unitOf[idx] >= 0 && named[unitOf[idx]]) results.push({ idx, rank: UNIT_HIT, score: 0 })
  }
  if (results.length) return toHits(results)

  for (const { refIndex: idx, score } of index.soldiers.search(query)) {
    results.push({ idx, rank: rankOf(idx), score: score! })
  }
  return toHits(results)
}

/**
 * Hits of consecutive slices of a list (each with the position its slice starts at) as one list's positions, in
 * order. When the best hit matches every query word properly, the loose hits (rank LOOSE and over) are left out:
 * they only matter when nothing else is found (a misspelled name). Decided here, over all the slices.
 */
export function mergeHits(slices: { hits: SearchHits; start: number }[]): Int32Array {
  const at = slices.map(() => 0)
  const merged = new Int32Array(slices.reduce((n, s) => n + s.hits.idx.length, 0))
  let looseOnly = false
  for (let k = 0; k < merged.length; k++) {
    let best = -1
    for (let s = 0; s < slices.length; s++) {
      if (at[s] === slices[s].hits.idx.length) continue
      if (best < 0) { best = s; continue }
      const a = slices[s].hits, i = at[s], b = slices[best].hits, j = at[best]
      // Equal rank and score: the earlier slice's soldier comes first, as in a single list
      if (a.rank[i] < b.rank[j] || (a.rank[i] === b.rank[j] && a.score[i] < b.score[j])) best = s
    }
    const rank = slices[best].hits.rank[at[best]]
    if (k === 0) looseOnly = rank >= LOOSE
    else if (rank >= LOOSE && !looseOnly) return merged.slice(0, k)
    merged[k] = slices[best].start + slices[best].hits.idx[at[best]++]
  }
  return merged
}
