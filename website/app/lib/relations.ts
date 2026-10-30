import type { Soldier } from './types'
import { parseDeathDay } from './deathDay'
import { placesChunkPath, placesOfPath } from './dataFiles'

// ── Sub-units ────────────────────────────────────────────────
// unit_detail is printed "2. četa, 1. bataljon", "VI bataljon", "1. vod, 2. četa, 3. bataljon", "prištapske jedinice",
// "3. kordunaški bataljon", "1. bataljon, mitraljeska četa". A record's sub-unit is the path from the battalion down.

export interface Level {
  key: string    // stable within a unit: "b1", "c2", "s:prištapske jedinice"
  label: string  // in Serbo-Croatian: "1. bataljon", "2. četa"; a named one as printed: "3. kordunaški bataljon"
  // A plain numbered level, the staff units' node and the node for records without a battalion are the site's
  // own words, which each language says its own way (RelationsTree); a named one is shown as printed
  kind?: 'battalion' | 'company' | 'platoon' | 'squad' | 'staff' | 'none'
  n?: number
}

const ROMAN: Record<string, number> = { i: 1, ii: 2, iii: 3, iv: 4, v: 5, vi: 6, vii: 7, viii: 8, ix: 9, x: 10, xi: 11, xii: 12 }

function number(raw: string): string | null {
  const n = raw.replace(/\.$/, '').toLowerCase()
  if (/^\d+$/.test(n)) return String(parseInt(n, 10))
  return ROMAN[n] ? String(ROMAN[n]) : null
}

// A unit above the battalions, in a division's records or Borci drugih jedinica's: "3. bataljon, 18. srpska brigada",
// "brigada »Braća Radić«", "Turopoljsko-posavski partizanski odred", "422. vazduhoplovni puk". It heads the path, so
// a division's 3. bataljon is its brigade's, not every brigade's (2026-10-30: the 25. srpska divizija's "3. bataljon,
// 18. srpska brigada" counted 263 comrades, the 18.'s alone 88). Its key leaves out what the books print otherwise:
// quotes, "udarna", a Roman numeral ("I udarna zagorska brigada", "brigada »Braća Radić«", "Udarna brigada Braća Radić")
const HIGHER = /(?<!\p{L})(?:brigada|odred|puk)(?!\p{L})/iu
const STAFF_PART = /^(?:štab|prištap|komanda|politodjel|politodel)/iu

const ORDINAL: Record<string, number> = { prva: 1, druga: 2, treća: 3, četvrta: 4, peta: 5, šesta: 6, sedma: 7, osma: 8 }

