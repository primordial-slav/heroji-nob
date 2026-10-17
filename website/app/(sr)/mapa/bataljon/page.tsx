import type { Metadata } from 'next'
import { lettering } from '../fonts'
import Battalion from './Battalion'
import styles from './bataljon.module.css'

// A battalion's war, episode by episode, on close-up sheets in the main map's hand: /mapa/bataljon. Local only, like
// the map page (kept out of git through .git/info/exclude); its text is still written here
export const metadata: Metadata = { title: 'Drugi bataljon „Pekiša Vuksan“', robots: { index: false, follow: false } }

type Params = Promise<Record<string, string | string[] | undefined>>
const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v)

// ?epizoda=vorkapic&korak=2 opens that step
export default async function Page({ searchParams }: { searchParams: Params }) {
  const q = await searchParams
  return (
    <div className={`${styles.wide} ${lettering.variable}`}>
      <Battalion initial={{ epizoda: one(q.epizoda), korak: one(q.korak) }} />
    </div>
  )
}
