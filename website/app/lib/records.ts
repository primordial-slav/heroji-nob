import type { Soldier, SoldierSource } from './types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { sources } from '@/app/data/sources'
import { messagesFor, type Messages } from '@/app/i18n'
import { localePath, type Lang } from '@/app/i18n/config'
import { sourceAuthor } from '@/app/i18n/sources'

// A record's own address: /units/<unit>?borac=<soldier id>, in a language /en/units/<unit>?borac=<soldier id>
export const RECORD_PARAM = 'borac'

export function unitByName(name?: string): Unit | undefined {
  return name ? units.find((u) => u.name === name) : undefined
}

export function recordPath(unit: Unit, soldierId: string, lang: Lang): string {
  return localePath(lang, `/units/${unit.id}?${RECORD_PARAM}=${encodeURIComponent(soldierId)}`)
}

export function cardPath(unit: Unit, soldierId: string, lang: Lang): string {
  return localePath(lang, `/kartica?jedinica=${encodeURIComponent(unit.id)}&${RECORD_PARAM}=${encodeURIComponent(soldierId)}`)
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

/** Label (in the page's language) and value (as the book has it) of every structured field the record has */
export function recordDetails(soldier: Soldier, t: Messages): [string, string][] {
  const died = soldier.death_type === 'umro'
  const f = t.record.fields
  const details: [string, string | undefined][] = [
    [f.fathersName, soldier.fathers_name],
    [f.birthYear, soldier.birth_year],
    [f.birthPlace, soldier.birth_place],
    [f.ethnicity, soldier.ethnicity],
    [f.occupation, soldier.occupation],
    [f.rank, soldier.rank],
    [f.unitDetail, soldier.unit_detail],
    [died ? f.deathDate : f.killedDate, soldier.death_date],
    [died ? f.deathPlace : f.killedPlace, soldier.death_place],
  ]
  return details.filter((d): d is [string, string] => Boolean(d[1]))
}

/** "1924 – 1945" when the record has both years */
export function lifeYears(soldier: Soldier): string | null {
  const born = soldier.birth_year?.match(/\d{4}/)?.[0]
  const died = soldier.death_date?.match(/\d{4}/)?.[0]
  return born && died ? `${born} – ${died}` : null
}

/** A line to quote the record by: the name, where it is printed (the book's title as printed), and the record's id */
export function citation(soldier: Soldier, lang: Lang): string {
  const source = sourceOf(soldier)
  const where = source
    ? [source.title, sourceAuthor(source, lang)].filter(Boolean).join(', ')
    : sourceTitle(soldier)
  return messagesFor(lang).record.citation(soldier.full_name, where, soldier.pdf_page ?? null, soldier.soldier_id)
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
