import Link from 'next/link'
import { notFound } from 'next/navigation'
import { units } from '@/app/data/units'
import { ArrowLeftIcon } from '@/app/components/Icons'
import { EPISODES } from '@/app/(sr)/mapa/bataljon/episodes'
import * as PL from '../../../_data/prva-licka-brigada'
import type { Battalion, Person } from '../../../_data/prva-licka-brigada'
import { Holder, Lanes, Name, ROLE, day, ordered, postsToPeople, recordHref, type Post } from '../../../_parts'
import { portraitOf, readPosts, readRecords } from '../../../_server'
import s from '../../../jedinica.module.css'

// A battalion number of the brigade (local only), and the battalions that bore it one after another: for each, its
// time in the brigade and what it came from, its fights (the 2. bataljon's, from the battalion page on the map), its
// staff, its companies and platoons with whoever the entries name in them (nobody known is said), and its soldiers.

const DATA: Record<string, typeof PL> = { 'prva-licka-brigada': PL }

// Built with the site: the unit files are read at build time (a server function on Vercel has none of public/)
export const dynamicParams = false
export function generateStaticParams() {
  return Object.entries(DATA).flatMap(([id, d]) => d.BATTALIONS.map((b) => ({ id, bataljon: b.slug })))
}
const FELL = /^(poginu|streljan|ubijen|nestao|nestala)/
const n = (x: number) => x.toLocaleString('de-DE')
// whose battalion a post of the entries is: its number, or the number and the kind ("3kordunašk")
const POST_KEY: Record<string, (b: string | null) => boolean> = {
  '1-bataljon': (b) => b === '1',
  '2-bataljon': (b) => b === '2',
  '3-bataljon': (b) => b === '3',
  '4-bataljon': (b) => b === '4',
  '3-kordunaski': (b) => /kordunašk/.test(b ?? ''),
  '4-banijski': (b) => /banijsk/.test(b ?? ''),
  '5-mitraljeski': (b) => /mitraljesk/.test(b ?? ''),
  '5-ruski': (b) => /rusk/.test(b ?? ''),
  '5-makedonski': (b) => /makedonsk/.test(b ?? ''),
}
const BATTLES: Record<string, typeof EPISODES> = { '2-bataljon': EPISODES }
const OTHER_ROLES = ['zamjenik komandanta', 'zamjenik komesara', 'operativni oficir', 'obavještajni oficir', 'intendant', 'referent saniteta']

function CompanyTable({ rows, unitId, empty }: { rows: { label: string; people: Person[] }[]; unitId: string; empty: string }) {
  return (
    <table className={s.table}>
      <tbody>
        {rows.flatMap(({ label, people }) => (people.length ? people : [null]).map((p, i) => (
          <tr key={`${label}${i}`}>
            <td className={s.tableKey}>{i === 0 ? label : ''}</td>
            {p ? (
              <>
                <td className={s.tableName}>{p.id ? <Link href={recordHref(unitId, p.id)}><Name name={p.name} /></Link> : <Name name={p.name} />}</td>
                <td>{p.when}{p.note ? <span className={s.muted}> {p.note}</span> : null}</td>
              </>
            ) : <td colSpan={2} className={s.unknown}>{empty}</td>}
          </tr>
        )))}
      </tbody>
    </table>
  )
}

