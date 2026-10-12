import { normalizeForSearch } from './diacritics'
import type { Soldier } from './types'

// The search itself, without React. useFuseSearch runs it off the page's thread, in search.worker.ts, each worker
// on a slice of the soldiers, and merges the slices' hits (mergeHits).
//
// Each word typed is looked up on its own among the words of each soldier: his surname, given name, nickname,
// father (as printed, "Krste", and in the nominative, "Krsto"), the names other books print for him, his birth
// year, his entry and his unit. A soldier's score adds up what each word typed is worth for him, and what a word
// is worth depends first on how it matches, then on where:
//
//   how:   the whole word, 1  >  another case of it ("Krsto" for "Krste", "Divoš" for "u Divošu"; father and entry
//          only), 0.92  >  a letter the scans misread ("Jeiić"), 0.7  >  the start of a word, 0.55  >  a typo, 0.45
//          (two in a long word, 0.3)  >  inside another word ("Bijelić" for "Jelić"), 0.05
//   where: surname 1  >  given name 0.9  >  nickname 0.85  >  father 0.75  >  the unit's name (when it has every
//          word typed) 0.65  >  birth year, entry 0.6 (a word of three letters 0.45, of two 0.3)
//
// So a typo in a name is worth less than the whole word in the entry, "Kikinda" lists the soldiers from Kikinda
// before Kikinđanin, and "Jelić Krste Milun", whom no book prints, lists the Jelićs, sons of Krsto, before Tadić
// Krste Milun. A word typed alone counts as much as a given name as as a surname, unless it looks like a surname
// (-ić, -ski, -ov): "Jelica" lists the women named Jelica among the Jelicas. Soldiers who score the same are
// listed alphabetically: surname, given name, father.
//
// Which soldiers are listed at all depends on how many of the words typed they match (a word found only inside
// another counts as not found): those who match the most of them, all if anyone does. Of three words or more,
// those who match all but one come after those who match all ("Petar Jelić Vrpolje": then the Petar Jelićs whose
// entry names no place, and the Jelićs from Vrpolje). Short words a query may hold ("u", "iz", "sin") count only
// where they match.
//
// The list comes in two parts: first the soldiers in whose name or entry every word typed is, as typed (the whole
// word, another case of it, or misread by the scan), then the similar ones (a word only the start of one of theirs,
// a typo, a word missing), which the page shows under "Slični zapisi".
//
// A unit's soldiers match when every word typed is in the unit's name ("13. proleterska", "Kozaračka"), not in the
// name of the person it is named after: "Marko" does not list all of Prva lička brigada „Marko Orešković“.

/** What search reads of a soldier: a worker is sent only this */
export interface SearchFields {
  last_name: string
  middle_name: string
  first_name: string
  /** The father in the nominative, where the book prints him in another case */
  fathers_name?: string
  additional_info: string
  birth_year: string
  unit?: string
  other_sources?: { name?: string; additional_info: string }[]
}

export function searchFields(soldier: Soldier): SearchFields {
  return {
    last_name: soldier.last_name,
    middle_name: soldier.middle_name,
    first_name: soldier.first_name,
    fathers_name: soldier.fathers_name && soldier.fathers_name !== soldier.middle_name ? soldier.fathers_name : undefined,
    additional_info: soldier.additional_info,
    birth_year: soldier.birth_year,
    unit: soldier.unit,
    other_sources: soldier.other_sources?.map((o) => ({ name: o.name, additional_info: o.additional_info })),
  }
}

const NON_WORD = /[^a-z0-9À-ɏ]+/
const NON_WORD_CASED = /[^A-Za-z0-9À-ɏ]+/

/** "Rolić Vojislava Milomir" -> ["rolic", "vojislava", "milomir"] */
function words(text: string | undefined): string[] {
  if (!text) return []
  return normalizeForSearch(text).toLowerCase().split(NON_WORD).filter(Boolean)
}

/** An entry's words, each with whether it starts with a capital: "u Gračacu" -> ["u", false], ["gracacu", true] */
function entryTokens(text: string | undefined): [string, boolean][] {
  if (!text) return []
  return normalizeForSearch(text).split(NON_WORD_CASED).filter(Boolean)
    .map((word) => [word.toLowerCase(), word[0] !== word[0].toLowerCase()])
}

