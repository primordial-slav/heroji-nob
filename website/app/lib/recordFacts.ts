import type { Soldier, SoldierSource } from './types'
import type { Messages } from '@/app/i18n'
import { units, type Unit } from '@/app/data/units'
import { partyOf } from './records'
import { isWoman } from './standIn'

// The record's facts, one list for the record dialog and the memorial card (the user's choice of 2026-10-26): the
// same rows in the same order, the dialog adding its links beside the ones it links (the place, the comrades, the
// same day). A row is left out where the record gives nothing for it.

export type FactKey = 'father' | 'mother' | 'born' | 'ethnicity' | 'occupation' | 'unit' | 'duty' | 'party' | 'death'

/** A line of the row of a man's units: "Prva proleterska" and ", 6. bataljon · komandant brigade" */
export interface FactLine {
  text: string
  rest?: string
  /** The unit, which its name links to */
  unit: Unit
}

export interface Fact {
  key: FactKey
  label: string
  value: string
  lines?: FactLine[]
  /** A family's report set a field of this row: the card marks it ("Ispravka po podacima porodice") */
  family?: boolean
}

/** The record's fields each row shows, for its family mark */
const ROW_FIELDS: Record<FactKey, string[]> = {
  father: ['fathers_name', 'middle_name'],
  mother: ['mothers_name'],
  born: ['birth_year', 'birth_date', 'birth_place'],
  ethnicity: ['ethnicity'],
  occupation: ['occupation'],
  unit: ['unit_detail'],
  duty: ['rank'],
  party: ['party'],
  death: ['death_type', 'death_date', 'death_place'],
}

export interface LinkedRecord {
  unit: Unit
  entry: SoldierSource & { soldier_id: string }
}

/**
 * The same man's records in other units: one for each unit, the first entry that unit's record gave (its own entry, its
 * books' after it). By the day he came to each where every one of them prints it, else as they stand: an order the books
 * don't give would read as a career no one printed (the user's choice of 2026-11-04).
 */
export function linkedRecords(soldier: Soldier): LinkedRecord[] {
  const seen = new Set<string>()
  const out: LinkedRecord[] = []
  for (const e of soldier.other_sources ?? []) {
    if (!e.unit_file || !e.soldier_id || seen.has(e.unit_file)) continue
    seen.add(e.unit_file)
    const unit = units.find((u) => u.dataFile === `/${e.unit_file}`)
    if (unit) out.push({ unit, entry: e as LinkedRecord['entry'] })
  }
  return out.every((r) => r.entry.since)
    ? out.sort((a, b) => a.entry.since!.localeCompare(b.entry.since!))
    : out
}

// A unit's name in a man's list of them, without the words that say nothing of which unit it is: "Prva proleterska
// brigada", "4. splitska brigada". The kind stays, or a brigade would read otherwise than the division beside it (the
// user's correction of 2026-11-04)
const NAME_FILLER = /\s*(?:narodnooslobodilačk\p{L}+|народноослободилачк\p{L}+|народноослободителн\p{L}+|narodnoosvobodiln\p{L}+|people[’']s liberation|udarn\p{L}+|ударн\p{L}+|assault)(?!\p{L})/giu

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
 * Otac (or Majka), Rođen, Narodnost, Zanimanje, U brigadi, Dužnost, Partija and the fate, in the page's language; the
 * values as the books give them (scripts/standardize_fields.py gives the dates one form). A man of several units has one
 * row, "Jedinice", in place of U brigadi and Dužnost: a line for each unit, the record opened first, "Prva proleterska
 * brigada, 6. bataljon · komandant brigade" (shortName: how the page names a unit; the user's choice of 2026-11-04).
 */
export function recordFacts(soldier: Soldier, t: Messages, unitName?: string, shortName?: (unit: Unit) => string): Fact[] {
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
  // the sub-unit and the duty, each its own row: "U brigadi: 6. bataljon", "Dužnost: komandant brigade" (the user's choice
  // of 2026-11-04: on one line they read as if he commanded the brigade from the battalion; a list prints the battalion he
  // came to and the highest duty he held)
  const linked = shortName ? linkedRecords(soldier) : []
  if (linked.length === 0) {
    add('unit', t.life.unit(unitKind(unitName)), soldier.unit_detail)
    add('duty', f.duty, soldier.rank)
  } else {
    const own = units.find((u) => u.name === unitName)
    const served = [
      ...(own ? [{ unit: own, detail: soldier.unit_detail, duty: soldier.rank }] : []),
      ...linked.map(({ unit, entry }) => ({ unit, detail: entry.unit_detail, duty: entry.rank })),
    ]
    const lines = served.map(({ unit, detail, duty }) => ({
      text: shortName!(unit).replace(NAME_FILLER, '').trim(),
      rest: `${detail ? `, ${detail}` : ''}${duty ? ` · ${duty}` : ''}`,
      unit,
    }))
    facts.push({ key: 'unit', label: f.units, value: lines.map((l) => `${l.text}${l.rest}`).join('; '), lines })
  }
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
  const family = new Set(soldier.family_fields ?? [])
  if (family.size) {
    for (const f of facts) {
      // the row of several units carries the duty too
      const fields = f.key === 'unit' && f.lines ? [...ROW_FIELDS.unit, ...ROW_FIELDS.duty] : ROW_FIELDS[f.key]
      if (fields.some((k) => family.has(k))) f.family = true
    }
  }
  // a family's date after "ili", beside the book's day: the death row marked too (Dejanović Dušan, the user, 2026-11-23)
  if (soldier.variants?.death?.some((d) => d.family)) {
    const death = facts.find((f) => f.key === 'death')
    if (death) death.family = true
  }
  return facts
}
