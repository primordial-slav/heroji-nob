import type { Messages } from '@/app/i18n/messages/sr'
import type { Soldier } from './types'
import { isWoman } from './standIn'

/** The sentences of the war's events a soldier was part of, for the record dialog and the memorial card */
export function eventLines(soldier: Soldier, t: Messages): string[] {
  const woman = isWoman(soldier)
  return (soldier.events ?? []).flatMap((e) => (e.e === 'igman' ? [t.record.igman(e, woman)] : []))
}
