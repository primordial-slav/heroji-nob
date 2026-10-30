import type { Messages } from '@/app/i18n/messages/sr'
import type { Soldier } from './types'
import { isWoman } from './standIn'

/** The sentences of the war's events a soldier was part of, in the order they happened, for the record dialog and
 *  the memorial card (scripts/make_war_events.py) */
export function eventLines(soldier: Soldier, t: Messages): string[] {
  const woman = isWoman(soldier)
  return (soldier.events ?? []).map((e) => (e.e === 'igman' ? t.record.igman(e, woman) : t.record.sutjeska(woman)))
}
