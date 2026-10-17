import Link from 'next/link'
import type { Person, Span } from './_data/prva-licka-brigada'
import s from './jedinica.module.css'

// Pieces the unit overview pages share (local only): dates as the site writes them, a person's line in a list of a
// post's holders, and the chart of spans over the war's months.

export interface Post {
  id: string
  name: string
  role: string
  level: string
  battalion: string | null
  company: string | null
  platoon: string | null
  company_of_platoon: string | null
  when: string
  start: string
  death_type: string
  death_date: string
  death_place: string
  hero: boolean
}

export interface Fate {
  type: string
  date: string
  place: string
}

const MONTH = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']

/** 1942-07-08 -> "8. 7. 1942."; 1942-07 -> "jul 1942." */
export function day(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  if (d) return `${d}. ${m}. ${y}.`
  if (m) return `${MONTH[m - 1]} ${y}.`
  return `${y}.`
}

export function recordHref(unitId: string, id: string): string {
  return `/units/${unitId}?borac=${id}`
}

/** "Opsenica Stevan" with the surname bold, as the books print names */
export function Name({ name }: { name: string }) {
  const [surname, ...rest] = name.split(' ')
  return <><b>{surname}</b>{rest.length ? ` ${rest.join(' ')}` : ''}</>
}

const FELL = /^(poginu|poginula|streljan|ubijen|nestao|nestala|umro od ran)/

export function fateLine(f: Fate | undefined, note?: string): string {
  if (!f || !f.type || !FELL.test(f.type) || (note && /pogin|umr|strelj|nesta/i.test(note))) return ''
  return `${f.type}${f.date ? ` ${f.date.replace(/\.$/, '')}.` : ''}${f.place ? ` ${f.place}` : ''}`.replace(/\.?$/, '.').replace(/\.\.$/, '.')
}

export function PersonRow({ p, unitId, book, fate }: { p: Person; unitId: string; book: string; fate?: Fate }) {
  const fell = fateLine(fate, p.note)
  return (
    <li className={s.person}>
      <span className={s.personName}>
        {p.id ? <Link href={recordHref(unitId, p.id)}><Name name={p.name} /></Link> : <Name name={p.name} />}
        {p.hero && <span className={s.hero}>narodni heroj</span>}
      </span>
      <span className={s.personWhen}>{p.when || <i>vreme nije navedeno</i>}</span>
      {(p.note || fell || p.p) && (
        <span className={s.personNote}>
          {[p.note, fell ? fell[0].toUpperCase() + fell.slice(1) : ''].filter(Boolean).join(' ')}
          {p.p && <> <a href={`${book}#page=${p.p}`} target="_blank" rel="noreferrer">strana u knjizi</a></>}
        </span>
      )}
    </li>
  )
}

/** A post's holders, in the order they held it (one without a time last) */
export function PostList({ post, people, unitId, book, fates }: {
  post: string; people: Person[]; unitId: string; book: string; fates: Map<string, Fate>
}) {
  const ordered = [...people].sort((a, b) => (a.start ? 0 : 1) - (b.start ? 0 : 1) || (a.start ?? '').localeCompare(b.start ?? ''))
  return (
    <div className={s.post}>
      {post && <h3>{post}</h3>}
      {ordered.length ? (
        <ol className={s.people}>
          {ordered.map((p, i) => <PersonRow key={`${p.name}${i}`} p={p} unitId={unitId} book={book} fate={p.id ? fates.get(p.id) : undefined} />)}
        </ol>
      ) : <p className={s.unknown}>Nije poznato.</p>}
    </div>
  )
}

export const ROLE: Record<string, string> = {
  komandant: 'komandant', komesar: 'politički komesar', 'zamjenik komandanta': 'zamenik komandanta',
  'zamjenik komesara': 'zamenik ili pomoćnik komesara', 'načelnik štaba': 'načelnik štaba',
  'operativni oficir': 'operativni oficir', 'obavještajni oficir': 'obaveštajni oficir', intendant: 'intendant',
  'referent saniteta': 'referent saniteta', komandir: 'komandir', 'zamjenik komandira': 'zamenik komandira',
  'komandant pozadine': 'komandant pozadine', 'delegat voda': 'politički delegat',
}

/** The posts the entries name, as a list of people (the time as printed, the order by it); with the post named. A
 *  post held "do 8. 10. 1942" or "prvi" comes first: it began with the unit. */
