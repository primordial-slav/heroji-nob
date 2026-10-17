import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeftIcon } from '@/app/components/Icons'
import { BelowSheet, MonthRail, Toolbar } from './Controls'
import { lettering } from './fonts'
import MapSheet from './Sheet'
import { MapProvider } from './state'

// The map page, /mapa: a work in progress, only on localhost while it takes shape (kept out of git through
// .git/info/exclude), unlinked and out of search engines. Its text is still written here; before it ships it moves
// to the messages, in every language.
export const metadata: Metadata = { title: 'Mapa', robots: { index: false, follow: false } }

type Params = Promise<Record<string, string | string[] | undefined>>
const UNIT_PAGES: Record<string, { href: string; name: string }> = {
  'prva-licka': { href: '/jedinica/prva-licka-brigada', name: 'Prva lička proleterska brigada „Marko Orešković“' },
}
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v)

// The address opens the map as it was left, or as a soldier's record asks: see state.tsx
export default async function Page({ searchParams }: { searchParams: Params }) {
  const q = await searchParams
  const initial = {
    unit: one(q.jedinica), view: one(q.prikaz), year: one(q.godina),
    month: one(q.mesec), whole: one(q.cela) === '1',
    place: one(q.mesto), label: one(q.oznaka),
  }
  // back to the unit's page (/jedinica, local only), where its "Ratni put" opened this map
  const back = UNIT_PAGES[initial.unit ?? '']
  return (
    <div className={`container page-content ${lettering.variable}`}>
      {back && <Link href={back.href} className="back-link"><ArrowLeftIcon size={16} /> {back.name}</Link>}
      <h1 className="page-title">Mapa</h1>
      <MapProvider initial={initial}>
        <Toolbar />
        <MapSheet aside={<MonthRail />} below={<BelowSheet />} />
      </MapProvider>
    </div>
  )
}
