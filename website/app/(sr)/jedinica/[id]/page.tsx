import Link from 'next/link'
import { notFound } from 'next/navigation'
import { units } from '@/app/data/units'
import { unitImageProps } from '@/app/lib/unitImage'
import { photoPosition } from '@/app/data/photoFocus'
import { ArrowLeftIcon } from '@/app/components/Icons'
import { LAND, SHEET } from '@/app/(sr)/mapa/map1941'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import { ROUTE } from '@/app/(sr)/mapa/units/prva-licka'
import * as PL from '../_data/prva-licka-brigada'
import { Lanes, day } from '../_parts'
import { portraitOf, readRecords } from '../_server'
import s from '../jedinica.module.css'

// The unit overview (local only, not linked from the site yet): the unit's path through the war as a timeline, then
// four doors, as the home page has: its war path on the map, its staff, its battalions, its soldiers. Only the Prva
// lička for now, from its book.

const DATA: Record<string, typeof PL> = { 'prva-licka-brigada': PL }

// Built with the site: the unit files are read at build time (a server function on Vercel has none of public/)
export const dynamicParams = false
export function generateStaticParams() {
  return Object.keys(DATA).map((id) => ({ id }))
}
const MAP: Record<string, { key: string; route: typeof ROUTE }> = { 'prva-licka-brigada': { key: 'prva-licka', route: ROUTE } }
const FELL = /^(poginu|streljan|ubijen|nestao|nestala)/
const n = (x: number) => x.toLocaleString('de-DE')

/** The map door's picture: the kingdom's outline and the brigade's way across it */
function RouteSketch({ route }: { route: typeof ROUTE }) {
  // the sheet (1000 x 873) widened to the card's 4:3
  const w = (SHEET.height * 4) / 3
  const line = route.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  return (
    <svg viewBox={`${(SHEET.width - w) / 2} 0 ${w} ${SHEET.height}`} className={s.sketch} aria-hidden="true">
      {LAND.map((d, i) => <path key={i} d={d} className={s.sketchLand} />)}
      <path d={line} className={s.sketchRoute} />
      <circle cx={route[0].x} cy={route[0].y} r={9} className={s.sketchStart} />
    </svg>
  )
}

/** The staff door's picture: the staff chart in small, a bar a post, a block a holder */
function StaffSketch({ chart, start, end }: { chart: typeof PL.STAFF_CHART; start: string; end: string }) {
  const t = (x: string) => new Date(x).getTime()
  const at = (x: string) => ((t(x) - t(start)) / (t(end) - t(start))) * 380 + 10
  return (
    <svg viewBox="0 0 400 300" className={s.sketch} aria-hidden="true">
      {chart.map((row, i) => row.spans.map((sp, j) => (
        <rect key={`${i}${j}`} x={at(sp.from) + 1} y={38 + i * 48} width={Math.max(3, at(sp.to) - at(sp.from) - 2)} height={30}
              className={sp.guess ? s.sketchBarGuess : j % 2 ? s.sketchBarAlt : s.sketchBar} />
      )))}
    </svg>
  )
}

