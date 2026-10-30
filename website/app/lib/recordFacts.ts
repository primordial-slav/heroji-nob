import type { Soldier } from './types'
import type { Messages } from '@/app/i18n'
import { partyOf } from './records'
import { isWoman } from './standIn'

// The record's facts, one list for the record dialog and the memorial card (the user's choice of 2026-10-26): the
// same rows in the same order, the dialog adding its links beside the ones it links (the place, the comrades, the
// same day). A row is left out where the record gives nothing for it.

export type FactKey = 'father' | 'mother' | 'born' | 'ethnicity' | 'occupation' | 'unit' | 'party' | 'death'

export interface Fact {
  key: FactKey
  label: string
  value: string
}

/** A unit as its name says it is: "brigade", "division", "detachment" (odred), "battalion", "company", or "unit" */
export function unitKind(name?: string): string {
  if (!name) return 'unit'
  if (/divizij/i.test(name)) return 'division'
  if (/odred/i.test(name)) return 'detachment'
  if (/brigad/i.test(name)) return 'brigade'
  if (/bataljon/i.test(name)) return 'battalion'
  if (/(?<!\p{L})četa(?!\p{L})/iu.test(name)) return 'company'
  return 'unit'
}

// The father by his name; not where the book prints only an initial ("B", "Đ.", "Lj"), which the name shows already,
// nor a value of more words, which is a place or the scan's ("Bosanska Gradiška", "Ivana Mil": 96 records in 2026-10)
const FULL_NAME = /^\p{Lu}\p{Ll}{2,}(?:-\p{Lu}\p{Ll}+)?$/u

/**
 * Otac (or Majka), Rođen, Narodnost, Zanimanje, U brigadi, Partija and the fate, in the page's language; the values as
 * the books give them (scripts/standardize_fields.py gives the dates one form)
 */
export function recordFacts(soldier: Soldier, t: Messages, unitName?: string): Fact[] {
  const woman = isWoman(soldier)
  const facts: Fact[] = []
  const add = (key: FactKey, label: string, value: string | undefined) => {
    if (value) facts.push({ key, label, value })
  }
  const f = t.record.fields
  if (FULL_NAME.test(soldier.fathers_name?.trim() ?? '')) add('father', f.father, soldier.fathers_name.trim())
  // the mother, where the book names her for an unknown father (the census's "Ajduk (Ruža) Joze"; standardize_fields.py)
  if (FULL_NAME.test(soldier.mothers_name?.trim() ?? '')) add('mother', f.mother, soldier.mothers_name!.trim())
  // the day of birth where an entry gives it, else the year; and the years other books give ("1915 ili 1918")
  const or = ` ${t.record.or} `
  const born = [soldier.birth_date || soldier.birth_year, ...(soldier.variants?.born ?? [])].filter(Boolean).join(or)
  add('born', t.life.born(woman), [born, soldier.birth_place].filter(Boolean).join(', '))
  // the census's "ostalo" (another nationality) says nothing on its own
  add('ethnicity', f.ethnicity, soldier.ethnicity === 'ostalo' ? '' : soldier.ethnicity)
  add('occupation', f.occupation, soldier.occupation)
  // the sub-unit, then the duty after a dot: "1. četa, 2. bataljon · komandir voda, komandir čete" (the user's choice of
  // 2026-10-30: a comma between them hid where the unit ends)
  add('unit', t.life.unit(unitKind(unitName)), [soldier.unit_detail, soldier.rank].filter(Boolean).join(' · '))
  // "Partija: SKOJ od 1941, KPJ od 1944"
  const party = partyOf(soldier)
  if (party.length) add('party', f.party, t.life.party(party))
  // a death the record gives without a date or a place still shows ("Umro", a survivor who has died since; "Umro:
  // posle rata", one the Slovene rosters mark "† po osvoboditvi")
  if (soldier.death_date || soldier.death_place || soldier.death_type) {
    const when = soldier.death_date || (soldier.death_after_war ? t.life.afterWar : '')
    const others = soldier.variants?.death ?? []
    // another book's day after "ili": "13.04.1945 ili 07.02.1945, Aleksandrovac" where every book names that place,
    // else each with its own, "05.03.1943, kod Gornjeg Vakufa ili 06.1943, Sutjeska" (a book that names none, its day)
    const value = others.every((d) => d.place === soldier.death_place)
      ? [[when, ...others.map((d) => d.date)].filter(Boolean).join(or), soldier.death_place].filter(Boolean).join(', ')
      : [[when, soldier.death_place], ...others.map((d) => [d.date, d.place])].map((p) => p.filter(Boolean).join(', ')).join(or)
    add('death', t.life.fate(soldier.death_type, woman), value || t.life.undated)
  }
  return facts
}