function higherKey(part: string): string {
  const key = part.toLowerCase()
    .replace(/[»«„“”"']/g, '')
    .replace(/(?<!\p{L})(?:udarna|partizanski|nop|narodnooslobodilački)(?!\p{L})/gu, '')
    .replace(/^([ivx]+)\.?(?=\s)/, (m, r: string) => (ROMAN[r] ? `${ROMAN[r]}.` : m))
    .replace(/^(prva|druga|treća|četvrta|peta|šesta|sedma|osma)(?=\s)/u, (m, w: string) => `${ORDINAL[w]}.`)
    .replace(/\s+/g, ' ').trim()
  // a named brigade or an odred is one with its number or without: "16. omladinska brigada »Joža Vlahović«",
  // "2. Karlovački NOP odred" and "Karlovački partizanski odred"
  return /(?:brigada \p{L}|odred$)/u.test(key) ? key.replace(/^\d+\.\s/, '') : key
}

export function subunitPath(detail?: string): Level[] {
  if (!detail) return []
  let higher: Level | null = null
  let battalion: Level | null = null
  let company: Level | null = null
  let platoon: Level | null = null
  let squad: Level | null = null
  let group: Level | null = null   // brigade-level groups outside the battalions: "prištapske jedinice", "četa za vezu"
  const inBattalion = /bataljon|bat\./i.test(detail)
  for (const raw of detail.split(/,\s*/)) {
    const part = raw.trim()
    let m: RegExpMatchArray | null
    if (!higher && HIGHER.test(part) && !STAFF_PART.test(part)) {
      higher = { key: `g:${higherKey(part)}`, label: part }
    } else if ((m = part.match(/^([0-9]+\.?|[IVXivx]{1,4}\.?)\s+(?:([a-zčćžšđ]+)\s+)?(?:bataljon|bat\.)$/i)) && number(m[1])) {
      const n = number(m[1])!
      battalion = m[2]
        ? { key: `b${n}:${m[2].toLowerCase()}`, label: `${n}. ${m[2].toLowerCase()} bataljon` }
        : { key: `b${n}`, label: `${n}. bataljon`, kind: 'battalion', n: Number(n) }
    } else if ((m = part.match(/^(?:bataljon|bat\.)\s+[»"„]?([^«"“]+)[«"“]?$/i))) {
      battalion = { key: `b:${m[1].toLowerCase()}`, label: `bataljon ${m[1]}` }
    } else if ((m = part.match(/^(\d+)\.?\s+(?:([a-zčćžšđ]+)\s+)?četa$/i))) {
      // "2. četa"; a company named for its district: "1. požeška četa" (Užički odred)
      const named = m[2] ? m[2].toLowerCase() : ''
      company = named
        ? { key: `c${m[1]}:${named}`, label: `${m[1]}. ${named} četa` }
        : { key: `c${m[1]}`, label: `${m[1]}. četa`, kind: 'company', n: Number(m[1]) }
    } else if ((m = part.match(/^(\d+)\.?\s+vod$/i))) {
      platoon = { key: `v${m[1]}`, label: `${m[1]}. vod`, kind: 'platoon', n: Number(m[1]) }
    } else if ((m = part.match(/^(\d+)\.?\s+desetina$/i))) {
      squad = { key: `d${m[1]}`, label: `${m[1]}. desetina`, kind: 'squad', n: Number(m[1]) }
    } else if (/četa|baterija|jedinic|intendantura|vod/i.test(part)) {
      const label = part.charAt(0).toLowerCase() + part.slice(1)
      // a named company inside a battalion ("1. bataljon, prateća četa") or a group of the brigade staff
      if (inBattalion) company = { key: `c:${label}`, label }
      else group = { key: `s:${label}`, label }
    }
  }
  const lower = [company, platoon, squad].filter((l): l is Level => l !== null)
  const top = higher ? [higher] : []
  if (battalion) return [...top, battalion, ...lower]
  // the companies at brigade staff (signals, scouts, quartermasters) go under one node, as the books group them
  if (group) return group.key === STAFF.key ? [...top, STAFF, ...lower] : [...top, STAFF, group, ...lower]
  return lower.length ? [...top, NO_BATTALION, ...lower] : top
}

const STAFF: Level = { key: 's:prištapske jedinice', label: 'prištapske jedinice', kind: 'staff' }
const NO_BATTALION: Level = { key: 'x', label: 'bataljon nije naveden', kind: 'none' }

// ── Day of death ─────────────────────────────────────────────

/** "15. 01. 1943", "16. XI 1944", "3. decembra 1944", "20.4.1944" -> "1943-01-15"; null without a day or outside
 * the war. The same reading as "Na današnji dan" (deathDay.ts). */
export function deathDay(soldier: Soldier): string | null {
  if (!soldier.death_date || soldier.death_type === 'umro') return null
  const d = parseDeathDay(soldier.death_date)
  if (!d || d.year < 1941 || d.year > 1945) return null
  return `${d.year}-${String(d.month).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`
}

/** "1943-01-15" -> [15, 1, 1943] */
export function dayParts(iso: string): [number, number, number] {
  const [y, m, d] = iso.split('-').map((n) => parseInt(n, 10))
  return [d, m, y]
}

/** Birth and death years: "1921–1943" */
export function lifeSpan(soldier: Soldier): string {
  const born = soldier.birth_year?.match(/\d{4}/)?.[0]
  const died = soldier.death_date?.match(/(?:18|19)\d\d/)?.[0]
  return born || died ? [born ?? '', died ?? ''].join('–').replace(/^–|–$/g, '') : ''
}

// ── Places (scripts/build_relations.py) ──────────────────────

export interface PlaceMember {
  id: string
  name: string
  file: string   // the unit's data file: "soldiers.json"
  years: string
}

export interface Place {
  village: string
  municipality: string
  members: PlaceMember[]
}

/** A place as the place files give it: village, municipality, and its people as [id, name, data file, years] */
export type PlaceRow = [string, string, [string, string, string, string][]]

// The places index is cut into small files (app/lib/placeFiles.ts), so opening a record loads its soldier's place
// alone: a shard of ids says which chunk of places his is in, and where
export const placeShard = (id: string) => id.slice(0, 7)
/** About how much of the index a chunk holds; a place larger than that is a chunk of its own */
export const PLACE_CHUNK_BYTES = 24000

// Each file once per visit
const placeFiles = new Map<string, Promise<unknown>>()

function placeFile<T>(path: string): Promise<T> {
  let file = placeFiles.get(path)
  if (!file) {
    file = fetch(path).then((res) => {
      if (!res.ok) throw new Error(`${path}: ${res.status}`)
      return res.json()
    })
    file.catch(() => placeFiles.delete(path))
    placeFiles.set(path, file)
  }
  return file as Promise<T>
}

/** A shard of ids: where each soldier's place is (w), and his set of embroidered frames (v, lib/vez.ts) */
interface PlaceShard {
  w: Record<string, [number, number]>
  v: Record<string, number>
}

/** The place a soldier was born in, with everyone else born there, or null if the index doesn't place him */
export async function placeOf(id: string): Promise<Place | null> {
  const shard = await placeFile<PlaceShard>(placesOfPath(placeShard(id)))
  const at = shard.w[id]
  if (!at) return null
  const [village, municipality, rows] = (await placeFile<PlaceRow[]>(placesChunkPath(at[0])))[at[1]]
  return { village, municipality, members: rows.map(([id, name, file, years]) => ({ id, name, file, years })) }
}

/** A soldier's set of embroidered frames, or null for the neutral set (a shard with no one of his is no file) */
export async function vezSetOf(id: string): Promise<number | null> {
  const shard = await placeFile<PlaceShard>(placesOfPath(placeShard(id))).catch(() => null)
  return shard?.v[id] ?? null
}