// Where a word of the soldier's is. A word of a surname or given name of several ("Budimir-Jelić") is worth a
// little less than the whole of one, so the Jelićs come before the Budimir-Jelićs
const SURNAME = 0, GIVEN = 1, NICK = 2, FATHER = 3, YEAR = 4, SURNAME_PART = 5, GIVEN_PART = 6
const WHERE = [1, 0.9, 0.85, 0.75, 0.6, 0.9, 0.8]
// A word typed alone that doesn't look like a surname: a surname counts no more than a given name
const AS_GIVEN = WHERE.map((w, role) => (role === SURNAME ? WHERE[GIVEN] : role === SURNAME_PART ? WHERE[GIVEN_PART] : w))
const SURNAME_LIKE = /(ic|ski|ska|cki|cka|ov|ev)$/
const IN_ENTRY = 0.6
const SHORT_IN_ENTRY = 0.45 // three letters
const TINY_IN_ENTRY = 0.3 // two letters, or one or two digits
const IN_UNIT = 0.65

// How a word typed matches one of the soldier's
const WHOLE = 1
const FORM = 0.92
const START = [0, 0.4, 0.45, 0.55] // by the letters typed: one, two, three or more
const MISREAD = 0.7
const TYPO = 0.45
const TWO_TYPOS = 0.3
const INSIDE = 0.05
/** A word typed counts as found from a match worth this much: everything but INSIDE */
const FOUND = 0.1

