import type { Soldier, SoldierSource } from './types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { sources } from '@/app/data/sources'

// A record's own address: /units/<unit>?borac=<soldier id>
export const RECORD_PARAM = 'borac'

export function unitByName(name?: string): Unit | undefined {
  return name ? units.find((u) => u.name === name) : undefined
}

export function recordPath(unit: Unit, soldierId: string): string {
  return `/units/${unit.id}?${RECORD_PARAM}=${encodeURIComponent(soldierId)}`
}

export function cardPath(unit: Unit, soldierId: string): string {
  return `/kartica?jedinica=${encodeURIComponent(unit.id)}&${RECORD_PARAM}=${encodeURIComponent(soldierId)}`
}

// An id can also be one a merged-away entry had (data merges keep it in other_sources), so old links keep working
export function findRecord(list: Soldier[], id: string): Soldier | undefined {
  return list.find((s) => s.soldier_id === id) ?? list.find((s) => s.other_sources?.some((o) => o.soldier_id === id))
}

// The soldier's own entry, then the same soldier's entries in the unit's other books
export function entriesOf(soldier: Soldier): SoldierSource[] {
  return [soldier, ...(soldier.other_sources ?? [])]
}

export const hasPage = (e: SoldierSource) => e.pdf_page != null && e.pdf_file != null

/** The book (or web page) an entry was printed in, as the Sources page lists it */
export function sourceOf(entry: SoldierSource) {
  return entry.pdf_file
    ? sources.find((s) => s.pdfPath === `/pdfs/${entry.pdf_file}`)
    : sources.find((s) => entry.source_url?.startsWith(s.pdfPath))
}

export function sourceTitle(entry: SoldierSource): string {
  return sourceOf(entry)?.title ?? entry.pdf_file ?? 'znaci.org'
}

/** Label and value of every structured field the record has, in reading order */
export function recordDetails(soldier: Soldier): [string, string][] {
  const died = soldier.death_type === 'umro'
  const details: [string, string | undefined][] = [
    ['Ime oca', soldier.fathers_name],
    ['Godina rođenja', soldier.birth_year],
    ['Mesto rođenja', soldier.birth_place],
    ['Narodnost', soldier.ethnicity],
    ['Zanimanje', soldier.occupation],
    ['Dužnost', soldier.rank],
    ['Podjedinica', soldier.unit_detail],
    [died ? 'Datum smrti' : 'Datum pogibije', soldier.death_date],
    [died ? 'Mesto smrti' : 'Mesto pogibije', soldier.death_place],
  ]
  return details.filter((d): d is [string, string] => Boolean(d[1]))
}

/** "1924 – 1945" when the record has both years */
export function lifeYears(soldier: Soldier): string | null {
  const born = soldier.birth_year?.match(/\d{4}/)?.[0]
  const died = soldier.death_date?.match(/\d{4}/)?.[0]
  return born && died ? `${born} – ${died}` : null
}

/** A line to quote the record by: the name, where it is printed, and the record's id */
export function citation(soldier: Soldier): string {
  const source = sourceOf(soldier)
  const where = source
    ? [source.title, source.author].filter(Boolean).join(', ')
    : sourceTitle(soldier)
  const page = soldier.pdf_page != null ? `, str. ${soldier.pdf_page}` : ''
  return `${soldier.full_name}. ${where}${page}. Knjiga boraca, zapis ${soldier.soldier_id}.`
}

// "narodni heroj", "proglašen za narodnog heroja", "Nosilac Ordena narodnog heroja"; not "predložen za narodnog heroja"
const HERO = /narodn(?:i|og|im)\s*heroj/i      // the OCR can lose the space ("Narodniheroj")
const PROPOSED = /predložen\w*\s+za\s+narodnog\s+heroja/gi
const SPOMENICA = /spomenic/i

/** The decorations any of the soldier's entries names */
export function decorationsOf(soldier: Soldier): { heroj: boolean; spomenica: boolean } {
  const text = entriesOf(soldier).map((e) => e.additional_info ?? '').join(' ')
  return { heroj: HERO.test(text.replace(PROPOSED, '')), spomenica: SPOMENICA.test(text) }
}
