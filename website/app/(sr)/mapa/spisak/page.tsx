import type { Metadata } from 'next'
import KilledList from '../KilledList'

// The killed behind a count on the map (/mapa/spisak): local like the map, unlinked and out of search engines
export const metadata: Metadata = { title: 'Poginuli · Mapa', robots: { index: false, follow: false } }

export default function Page() {
  return (
    <div className="container page-content">
      <KilledList />
    </div>
  )
}