// The name a bio gives as "zvani Muta" / "zvana Mica": families often know a soldier only by it
const NICKNAME = /\bzvan[aio]\s+[„"»]?([A-ZČĆŽŠĐ][a-zčćžšđ'-]+)/g

function nicknames(soldier: SearchFields): string[] {
  const bios = [soldier.additional_info, ...(soldier.other_sources ?? []).map((o) => o.additional_info)]
  const found: string[] = []
  for (const bio of bios) {
    for (const m of (bio ?? '').matchAll(NICKNAME)) found.push(m[1])
  }
  return found
}

// Words a query may hold that say nothing of the soldier: they count only where they match, for a tenth
const MINOR = new Set(['i', 'u', 'iz', 'od', 'do', 'na', 'kod', 'sa', 's', 'za', 'v', 'pri', 'in', 'sin', 'kci', 'roden', 'rodena', 'r'])
const MINOR_WORTH = 0.1

// Case endings of nouns and adjectives, folded: "u Gračacu", "iz Divosela", "v Trbovljah"
const ENDINGS = ['a', 'e', 'i', 'o', 'u', 'om', 'em', 'im', 'ih', 'oj', 'og', 'ah', 'ama', 'ima', 'oga', 'ega', 'omu', 'emu']
// A father as the books print him: "Milunov", "Krstin"
const FATHER_ENDINGS = ['ov', 'ev', 'in', 'ova', 'eva', 'ina']
const SOFTENED: Record<string, string> = { k: 'c', g: 'z', h: 's' }

/**
 * The other cases of a word: "krsto" -> krste, krsta, krstom...; "petar" -> petra; "gracac" -> gracca, gracacu;
 * "rijeka" -> rijeci. Not the word itself.
 */
function forms(word: string, father: boolean): Set<string> {
  const stems = [word]
  if (word.length >= 4 && /[aeiou]$/.test(word)) stems.push(word.slice(0, -1))
  const base = stems[stems.length - 1]
  // A vowel that drops in the other cases (Petar, Petra; Đurađ, Đurđa; Gračac, Gračca), and comes back
  if (base.length >= 4 && /[^aeiou]a[^aeiou]$/.test(base)) stems.push(base.slice(0, -2) + base.slice(-1))
  if (base.length >= 4 && /[aeiou][^aeiou][^aeiou]$/.test(base) && !/(lj|nj|dz|st|sk|sl|zd|ck)$/.test(base)) stems.push(base.slice(0, -1) + 'a' + base.slice(-1))
  const out = new Set<string>()
  for (const stem of stems) {
    out.add(stem)
    for (const e of ENDINGS) out.add(stem + e)
    if (father) for (const e of FATHER_ENDINGS) out.add(stem + e)
  }
  const soft = /^(.{2,})([kgh])a$/.exec(word)
  if (soft) out.add(soft[1] + SOFTENED[soft[2]] + 'i')
  out.delete(word)
  return out
}

// Letters the scans' text layers take for one another, folded: such a swap costs less than a typo
const MISREADINGS = new Set(['li', 'il', 'lt', 'tl', 'ij', 'ji', 'ce', 'ec', 'nu', 'un', 'hb', 'bh', 'l1', '1l', 'i1', '1i', 'o0', '0o', 'b3', '3b', 's5', '5s'])
const MISREAD_COST = 0.4
// One letter read as two, or two as one
const SPLIT_READINGS: Record<string, string[]> = { m: ['rn', 'ni', 'in'], u: ['ii', 'li', 'il'], d: ['cl'], w: ['vv'] }

// The three rows distance() works on, kept between calls
let rows = [new Float64Array(32), new Float64Array(32), new Float64Array(32)]

/**
 * How far apart two words are: a typo (a letter left out, added, wrong, or two swapped) costs 1, a misreading
 * MISREAD_COST. Stops counting past `max`, returning max + 1.
 */
function distance(a: string, b: string, max: number): number {
  const n = a.length, m = b.length
  if (Math.abs(n - m) > max + 1) return max + 1
  if (rows[0].length <= m) rows = rows.map(() => new Float64Array(m + 1))
  let [prev2, prev, row] = rows
  for (let j = 0; j <= m; j++) prev[j] = j
  for (let i = 1; i <= n; i++) {
    row[0] = i
    let low = i
    const ca = a[i - 1]
    for (let j = 1; j <= m; j++) {
      const cb = b[j - 1]
      const sub = ca === cb ? 0 : MISREADINGS.has(ca + cb) ? MISREAD_COST : 1
      let d = Math.min(prev[j] + 1, row[j - 1] + 1, prev[j - 1] + sub)
      if (i > 1 && j > 1) {
        if (ca === b[j - 2] && a[i - 2] === cb) d = Math.min(d, prev2[j - 2] + 1)
        // "rn" in one word for "m" in the other
        if (SPLIT_READINGS[ca]?.includes(b.slice(j - 2, j))) d = Math.min(d, prev[j - 2] + MISREAD_COST)
        if (SPLIT_READINGS[cb]?.includes(a.slice(i - 2, i))) d = Math.min(d, prev2[j - 1] + MISREAD_COST)
      }
      row[j] = d
      if (d < low) low = d
    }
    if (low > max) return max + 1
    const done = prev2
    prev2 = prev
    prev = row
    row = done
  }
  return prev[m]
}

/** How much a typed word may differ from a soldier's word, by its length */
const allowed = (word: string) => (/\d/.test(word) ? 0 : word.length <= 3 ? MISREAD_COST : word.length <= 7 ? 1 : 2)

/** What a word is worth that differs by `d` */
function closeness(d: number): number {
  if (d <= MISREAD_COST + 1e-9) return MISREAD
  if (d <= 1 + 1e-9) return TYPO
  return TWO_TYPOS
}

// The order results are listed in when they match alike, as numbers a worker can compute for its slice alone:
// Serbo-Croatian alphabetical order of the surname, then of the given name and father, ten letters each
const ALPHABET = ' abcčćdđefghijklmnopqrsštuvwxyzž'
const LETTER = new Map([...ALPHABET].map((ch, i) => [ch, i]))

function alphabetical(text: string): number {
  let key = 0, n = 0
  for (const ch of text.toLowerCase()) {
    if (n === 10) break
    let d = LETTER.get(ch)
    if (d === undefined) d = LETTER.get(ch.normalize('NFD')[0])
    if (d === undefined) continue
    key = key * 32 + d
    n++
  }
  for (; n < 10; n++) key *= 32
  return key
}

export interface SoldierIndex {
  data: SearchFields[]
  /** Every word of the soldiers', and its number */
  ids: Map<string, number>
  words: string[]
  /** Who has each word in a name, as soldier * 8 + where: the word's postings are nameAt[id] .. nameAt[id + 1] */
  nameAt: Int32Array
  names: Int32Array
  /** Who has each word in an entry, as soldier * 2, + 1 where it starts with a capital */
  entryAt: Int32Array
  entries: Int32Array
  /** The words of names and of entries, in alphabetical order, for words typed in part */
  nameWords: Int32Array
  entryWords: Int32Array
  /** Each unit's words, the soldiers of each unit, and each soldier's unit (-1 if none) */
  unitWords: string[][]
  unitMembers: number[][]
  unitOf: Int32Array
}

/** Search results as positions in the searched list, best first, with what they are ordered by */
export interface SearchHits {
  idx: Int32Array
  /** How many of the words typed the soldier does not match */
  missed: Int32Array
  /** 1 for a similar soldier, listed after those who have every word as typed */
  near: Uint8Array
  /** Lower is better: minus what the words typed are worth for the soldier */
  score: Float64Array
  /** Alphabetical order of the surname, then of the rest of the name */
  key: Float64Array
  key2: Float64Array
  /** How many words typed count (minor words left out) */
  terms: number
}

/** Posting lists from per-word arrays */
function packed(lists: number[][]): [Int32Array, Int32Array] {
  const at = new Int32Array(lists.length + 1)
  for (let w = 0; w < lists.length; w++) at[w + 1] = at[w] + lists[w].length
  const all = new Int32Array(at[lists.length])
  for (let w = 0; w < lists.length; w++) all.set(lists[w], at[w])
  return [at, all]
}

// The name of the person a unit is named after: „Rade Končar“. One word is the unit's own name: "Ljubljanska"
const HONORARY = /[„"][^„"“”]* [^„"“”]*[“”"]/g

export function createSoldierIndex(data: SearchFields[]): SoldierIndex {
  const ids = new Map<string, number>()
  const words_: string[] = []
  const nameLists: number[][] = []
  const entryLists: number[][] = []
  // The last soldier who got each word in a name with each role, and in an entry, so each is listed once
  const lastName: number[] = []
  const lastEntry: number[] = []
  const id = (word: string) => {
    let w = ids.get(word)
    if (w === undefined) {
      w = words_.push(word) - 1
      ids.set(word, w)
      nameLists.push([])
      entryLists.push([])
      lastName.push(-1)
      lastEntry.push(-1)
    }
    return w
  }
  const unitPos = new Map<string, number>()
  const unitWords: string[][] = []
  const unitMembers: number[][] = []
  const unitOf = new Int32Array(data.length).fill(-1)

  data.forEach((soldier, i) => {
    const name = (word: string, role: number) => {
      const w = id(word)
      const posting = i * 8 + role
      if (lastName[w] === posting) return
      lastName[w] = posting
      nameLists[w].push(posting)
    }
    const surname = words(soldier.last_name), given = words(soldier.first_name)
    for (const word of surname) name(word, surname.length > 1 ? SURNAME_PART : SURNAME)
    for (const word of given) name(word, given.length > 1 ? GIVEN_PART : GIVEN)
    for (const word of words(soldier.middle_name)) name(word, FATHER)
    for (const word of words(soldier.fathers_name)) name(word, FATHER)
    for (const nick of nicknames(soldier)) for (const word of words(nick)) name(word, NICK)
    // Other books print "Surname Father Given"
    for (const source of soldier.other_sources ?? []) {
      const parts = (source.name ?? '').split(/\s+/).map(words).filter((part) => part.length)
      parts.forEach((part, k) => {
        const role = k === 0 ? (part.length > 1 ? SURNAME_PART : SURNAME) : k === parts.length - 1 ? (part.length > 1 ? GIVEN_PART : GIVEN) : FATHER
        for (const word of part) name(word, role)
      })
    }
    for (const word of words(soldier.birth_year)) name(word, YEAR)
    for (const bio of [soldier.additional_info, ...(soldier.other_sources ?? []).map((o) => o.additional_info)]) {
      for (const [word, capital] of entryTokens(bio)) {
        const w = id(word)
        const posting = i * 2 + (capital ? 1 : 0)
        if (lastEntry[w] === posting || lastEntry[w] === i * 2 + 1) continue
        lastEntry[w] = posting
        entryLists[w].push(posting)
      }
    }
    if (soldier.unit) {
      let pos = unitPos.get(soldier.unit)
      if (pos === undefined) {
        pos = unitMembers.push([]) - 1
        unitPos.set(soldier.unit, pos)
        unitWords.push(words(soldier.unit.replace(HONORARY, ' ')))
      }
      unitMembers[pos].push(i)
      unitOf[i] = pos
    }
  })

  const [nameAt, names] = packed(nameLists)
  const [entryAt, entries] = packed(entryLists)
  const byWord = (a: number, b: number) => (words_[a] < words_[b] ? -1 : words_[a] > words_[b] ? 1 : 0)
  const nameWords = Int32Array.from(words_.keys()).filter((w) => nameAt[w + 1] > nameAt[w]).sort(byWord)
  const entryWords = Int32Array.from(words_.keys()).filter((w) => entryAt[w + 1] > entryAt[w]).sort(byWord)
  return { data, ids, words: words_, nameAt, names, entryAt, entries, nameWords, entryWords, unitWords, unitMembers, unitOf }
}

/** The words of `sorted` that start with `start` (but are not it), with what each is worth */
function startingWith(index: SoldierIndex, sorted: Int32Array, start: string, worth: number, out: Map<number, number>) {
  let lo = 0, hi = sorted.length
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (index.words[sorted[mid]] < start) lo = mid + 1
    else hi = mid
  }
  for (let k = lo; k < sorted.length; k++) {
    const word = index.words[sorted[k]]
    if (!word.startsWith(start)) break
    if (word !== start) keep(out, sorted[k], worth)
  }
}

