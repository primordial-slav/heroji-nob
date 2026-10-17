import type { Metadata } from 'next'

// The unit overview pages: a work in progress, not linked from the site yet and kept out of search engines, as the
// map is. Their text is still written in the pages; before they ship it moves to the messages, in every language.
export const metadata: Metadata = { title: 'Jedinica', robots: { index: false, follow: false } }

export default function UnitOverviewLayout({ children }: { children: React.ReactNode }) {
  return children
}
