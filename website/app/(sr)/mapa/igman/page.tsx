import type { Metadata } from 'next'
import IgmanList from './IgmanList'

// The men of the Prva proleterska on the Igman march (/mapa/igman): local like the map, unlinked and out of search
// engines until the list is checked
export const metadata: Metadata = { title: 'Igmanski marš · Prva proleterska', robots: { index: false, follow: false } }

export default function Page() {
  return (
    <div className="container page-content">
      <IgmanList />
    </div>
  )
}