function keep(out: Map<number, number>, w: number, worth: number) {
  if (worth > (out.get(w) ?? 0)) out.set(w, worth)
}

// Which part of the name a typed word's best match is in, for the order of the words typed: 0 none
const PART_OF = [1, 3, 3, 2, 0, 1, 3] // surname, given name, nickname, father, year, part of a surname, of a given name

/** Best match per soldier for one typed word, with the soldiers it touched */
interface WordMatch {
  worth: Float32Array
  /** In which part of the name the best match is (PART_OF) */
  part: Uint8Array
  /** 1 where the word is in the soldier's name or entry as typed: the whole word, another case of it, or misread */
  asTyped: Uint8Array
  touched: number[]
  /** What it is worth for each unit's soldiers, and whether it is a whole word of the unit's name */
  units: Float32Array
  unitsAsTyped: Uint8Array
}

function matchWord(index: SoldierIndex, typed: string, wholeOnly: boolean, alone: boolean): WordMatch {
  const { ids, words: vocab, nameAt, names, entryAt, entries } = index
  const worth = new Float32Array(index.data.length)
  const part = new Uint8Array(index.data.length)
  const asTyped = new Uint8Array(index.data.length)
  const touched: number[] = []
  const give = (i: number, value: number, of: number, how: number) => {
    if (worth[i] === 0) touched.push(i)
    if (value > worth[i]) {
      worth[i] = value
      part[i] = of
    }
    if (how >= MISREAD) asTyped[i] = 1
  }
  const numeric = /^\d+$/.test(typed)
  const exact = ids.get(typed)
  // A word typed alone counts for more as a surname than as a given name only when it looks like a surname:
  // "Jelić" lists the Jelićs first, "Branko" the Brankos, wherever the book prints the name
  const where = alone && !SURNAME_LIKE.test(typed) ? AS_GIVEN : WHERE

  // Names: what each matching word is worth, and what it is worth as a father (another case counts there)
  const inName = new Map<number, number>()
  const asFather = new Map<number, number>()
  if (exact !== undefined) inName.set(exact, WHOLE)
  if (!wholeOnly) {
    // Another case of a word of three letters is most often only the start of a longer one: "Mil", "Mile"
    if (!numeric && typed.length >= 4) {
      for (const form of forms(typed, true)) {
        const w = ids.get(form)
        if (w !== undefined) asFather.set(w, FORM)
      }
    }
    startingWith(index, index.nameWords, typed, START[Math.min(typed.length, 3)], inName)
    const max = allowed(typed)
    for (const w of index.nameWords) {
      const word = vocab[w]
      if (max > 0 && Math.abs(word.length - typed.length) <= max) {
        const d = distance(typed, word, max)
        if (d > 0 && d <= max) keep(inName, w, closeness(d))
      }
      if (typed.length >= 4 && word.length > typed.length && word.indexOf(typed, 1) > 0) keep(inName, w, INSIDE)
    }
  }
  const credit = (w: number, value: number, father: number) => {
    for (let p = nameAt[w]; p < nameAt[w + 1]; p++) {
      const role = names[p] & 7
      const how = role === FATHER ? Math.max(value, father) : value
      if (how > 0) give(names[p] >> 3, how * where[role], PART_OF[role], how)
    }
  }
  for (const [w, value] of inName) credit(w, value, asFather.get(w) ?? 0)
  for (const [w, father] of asFather) if (!inName.has(w)) credit(w, 0, father)

  // Entries: places, years, duties. A short word there is often an abbreviation or a day ("jel.", "st.", "13."),
  // so it counts for less than a name that starts with it; one letter is not looked for
  if (typed.length >= 2) {
    const inEntryWorth = typed.length >= 4 || (numeric && typed.length === 4) ? IN_ENTRY : typed.length === 3 ? SHORT_IN_ENTRY : TINY_IN_ENTRY
    const inEntry = new Map<number, number>()
    // Another case counts in an entry only for a word with a capital, a place or a name: "u Gračacu", not "u radu"
    // for "Rade"
    const asPlace = new Map<number, number>()
    if (exact !== undefined) inEntry.set(exact, WHOLE)
    if (!wholeOnly) {
      if (!numeric && typed.length >= 4) {
        for (const form of forms(typed, false)) {
          const w = ids.get(form)
          if (w !== undefined) asPlace.set(w, FORM)
        }
      }
      if (!numeric && typed.length >= 3) startingWith(index, index.entryWords, typed, START[3], inEntry)
      if (numeric && typed.length >= 3) startingWith(index, index.entryWords, typed, START[3], inEntry)
      if (!numeric && typed.length >= 5) {
        for (const w of index.entryWords) {
          const word = vocab[w]
          if (Math.abs(word.length - typed.length) > 1) continue
          const d = distance(typed, word, 1)
          if (d > 0 && d <= 1) keep(inEntry, w, closeness(d))
        }
      }
    }
    for (const [w, value] of inEntry) {
      for (let p = entryAt[w]; p < entryAt[w + 1]; p++) give(entries[p] >> 1, value * inEntryWorth, 0, value)
    }
    for (const [w, value] of asPlace) {
      for (let p = entryAt[w]; p < entryAt[w + 1]; p++) if (entries[p] & 1) give(entries[p] >> 1, value * inEntryWorth, 0, value)
    }
  }

  // Units: "proleterska", "13."
  const units = new Float32Array(index.unitWords.length)
  const unitsAsTyped = new Uint8Array(index.unitWords.length)
  index.unitWords.forEach((unitWords, pos) => {
    let best = 0
    for (const word of unitWords) {
      if (word === typed) best = WHOLE
      else if (!wholeOnly && typed.length >= 3 && word.startsWith(typed)) best = Math.max(best, START[3])
      else if (!wholeOnly && typed.length >= 5) {
        const d = distance(typed, word, 1)
        if (d <= 1) best = Math.max(best, closeness(d))
      }
    }
    units[pos] = best * IN_UNIT
    unitsAsTyped[pos] = best === WHOLE ? 1 : 0
  })
  return { worth, part, asTyped, touched, units, unitsAsTyped }
}

