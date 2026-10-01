import type { Unit } from '@/app/data/units'
import type { Soldier } from './types'

// The home page searches every unit at once, so instead of every unit's full data file (67 MB) it loads one
// compact list, /search-index.json: per soldier only what search, the results, "Na današnji dan" and the
// comrades tree in the dialog use, as an array rather than an object. Opening a soldier loads his full record
// from /records/<unit id>/<part>, a slice of RECORDS_PER_PART records of the unit's data file. Both are built from the data files
// (app/search-index.json/route.ts, app/records/[unit]/[part]/route.ts): at build time as static files, and
// fresh on every request under `next dev`.

export const SEARCH_INDEX_PATH = '/search-index.json'
export const RECORDS_PER_PART = 250

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

export const recordsPath = (unit: Unit, part: number) => `/records/${unit.id}/${part}`

// Where each soldier of the loaded index is in his unit's data file
const located = new Map<string, { unit: Unit; position: number }>()

/** Every unit's soldiers from the search index, in the order of `units`, with `unit` set to the unit's name */
export async function loadSearchIndex(units: Unit[]): Promise<Soldier[][]> {
  const response = await fetch(SEARCH_INDEX_PATH)
  if (!response.ok) throw new Error(`${SEARCH_INDEX_PATH}: ${response.status}`)
  const index: SearchIndex = await response.json()
  return units.map((unit) =>
    (index[unit.dataFile] ?? []).map((row, position) => {
      const soldier = decodeRow(row, unit.name)
      located.set(soldier.soldier_id, { unit, position })
      return soldier
    }))
}

/** The full record of a soldier from the search index, with the fields the home page set on him */
export async function fullRecord(soldier: Soldier): Promise<Soldier> {
  const at = located.get(soldier.soldier_id)
  if (!at) return soldier
  const response = await fetch(recordsPath(at.unit, Math.floor(at.position / RECORDS_PER_PART)))
  if (!response.ok) throw new Error(`${response.url}: ${response.status}`)
  const records: Soldier[] = await response.json()
  const full = records.find((r) => r.soldier_id === soldier.soldier_id)
  return full ? { ...full, unit: soldier.unit, also_units: soldier.also_units } : soldier
}
