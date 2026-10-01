import type { Soldier } from './types'

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

const ROMAN: Record<string, number> = { i: 1, ii: 2, iii: 3, iv: 4, v: 5, vi: 6, vii: 7, viii: 8, ix: 9, x: 10 }

function number(raw: string): string | null {
  const n = raw.replace(/\.$/, '').toLowerCase()
  if (/^\d+$/.test(n)) return String(parseInt(n, 10))
  return ROMAN[n] ? String(ROMAN[n]) : null
}

export function subunitPath(detail?: string): Level[] {
  if (!detail) return []
  let battalion: Level | null = null
  let company: Level | null = null
  let platoon: Level | null = null
  let squad: Level | null = null
  let group: Level | null = null   // brigade-level groups outside the battalions: "prištapske jedinice", "četa za vezu"
  const inBattalion = /bataljon|bat\./i.test(detail)
  for (const raw of detail.split(/,\s*/)) {
    const part = raw.trim()
    let m: RegExpMatchArray | null
    if ((m = part.match(/^([0-9]+\.?|[IVXivx]{1,4}\.?)\s+(?:([a-zčćžšđ]+)\s+)?(?:bataljon|bat\.)$/i)) && number(m[1])) {
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
  if (battalion) return [battalion, ...lower]
  // the companies at brigade staff (signals, scouts, quartermasters) go under one node, as the books group them
  if (group) return group.key === STAFF.key ? [STAFF, ...lower] : [STAFF, group, ...lower]
  return lower.length ? [NO_BATTALION, ...lower] : []
}

const STAFF: Level = { key: 's:prištapske jedinice', label: 'prištapske jedinice', kind: 'staff' }
const NO_BATTALION: Level = { key: 'x', label: 'bataljon nije naveden', kind: 'none' }

// Sub-unit paths and days of death of a unit's list, worked out once per list
const indexes = new WeakMap<Soldier[], { paths: Map<Soldier, Level[]>; days: Map<Soldier, string | null> }>()

export function unitIndex(list: Soldier[]) {
  let index = indexes.get(list)
  if (!index) {
    index = { paths: new Map(), days: new Map() }
    for (const s of list) {
      index.paths.set(s, subunitPath(s.unit_detail))
      index.days.set(s, deathDay(s))
    }
    indexes.set(list, index)
  }
  return index
}

// ── Day of death ─────────────────────────────────────────────

const MONTHS: [RegExp, number][] = [
  [/^(januar|siječ)/, 1], [/^(februar|veljač)/, 2], [/^(mart|ožuj)/, 3], [/^(april|travn)/, 4], [/^(maj|svib)/, 5],
  [/^(jun|lipn)/, 6], [/^(jul|srpn)/, 7], [/^(avgust|august|kolovoz)/, 8], [/^(septemb|rujn)/, 9],
  [/^(oktob|listopad)/, 10], [/^(novemb|studen)/, 11], [/^(decemb|prosin)/, 12],
]

/** "15. 01. 1943", "16. IV 1944", "3. decembra 1944" -> "1943-01-15"; null without a day or outside the war */
export function deathDay(soldier: Soldier): string | null {
  if (!soldier.death_date || soldier.death_type === 'umro') return null
  const d = soldier.death_date.replace(/\s+/g, ' ')
  const m = d.match(/^(\d{1,2})\.\s?(\d{1,2}|[IVX]{1,4}|[a-zčćžšđ]+)\.?\s?(19\d\d)/i)
  if (!m) return null
  const year = parseInt(m[3], 10)
  if (year < 1941 || year > 1945) return null
  let month = /^\d+$/.test(m[2]) ? parseInt(m[2], 10) : ROMAN[m[2].toLowerCase()] ?? 0
  if (!month) month = MONTHS.find(([rx]) => rx.test(m[2].toLowerCase()))?.[1] ?? 0
  const day = parseInt(m[1], 10)
  if (month < 1 || month > 12 || day < 1 || day > 31) return null
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
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

interface PlaceIndex {
  byId: Map<string, Place>
}

let placeIndex: Promise<PlaceIndex> | null = null

export function loadPlaces(): Promise<PlaceIndex> {
  placeIndex ??= fetch('/relations/places.json')
    .then((res) => res.json())
    .then((doc: { files: string[]; places: [string, string, [string, string, number, string][]][] }) => {
      const byId = new Map<string, Place>()
      for (const [village, municipality, rows] of doc.places) {
        const place: Place = {
          village,
          municipality,
          members: rows.map(([id, name, file, years]) => ({ id, name, file: doc.files[file], years })),
        }
        for (const m of place.members) byId.set(m.id, place)
      }
      return { byId }
    })
    .catch((e) => {
      placeIndex = null
      throw e
    })
  return placeIndex
}
