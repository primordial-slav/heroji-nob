import type { Soldier } from '@/app/lib/types'
import { contributionsFor } from '@/app/data/family'
import { HomeIcon } from './Icons'
import s from './FamilyMark.module.css'

/** After a card's row a family's report set (lib/recordFacts.ts, `Fact.family`): "Ispravka po podacima porodice" */
export default function FamilyMark({ title }: { title: string }) {
  return (
    <span className={s.mark} title={title}>
      <HomeIcon size={14} />
      <span className={s.words}>{title}</span>
    </span>
  )
}

/** Whether a family has added to the card: its note or photo (data/family.ts; not a public page's nor a visitor's), a row
 *  its report set (family_fields), or its papers among the entries (Porodična arhiva, "porodica:") */
export function familyAdded(soldier: Soldier): boolean {
  const others = (soldier.other_sources ?? []).map((o) => o.soldier_id).filter(Boolean) as string[]
  if (contributionsFor(soldier.soldier_id, others).some((c) => !c.origin)) return true
  if (soldier.family_fields?.length) return true
  return [soldier.source_url, ...(soldier.other_sources ?? []).map((o) => o.source_url)].some((u) => !!u?.startsWith('porodica:'))
}

/** The card's dot after the name (the user's choice of 2026-11-23, "just a small mark, nothing a real user can really
 *  notice"): 5 px in the embroidered frames' thread colour, its words only in the tooltip */
export function FamilyDot({ soldier, title }: { soldier: Soldier; title: string }) {
  if (!familyAdded(soldier)) return null
  return <span className={s.dot} title={title} role="img" aria-label={title} />
}