// Names typed in the books' order (surname, father, given name) or the spoken one (given name, father, surname)
// come before the same words in other parts of the name: "Stanišić Savo Lazo" is Lazo, son of Savo
const IN_ORDER = 0.01

function inOrder(parts: number[]): boolean {
  let up = true, down = true
  for (let k = 1; k < parts.length; k++) {
    if (parts[k] < parts[k - 1]) up = false
    if (parts[k] > parts[k - 1]) down = false
  }
  return up || down
}

/**
 * The soldiers that match the words of `query` (normalized as normalizeForSearch does), best first. A slice's
 * results carry all that mergeHits needs to list them with the other slices' as one list's.
 */
export function searchSoldiers(index: SoldierIndex, query: string, wholeWords = false): SearchHits {
  const typed = words(query)
  const major = typed.filter((word) => !MINOR.has(word))
  const counted = major.length ? major : typed
  const minor = major.length ? typed.filter((word) => MINOR.has(word)) : []
  const matches = counted.map((word) => matchWord(index, word, wholeWords, counted.length === 1))
  const extras = minor.map((word) => matchWord(index, word, true, false))

  // The units whose name has every word typed
  const named = index.unitWords.map((_, pos) => matches.every((match) => match.units[pos] > 0))

  // Everyone a word found, and the soldiers of those units
  const seen = new Uint8Array(index.data.length)
  const candidates: number[] = []
  const consider = (i: number) => {
    if (!seen[i]) {
      seen[i] = 1
      candidates.push(i)
    }
  }
  for (const match of matches) match.touched.forEach(consider)
  named.forEach((all, pos) => all && index.unitMembers[pos].forEach(consider))

  const found: { i: number; missed: number; near: number; worth: number }[] = []
  const parts: number[] = []
  for (const i of candidates) {
    let worth = 0, missed = 0, near = 0
    const unit = index.unitOf[i]
    const inNamed = unit >= 0 && named[unit]
    parts.length = 0
    for (const match of matches) {
      const inUnit = inNamed ? match.units[unit] : 0
      const value = Math.max(match.worth[i], inUnit)
      worth += value
      if (value < FOUND) missed++
      else if (match.worth[i] >= inUnit && match.part[i]) parts.push(match.part[i])
      if (!match.asTyped[i] && !(inNamed && match.unitsAsTyped[unit])) near = 1
    }
    if (missed === counted.length) continue
    if (wholeWords && missed > 0) continue
    if (parts.length > 1 && inOrder(parts)) worth += IN_ORDER
    for (const extra of extras) worth += extra.worth[i] * MINOR_WORTH
    found.push({ i, missed, near, worth: Math.round(worth * 1e6) / 1e6 })
  }

  const key = new Float64Array(found.length), key2 = new Float64Array(found.length)
  const order = found.map((hit, k) => {
    const s = index.data[hit.i]
    key[k] = alphabetical(s.last_name ?? '')
    key2[k] = alphabetical(`${s.first_name ?? ''} ${s.middle_name ?? ''}`)
    return k
  })
  order.sort((a, b) =>
    found[a].near - found[b].near || found[b].worth - found[a].worth || key[a] - key[b] || key2[a] - key2[b] || found[a].i - found[b].i)
  const hits: SearchHits = {
    idx: new Int32Array(found.length),
    missed: new Int32Array(found.length),
    near: new Uint8Array(found.length),
    score: new Float64Array(found.length),
    key: new Float64Array(found.length),
    key2: new Float64Array(found.length),
    terms: counted.length,
  }
  order.forEach((k, n) => {
    hits.idx[n] = found[k].i
    hits.missed[n] = found[k].missed
    hits.near[n] = found[k].near
    hits.score[n] = -found[k].worth
    hits.key[n] = key[k]
    hits.key2[n] = key2[k]
  })
  return hits
}

