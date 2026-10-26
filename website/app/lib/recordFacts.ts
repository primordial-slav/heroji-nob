import type { Soldier } from './types'
import type { Messages } from '@/app/i18n'
import { partyOf } from './records'
import { isWoman } from './standIn'

// The record's facts, one list for the record dialog and the memorial card (the user's choice of 2026-10-26): the
// same rows in the same order, the dialog adding its links beside the ones it links (the place, the comrades, the
// same day). A row is left out where the record gives nothing for it.

export type FactKey = 'father' | 'born' | 'ethnicity' | 'occupation' | 'unit' | 'party' | 'death'

export interface Fact {
  key: FactKey
  label: string
  value: string
}

/** A unit as its name says it is: "brigade", "division", "detachment" (odred), or "unit" */
export function unitKind(name?: string): string {
  if (!name) return 'unit'
  if (/divizij/i.test(name)) return 'division'
  if (/odred/i.test(name)) return 'detachment'
  if (/brigad/i.test(name)) return 'brigade'
  return 'unit'
}

// The father by his name; not where the book prints only an initial ("B", "Đ.", "Lj"), which the name shows already,
// nor a value of more words, which is a place or the scan's ("Bosanska Gradiška", "Ivana Mil": 96 records in 2026-10)
const FULL_NAME = /^\p{Lu}\p{Ll}{2,}(?:-\p{Lu}\p{Ll}+)?$/u

/**
 * Otac, Rođen, Narodnost, Zanimanje, U brigadi, Partija and the fate, in the page's language; the values as the
 * books give them (scripts/standardize_fields.py gives the dates one form)
 */
export function recordFacts(soldier: Soldier, t: Messages, unitName?: string): Fact[] {
  const woman = isWoman(soldier)
  const facts: Fact[] = []
  const add = (key: FactKey, label: string, value: string | undefined) => {
    if (value) facts.push({ key, label, value })
  }
  const f = t.record.fields
  if (FULL_NAME.test(soldier.fathers_name?.trim() ?? '')) add('father', f.father, soldier.fathers_name.trim())
  // the day of birth where the entry gives it (the life line's first step), else the year
  const born = soldier.life_events?.find((e) => e.k === 'born')
  const day = born && /^\d{4}-\d\d-\d\d$/.test(born.d) ? born.d.split('-').map(Number) : null
  add('born', t.life.born(woman), [day ? t.kin.day(day[2], day[1], day[0]) : soldier.birth_year, soldier.birth_place].filter(Boolean).join(', '))
  add('ethnicity', f.ethnicity, soldier.ethnicity)
  add('occupation', f.occupation, soldier.occupation)
  add('unit', t.life.unit(unitKind(unitName)), [soldier.unit_detail, soldier.rank].filter(Boolean).join(', '))
  // "Partija: SKOJ od 1941, KPJ od 1944"
  const party = partyOf(soldier)
  if (party.length) add('party', f.party, t.life.party(party))
  // a death the record gives without a date or a place still shows ("Umro", a survivor who has died since; "Umro:
  // posle rata", one the Slovene rosters mark "† po osvoboditvi")
  if (soldier.death_date || soldier.death_place || soldier.death_type) {
    const when = soldier.death_date || (soldier.death_after_war ? t.life.afterWar : '')
    add('death', t.life.fate(soldier.death_type, woman), [when, soldier.death_place].filter(Boolean).join(', ') || t.life.undated)
  }
  return facts
}
