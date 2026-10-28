import type { Soldier, SoldierSource } from './types'
import { sources } from '@/app/data/sources'
import type { Lang, Messages } from '@/app/i18n'
import { sourceAuthor } from '@/app/i18n/sourceNames'

// The books a record's entries are printed in (data/sources.ts): apart from lib/records.ts, so that the pages'
// search results don't load the list of books, which only the record dialog and the memorial card use

/** The book (or web page) an entry was printed in, as the Sources page lists it */
export function sourceOf(entry: SoldierSource) {
  return entry.pdf_file
    ? sources.find((s) => s.pdfPath === `/pdfs/${entry.pdf_file}`)
    : sources.find((s) => entry.source_url?.startsWith(s.pdfPath))
}

export function sourceTitle(entry: SoldierSource): string {
  return sourceOf(entry)?.title ?? entry.pdf_file ?? 'znaci.org'
}

/** A line to quote the record by: the name, where it is printed (the book's title as printed), and the record's id */
export function citation(soldier: Soldier, lang: Lang, t: Messages): string {
  const source = sourceOf(soldier)
  const where = source
    ? [source.title, sourceAuthor(source, lang)].filter(Boolean).join(', ')
    : sourceTitle(soldier)
  return t.record.citation(soldier.full_name, where, soldier.pdf_page ?? soldier.source_page ?? null, soldier.soldier_id)
}