export default async function UnitOverview({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const unit = units.find((u) => u.id === id)
  const data = DATA[id]
  if (!unit || !data) notFound()

  const recs = readRecords(unit.dataFile)
  const fallen = recs.list.filter((r) => FELL.test(r.death_type ?? '')).length
  const map = MAP[id]
  const leaders = new Set(data.STAFF.flatMap((x) => x.people.map((p) => p.name))).size
  // the soldiers' door: wartime portraits only, as every display of many faces (data/wartimePortraits.ts)
  const faces = recs.list.filter((r) => WARTIME_PORTRAITS.includes(r.soldier_id)).map((r) => portraitOf(r)).filter(Boolean).slice(0, 6) as string[]
  const numbers = [...new Set(data.BATTALIONS.map((b) => b.short.slice(0, 1)))]

  // the battalions as lanes by their number: the 3. and 4. were others before 18. 11. 1942, the 5. three in turn
  const lanes = [
    { label: 'Brigada', spans: data.NAMES.map((x, i) => ({ name: x.name, from: x.from, to: data.NAMES[i + 1]?.from ?? data.END })) },
    ...data.COMMAND,
    ...numbers.map((no) => ({
      label: `${no}. bataljon`,
      spans: data.BATTALIONS.filter((b) => b.short.startsWith(`${no}.`))
        .map((b) => ({ name: b.short.slice(3), from: b.from, to: b.to, href: `/jedinica/${id}/bataljoni/${b.slug}`, note: b.origin })),
    })),
  ]

  return (
    <div>
      <section className="container unit-hero">
        <Link href="/jedinice" className="back-link"><ArrowLeftIcon size={16} /> Sve jedinice</Link>
        <div className="unit-hero-body">
          <img {...unitImageProps(unit.image, '104vw')} alt={unit.name} className="unit-hero-photo" style={{ objectPosition: photoPosition(unit.id) }} />
          <div>
            <h1>{unit.name.replace(/"([^"]+)"/, '„$1“')}</h1>
            <p className="unit-hero-desc">{unit.description}</p>
          </div>
        </div>
      </section>

      <div className={`container ${s.page}`}>
        <section aria-labelledby="put">
          <h2 id="put" className={s.head}>Put brigade</h2>
          <Lanes lanes={lanes} start={data.START} end={data.END} />
          <ol className={s.events}>
            {data.EVENTS.map((e) => (
              <li key={e.date + e.text.slice(0, 12)}>
                <time dateTime={e.date}>{day(e.date)}</time>
                <span>{e.text}{e.p && <> <a href={`${data.BOOK}#page=${e.p}`} target="_blank" rel="noreferrer">strana u knjizi</a></>}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className={`doors ${s.doors}`} aria-label="Dalje o brigadi">
          <ul className="unit-grid doors-grid">
            {map && (
              <li>
                <Link href={`/mapa?jedinica=${map.key}`} className="unit-card door">
                  <div className={`unit-card-photo ${s.doorSketch}`}><RouteSketch route={map.route} /></div>
                  <div className="unit-card-body">
                    <h3 className="unit-name">Ratni put</h3>
                    <p className="unit-desc">Put brigade mesec po mesec na karti Jugoslavije, s borbama i mestima gde su borci poginuli.</p>
                    <p className="unit-count">{day(data.START.slice(0, 7))} – {day(data.END.slice(0, 7))}</p>
                  </div>
                </Link>
              </li>
            )}
            <li>
              <Link href={`/jedinica/${id}/stab`} className="unit-card door">
                <div className={`unit-card-photo ${s.doorSketch}`}>
                  <StaffSketch chart={data.STAFF_CHART} start={data.START} end={data.END} />
                </div>
                <div className="unit-card-body">
                  <h3 className="unit-name">Štab brigade</h3>
                  <p className="unit-desc">Komandanti, komesari, njihovi zamenici i načelnici štaba, po vremenu kad su bili na dužnosti.</p>
                  <p className="unit-count">{leaders} starešina</p>
                </div>
              </Link>
            </li>
            <li>
              <Link href={`/jedinica/${id}/bataljoni`} className="unit-card door">
                <div className={`unit-card-photo ${s.doorNumbers}`} aria-hidden="true">
                  {numbers.map((no) => <span key={no}>{no}.</span>)}
                </div>
                <div className="unit-card-body">
                  <h3 className="unit-name">Bataljoni</h3>
                  <p className="unit-desc">Bataljoni brigade po broju, njihovi štabovi, čete i vodovi.</p>
                  <p className="unit-count">{data.BATTALIONS.length} bataljona</p>
                </div>
              </Link>
            </li>
            <li>
              <Link href={`/units/${id}`} className="unit-card door">
                <div className="unit-card-photo door-pics door-faces" aria-hidden="true">
                  {faces.map((src) => <img key={src} src={src} alt="" loading="lazy" />)}
                </div>
                <div className="unit-card-body">
                  <h3 className="unit-name">Borci</h3>
                  <p className="unit-desc">Spisak boraca brigade iz njene knjige, s pretragom po imenu i mestu.</p>
                  <p className="unit-count">{n(recs.list.length)} boraca · {n(fallen)} poginulih</p>
                </div>
              </Link>
            </li>
          </ul>
        </section>
      </div>
    </div>
  )
}
