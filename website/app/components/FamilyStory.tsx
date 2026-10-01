'use client'

import type { FamilyContribution } from '@/app/data/family'
import { useT } from '@/app/i18n/LangContext'

// What a family sent about the soldier: a photograph and/or a story, with who sent it. The first photo is
// already his portrait at the top of the record (data/portraits.ts), so it isn't shown again here.
// Their words are shown as sent; only the heading and the month are in the page's language.
export default function FamilyStory({ items }: { items: FamilyContribution[] }) {
  const t = useT().family
  const portrait = items.find((item) => item.photo)
  const shown = items
    .map((item) => (item === portrait ? { ...item, photo: undefined } : item))
    .filter((item) => item.photo || item.text)
  if (shown.length === 0) return null
  const sentOn = (date: string) => {
    const [year, month] = date.split('-').map(Number)
    return t.sent(year, month || undefined)
  }
  return (
    <section className="family-story">
      <h3>{t.title}</h3>
      {shown.map((item, i) => (
        <figure key={i} className={item.photo ? 'family-item has-photo' : 'family-item'}>
          {item.photo && <img src={`/porodica/${item.photo}`} alt={item.photoCaption ?? ''} />}
          <figcaption>
            {item.photoCaption && <p className="family-caption">{item.photoCaption}</p>}
            {item.text && <p className="family-text">{item.text}</p>}
            <p className="family-from">{item.from} · {sentOn(item.date)}</p>
          </figcaption>
        </figure>
      ))}
    </section>
  )
}
