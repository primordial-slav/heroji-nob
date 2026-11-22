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