export function postsToPeople(posts: Post[], withRole = false, unitStart = ''): Person[] {
  const seen = new Set<string>()
  return posts
    .filter((p) => (seen.has(`${p.id}${p.role}${p.when}`) ? false : (seen.add(`${p.id}${p.role}${p.when}`), true)))
    .map((p) => ({
      name: p.name, id: p.id,
      when: [withRole ? ROLE[p.role] ?? p.role : '', withRole && p.platoon ? `${p.platoon}. vod` : '', p.when]
        .filter(Boolean).join(', ') || undefined,
      start: (unitStart && /^\s*do\b/i.test(p.when) ? unitStart : p.start) || undefined, hero: p.hero,
    }))
}

/** A post's holder as a row: the time, his portrait, the name, narodni heroj, what became of him, the book's page */
export function Holder({ p, unitId, book, photo, fate }: { p: Person; unitId: string; book: string; photo?: string; fate?: Fate }) {
  const fell = fateLine(fate, p.note)
  return (
    <li className={s.holder}>
      <span className={s.holderWhen}>{p.when ?? <i>vreme nije navedeno</i>}</span>
      <span className={s.holderPhoto}>{photo ? <img src={photo} alt="" loading="lazy" /> : null}</span>
      <span className={s.holderBody}>
        <span className={s.holderName}>
          {p.id ? <Link href={recordHref(unitId, p.id)}><Name name={p.name} /></Link> : <Name name={p.name} />}
        </span>
        {p.hero && <span className={s.holderHero}>Narodni heroj</span>}
        {(p.note || fell) && <span className={s.holderNote}>{[p.note, fell ? fell[0].toUpperCase() + fell.slice(1) : ''].filter(Boolean).join(' ')}</span>}
        {p.p && <a className={s.holderSource} href={`${book}#page=${p.p}`} target="_blank" rel="noreferrer">strana u knjizi</a>}
      </span>
    </li>
  )
}

export const ordered = (people: Person[]) =>
  [...people].sort((a, b) => (a.start ? 0 : 1) - (b.start ? 0 : 1) || (a.start ?? '').localeCompare(b.start ?? ''))

// ---------- the chart: lanes of spans over the war's months

function at(iso: string, start: string, end: string): number {
  const t = (x: string) => new Date(x.length === 7 ? `${x}-01` : x).getTime()
  return Math.min(100, Math.max(0, ((t(iso) - t(start)) / (t(end) - t(start))) * 100))
}

export interface Lane {
  label: string
  spans: (Span & { guess?: boolean })[]
}

export function Lanes({ lanes, start, end }: { lanes: Lane[]; start: string; end: string }) {
  const years: number[] = []
  for (let y = Number(start.slice(0, 4)) + 1; y <= Number(end.slice(0, 4)); y++) years.push(y)
  return (
    <div className={s.chartScroll}>
      <div className={s.chart} role="table" aria-label="Pod čijom je komandom brigada bila i njeni bataljoni">
        <div className={s.chartRow} role="row">
          <span className={s.chartLabel} role="rowheader" />
          <span className={s.chartTrack} role="cell">
            <span className={s.chartYear} style={{ left: 0, transform: 'none' }}>{start.slice(0, 4)}</span>
            {years.map((y) => (
              <span key={y} className={s.chartYear} style={{ left: `${at(`${y}-01-01`, start, end)}%` }}>{y}</span>
            ))}
          </span>
        </div>
        {lanes.map((lane) => (
          <div key={lane.label} className={s.chartRow} role="row">
            <span className={s.chartLabel} role="rowheader">{lane.label}</span>
            <span className={s.chartTrack} role="cell">
              {years.map((y) => <span key={y} className={s.chartTick} style={{ left: `${at(`${y}-01-01`, start, end)}%` }} />)}
              {lane.spans.map((sp) => {
                const left = at(sp.from, start, end)
                const width = Math.max(1.2, at(sp.to, start, end) - left)
                const body = <span className={s.spanText}>{sp.name}</span>
                const title = `${sp.name}: ${day(sp.from)} – ${day(sp.to)}${sp.guess ? ' (vreme približno)' : ''}${sp.note ? `. ${sp.note}` : ''}`
                const cls = `${s.span}${sp.href ? ` ${s.spanLink}` : ''}${sp.guess ? ` ${s.spanGuess}` : ''}`
                return sp.href ? (
                  <Link key={sp.name + sp.from} href={sp.href} className={cls} style={{ left: `${left}%`, width: `${width}%` }} title={title}>{body}</Link>
                ) : (
                  <span key={sp.name + sp.from} className={cls} style={{ left: `${left}%`, width: `${width}%` }} title={title}>{body}</span>
                )
              })}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
