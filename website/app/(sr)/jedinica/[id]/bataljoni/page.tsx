import Link from 'next/link'
import { notFound } from 'next/navigation'
import { units } from '@/app/data/units'
import { ArrowLeftIcon } from '@/app/components/Icons'
import * as PL from '../../_data/prva-licka-brigada'
import { Lanes, day } from '../../_parts'
import { readRecords } from '../../_server'
import s from '../../jedinica.module.css'

// The brigade's battalions (local only), under their numbers: a card each, to its own page. One number was borne
// by different battalions one after another, with their own men and companies.

const DATA: Record<string, typeof PL> = { 'prva-licka-brigada': PL }

// Built with the site: the unit files are read at build time (a server function on Vercel has none of public/)
export const dynamicParams = false
export function generateStaticParams() {
  return Object.keys(DATA).map((id) => ({ id }))
}
const n = (x: number) => x.toLocaleString('de-DE')

export default async function BattalionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const unit = units.find((u) => u.id === id)
  const data = DATA[id]
  if (!unit || !data) notFound()

  const recs = readRecords(unit.dataFile)
  const count = (detail: string[]) =>
    recs.list.filter((r) => detail.some((d) => r.unit_detail === d || (r.unit_detail ?? '').endsWith(`, ${d}`))).length
  const numbers = [...new Set(data.BATTALIONS.map((b) => b.short.slice(0, 1)))]
  const lanes = numbers.map((no) => ({
    label: `${no}. bataljon`,
    spans: data.BATTALIONS.filter((b) => b.short.startsWith(`${no}.`))
      .map((b) => ({ name: b.short.slice(3), from: b.from, to: b.to, href: `/jedinica/${id}/bataljoni/${b.slug}`, note: b.origin })),
  }))

  return (
    <div className={`container ${s.page}`}>
      <Link href={`/jedinica/${id}`} className="back-link"><ArrowLeftIcon size={16} /> {unit.name.replace(/"([^"]+)"/, '„$1“')}</Link>
      <h1 className={s.title}>Bataljoni</h1>
      <p className={s.lead}>
        Brigada je imala četiri bataljona, a tri puta i peti. Isti broj nosili su jedan za drugim različiti bataljoni:
        kordunaški i banijski vratili su se u svoje krajeve novembra 1942, a njihove brojeve dobili su bataljoni 4.
        ličkog odreda. Svaki od tri peta bataljona osnovan je iznova.
      </p>
      <Lanes lanes={lanes} start={data.START} end={data.END} />

      {numbers.map((no) => (
        <section key={no} className={s.numberGroup} aria-label={`${no}. bataljon`}>
          <h2 className={s.numberHead}><span className={s.numberBig}>{no}.</span> bataljon</h2>
          <ul className={s.numberCards}>
            {data.BATTALIONS.filter((b) => b.short.startsWith(`${no}.`)).map((b) => (
              <li key={b.slug}>
                <Link href={`/jedinica/${id}/bataljoni/${b.slug}`}>
                  <span className={s.numberTitle}>{b.name}</span>
                  <span className={s.numberLine}>{day(b.from)} – {b.to === data.END ? 'kraj rata' : day(b.to)}</span>
                  <span className={s.numberLine}>{b.origin}</span>
                  <span className={s.batCount}>{n(count(b.detail))} boraca na spisku</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
