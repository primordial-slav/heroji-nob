import type { FamilyContribution } from '@/app/data/family'

const MONTHS = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']

function sentOn(date: string): string {
  const [year, month] = date.split('-').map(Number)
  return month ? `${MONTHS[month - 1]} ${year}.` : `${year}.`
}

// What a family sent about the soldier: a photograph and/or a story, with who sent it
export default function FamilyStory({ items }: { items: FamilyContribution[] }) {
  if (items.length === 0) return null
  return (
    <section className="family-story">
      <h3>Od porodice</h3>
      {items.map((item, i) => (
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
