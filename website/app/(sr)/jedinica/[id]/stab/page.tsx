import Link from 'next/link'
import { notFound } from 'next/navigation'
import { units } from '@/app/data/units'
import { ArrowLeftIcon } from '@/app/components/Icons'
import * as PL from '../../_data/prva-licka-brigada'
import { Holder, Lanes, Name, ROLE, ordered, postsToPeople, recordHref } from '../../_parts'
import { portraitOf, readPosts, readRecords } from '../../_server'
import s from '../../jedinica.module.css'

// The brigade's staff (local only): who held which post when, first as a chart, then each post's holders in order,
// each with the time the book or his entry gives, his portrait where there is one, what became of him, and the page
// of the book; then the other officers of the staff and the companies under it, as the entries name them.

const DATA: Record<string, typeof PL> = { 'prva-licka-brigada': PL }

// Built with the site: the unit files are read at build time (a server function on Vercel has none of public/)
export const dynamicParams = false
export function generateStaticParams() {
  return Object.keys(DATA).map((id) => ({ id }))
}
const COMPANY: Record<string, string> = {
  izviđačk: 'Izviđačka četa', prateć: 'Prateća četa', inžinjerijsk: 'Inžinjerijska četa', sanitetsk: 'Sanitetska četa',
  protivavionske: 'Protivavionska četa', protivkolske: 'Protivavionska četa', štabn: 'Štabna četa',
}

export default async function StaffPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const unit = units.find((u) => u.id === id)
  const data = DATA[id]
  if (!unit || !data) notFound()

  const recs = readRecords(unit.dataFile)
  const posts = readPosts(id)
  const others = ['operativni oficir', 'obavještajni oficir', 'intendant', 'referent saniteta', 'komandant pozadine']
  const otherRows = others.flatMap((role) =>
    ordered(postsToPeople(posts.filter((p) => p.level === 'brigada' && p.role === role), false, data.START)).map((p) => ({ role, p })))
  const companies = posts.filter((p) => p.level === 'četa' && p.company && !/^\d$/.test(p.company))
  const companyKeys = [...new Set(companies.map((c) => COMPANY[c.company!] ?? c.company!))]
  const lanes = data.STAFF_CHART.map((x) => ({
    label: x.post, spans: x.spans.map((sp) => ({ name: sp.name, from: sp.from, to: sp.to, guess: sp.guess })),
  }))

  return (
    <div className={`container ${s.page}`}>
      <Link href={`/jedinica/${id}`} className="back-link"><ArrowLeftIcon size={16} /> {unit.name.replace(/"([^"]+)"/, '„$1“')}</Link>
      <h1 className={s.title}>Štab brigade</h1>
      <p className={s.lead}>
        Ko je bio na kojoj dužnosti i kada, kako to piše u knjizi brigade i u zapisima boraca. Vreme je navedeno onako
        kako ga knjiga daje. Ime vodi na zapis borca.
      </p>

      <section aria-labelledby="pregled">
        <h2 id="pregled" className={s.head}>Ko je kada bio na dužnosti</h2>
        <Lanes lanes={lanes} start={data.START} end={data.END} />
        <p className={s.muted}>Isprekidano: vreme je približno, iz toga kad je dužnost preuzeo sledeći.</p>
      </section>

      {data.STAFF.map((x) => (
        <section key={x.post} className={s.section} aria-label={x.post}>
          <h2 className={s.head}>{x.post}</h2>
          <ol className={s.holders}>
            {ordered(x.people).map((p, i) => (
              <Holder key={`${p.name}${i}`} p={p} unitId={id} book={data.BOOK} photo={portraitOf(p.id ? recs.byId.get(p.id) : undefined)} fate={p.id ? recs.fates.get(p.id) : undefined} />
            ))}
          </ol>
        </section>
      ))}

      <section className={s.section} aria-labelledby="ostali">
        <h2 id="ostali" className={s.head}>Ostale dužnosti u štabu</h2>
        <p className={s.lead}>Operativni i obaveštajni oficiri, intendanti i referenti saniteta, kako ih navode zapisi boraca.</p>
        <table className={s.table}>
          <thead><tr><th>Dužnost</th><th>Ime</th><th>Vreme</th></tr></thead>
          <tbody>
            {otherRows.map(({ role, p }, i) => (
              <tr key={`${role}${p.id}${i}`}>
                <td>{otherRows[i - 1]?.role === role ? '' : ROLE[role][0].toUpperCase() + ROLE[role].slice(1)}</td>
                <td className={s.tableName}>{p.id ? <Link href={recordHref(id, p.id)}><Name name={p.name} /></Link> : <Name name={p.name} />}</td>
                <td>{p.when ?? <i className={s.muted}>nije navedeno</i>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {companyKeys.length > 0 && (
        <section className={s.section} aria-labelledby="cete">
          <h2 id="cete" className={s.head}>Čete pri štabu brigade</h2>
          <table className={s.table}>
            <thead><tr><th>Četa</th><th>Ime</th><th>Dužnost i vreme</th></tr></thead>
            <tbody>
              {companyKeys.flatMap((key) => {
                const people = ordered(postsToPeople(companies.filter((c) => (COMPANY[c.company!] ?? c.company) === key), true, data.START))
                return people.map((p, i) => (
                  <tr key={`${key}${p.id}${i}`}>
                    <td>{i === 0 ? key : ''}</td>
                    <td className={s.tableName}>{p.id ? <Link href={recordHref(id, p.id)}><Name name={p.name} /></Link> : <Name name={p.name} />}</td>
                    <td>{p.when}</td>
                  </tr>
                ))
              })}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}