/** A search's results as positions in the searched list, best first; the similar ones from `nearFrom` on */
export interface MergedHits {
  positions: Int32Array
  nearFrom: number
}

/**
 * Hits of consecutive slices of a list (each with the position its slice starts at) as one list's. Who is listed
 * depends on all slices: those who match the most of the words typed, and of three words or more, if anyone
 * matches all, also those who miss one.
 */
export function mergeHits(slices: { hits: SearchHits; start: number }[]): MergedHits {
  let fewest = Infinity
  for (const { hits } of slices) for (let k = 0; k < hits.missed.length; k++) fewest = Math.min(fewest, hits.missed[k])
  const terms = slices[0]?.hits.terms ?? 0
  const allowedMisses = terms >= 3 && fewest === 0 ? 1 : fewest
  const at = slices.map(() => 0)
  const next = (s: number) => {
    const { hits } = slices[s]
    while (at[s] < hits.idx.length && hits.missed[at[s]] > allowedMisses) at[s]++
    return at[s] < hits.idx.length
  }
  const merged: number[] = []
  let nearFrom = -1
  for (;;) {
    let best = -1
    for (let s = 0; s < slices.length; s++) {
      if (!next(s)) continue
      if (best < 0) { best = s; continue }
      const a = slices[s].hits, i = at[s], b = slices[best].hits, j = at[best]
      // Alike: the earlier slice's soldier comes first, as in a single list
      if (a.near[i] !== b.near[j] ? a.near[i] < b.near[j]
        : a.score[i] < b.score[j] || (a.score[i] === b.score[j] && (a.key[i] < b.key[j] || (a.key[i] === b.key[j] && a.key2[i] < b.key2[j])))) best = s
    }
    if (best < 0) break
    if (nearFrom < 0 && slices[best].hits.near[at[best]]) nearFrom = merged.length
    merged.push(slices[best].start + slices[best].hits.idx[at[best]++])
  }
  return { positions: Int32Array.from(merged), nearFrom: nearFrom < 0 ? merged.length : nearFrom }
}