export default async function BattalionPage({ params }: { params: Promise<{ id: string; bataljon: string }> }) {
  const { id, bataljon } = await params
  const unit = units.find((u) => u.id === id)
  const data = DATA[id]
  const bat = data?.BATTALIONS.find((b) => b.slug === bataljon)
  if (!unit || !data || !bat) notFound()
  // the others that bore the same number, before or after it: different battalions, with their own men and companies
  const sameNo = data.BATTALIONS.filter((b) => b.short[0] === bat.short[0])

  const recs = readRecords(unit.dataFile)
  const allPosts = readPosts(id)
  const lanes = [
    { label: `${bat.short[0]}. bataljon`, spans: sameNo.map((b) => ({ name: b.short.slice(3), from: b.from, to: b.to, note: b.origin, href: b.slug === bat.slug ? undefined : `/jedinica/${id}/bataljoni/${b.slug}` })) },
    ...data.COMMAND.slice(0, 1),
  ]

  const section = (bat: Battalion) => {
    const mine = recs.list.filter((r) => bat.detail.some((d) => r.unit_detail === d || (r.unit_detail ?? '').endsWith(`, ${d}`)))
    const fallen = mine.filter((r) => FELL.test(r.death_type ?? ''))
    const posts = allPosts.filter((p) => POST_KEY[bat.slug]?.(p.battalion))
    const staff = data.BATTALION_STAFF[bat.slug] ?? []
    const named = new Set(staff.flatMap((x) => x.people.map((p) => p.id)).filter(Boolean))
    const more = (role: string) => postsToPeople(posts.filter((p: Post) => p.level === 'bataljon' && p.role === role && !named.has(p.id)), false, bat.from)
    const lists = [
      ...['Komandant', 'Politički komesar'].map((post) => ({
        post, people: [...(staff.find((x) => x.post === post)?.people ?? []), ...more(post === 'Komandant' ? 'komandant' : 'komesar')],
      })),
      ...staff.filter((x) => !['Komandant', 'Politički komesar'].includes(x.post)),
      ...OTHER_ROLES.map((role) => ({
        post: ROLE[role][0].toUpperCase() + ROLE[role].slice(1),
        people: postsToPeople(posts.filter((p) => p.level === 'bataljon' && p.role === role), false, bat.from),
      })).filter((x) => x.people.length && !staff.some((y) => y.post.toLowerCase() === x.post.toLowerCase())),
    ]
    const companyPosts = posts.filter((p) => p.level === 'četa')
    const curated = data.COMPANY_STAFF[bat.slug] ?? {}
    const numbered = [...new Set(['1', '2', '3', '4', ...companyPosts.map((p) => p.company ?? '').filter((c) => /^\d$/.test(c))])].sort()
    const companyRows = numbered.map((c) => ({
      label: `${c}. četa`,
      people: ordered([...(curated[c] ?? []), ...postsToPeople(companyPosts.filter((p) => p.company === c), true, bat.from)]),
    }))
    const special = [...new Set(companyPosts.map((p) => p.company ?? '').filter((c) => c && !/^\d$/.test(c)))]
    const specialRows = special.map((c) => ({
      label: `${c[0].toUpperCase()}${c.slice(1)}a četa`,
      people: ordered(postsToPeople(companyPosts.filter((p) => p.company === c), true, bat.from)),
    }))
    const unknownCompany = ordered([...(curated['?'] ?? []), ...postsToPeople(companyPosts.filter((p) => !p.company), true, bat.from)])
    const platoons = posts.filter((p) => p.level === 'vod')
    const platoonRows = numbered.map((c) => ({
      label: `${c}. četa`,
      people: ordered(postsToPeople(platoons.filter((p) => p.company_of_platoon === c), true, bat.from)),
    })).filter((r) => r.people.length)
    const platoonsNoCompany = ordered(postsToPeople(platoons.filter((p) => !p.company_of_platoon), true, bat.from))
    const battles = BATTLES[bat.slug] ?? []

    return (
      <article className={s.batSection}>
        <dl className={s.facts}>
          <dt>U brigadi</dt>
          <dd>{day(bat.from)} – {bat.to === data.END ? 'kraj rata' : day(bat.to)}</dd>
          <dt>Nastao od</dt>
          <dd>
            {bat.origin}
            {bat.p && <> <a href={`${data.BOOK}#page=${bat.p}`} target="_blank" rel="noreferrer">strana u knjizi</a></>}
          </dd>
          {bat.after && <><dt>Posle</dt><dd>{bat.after}</dd></>}
        </dl>
        <div className={s.buttons}>
          {battles.length > 0 && <Link href="/mapa/bataljon" className="btn btn-primary">Borbe bataljona na karti</Link>}
          <a href={`#${bat.slug}-borci`} className="btn btn-secondary">Borci ({n(mine.length)})</a>
          <a href={`#${bat.slug}-borci`} className="btn btn-secondary">Poginuli ({n(fallen.length)})</a>
        </div>

        {battles.length > 0 && (
          <>
            <h3 className={s.subhead}>Borbe bataljona</h3>
            <ol className={s.events}>
              {battles.map((e) => (
                <li key={e.key}>
                  <time dateTime={e.start}>{e.dates}</time>
                  <span>
                    <Link href={`/mapa/bataljon?epizoda=${e.key}`}><b>{e.title}</b></Link>. {e.about}
                    {e.fallen?.length ? <span className={s.muted}> Poginulo: {e.fallen.length}.</span> : null}
                  </span>
                </li>
              ))}
            </ol>
          </>
        )}

        <h3 className={s.subhead}>Štab bataljona</h3>
        {lists.map((x) => (
          <div key={x.post} className={s.staffPost}>
            <h4>{x.post}</h4>
            {x.people.length ? (
              <ol className={s.holders}>
                {ordered(x.people).map((p, i) => (
                  <Holder key={`${p.name}${i}`} p={p} unitId={id} book={data.BOOK}
                          photo={portraitOf(p.id ? recs.byId.get(p.id) : undefined)} fate={p.id ? recs.fates.get(p.id) : undefined} />
                ))}
              </ol>
            ) : <p className={s.unknown}>Nije poznato.</p>}
          </div>
        ))}

        <h3 className={s.subhead}>Čete</h3>
        <CompanyTable rows={[...companyRows, ...specialRows]} unitId={id} empty="Starešine nisu poznate." />
        {unknownCompany.length > 0 && (
          <details className={s.fold}>
            <summary>Starešine čete za koje zapis ne kaže koja je četa ({unknownCompany.length})</summary>
            <CompanyTable rows={[{ label: '', people: unknownCompany }]} unitId={id} empty="" />
          </details>
        )}

        <h3 className={s.subhead}>Vodovi</h3>
        {platoonRows.length ? <CompanyTable rows={platoonRows} unitId={id} empty="" /> : <p className={s.unknown}>Komandiri vodova po četama nisu poznati.</p>}
        {platoonsNoCompany.length > 0 && (
          <details className={s.fold}>
            <summary>Komandiri vodova za koje zapis ne kaže koja je četa ({platoonsNoCompany.length})</summary>
            <CompanyTable rows={[{ label: '', people: platoonsNoCompany }]} unitId={id} empty="" />
          </details>
        )}

        <h3 className={s.subhead} id={`${bat.slug}-borci`}>Borci</h3>
        <p className={s.muted}>Borci čiji zapis navodi ovaj bataljon. Mnogi zapisi bataljon ne navode, pa ih ovde nema.</p>
        <details className={s.fold}>
          <summary>Poginuli ({n(fallen.length)})</summary>
          <ul className={s.names}>
            {fallen.map((r) => (
              <li key={r.soldier_id}><Link href={recordHref(id, r.soldier_id)}><Name name={r.full_name} /></Link> <span className={s.muted}>{r.death_date}</span></li>
            ))}
          </ul>
        </details>
        <details className={s.fold}>
          <summary>Svi borci ({n(mine.length)})</summary>
          <ul className={s.names}>
            {mine.map((r) => <li key={r.soldier_id}><Link href={recordHref(id, r.soldier_id)}><Name name={r.full_name} /></Link></li>)}
          </ul>
        </details>
      </article>
    )
  }

  const before = sameNo.filter((b) => b.from < bat.from)
  const after = sameNo.filter((b) => b.from > bat.from)
  return (
    <div className={`container ${s.page}`}>
      <Link href={`/jedinica/${id}/bataljoni`} className="back-link"><ArrowLeftIcon size={16} /> Bataljoni</Link>
      <h1 className={s.title}>{bat.name}</h1>
      {(before.length > 0 || after.length > 0) && (
        <p className={s.lead}>
          {before.length > 0 && <>Pre njega je broj {bat.short[0]} nosio {before.map((b, i) => <span key={b.slug}>{i ? ', zatim ' : ''}<Link href={`/jedinica/${id}/bataljoni/${b.slug}`}>{b.short.slice(3)}</Link></span>)}. </>}
          {after.length > 0 && <>Posle njega {after.length > 1 ? 'su ga nosili' : 'ga je nosio'} {after.map((b, i) => <span key={b.slug}>{i ? ', zatim ' : ''}<Link href={`/jedinica/${id}/bataljoni/${b.slug}`}>{b.short.slice(3)}</Link></span>)}. </>}
          To su različiti bataljoni, s drugim ljudima i četama.
        </p>
      )}
      <Lanes lanes={lanes} start={data.START} end={data.END} />
      {section(bat)}
    </div>
  )
}
