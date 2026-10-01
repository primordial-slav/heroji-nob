import type { Metadata } from 'next'
import Link from 'next/link'
import { units } from '@/app/data/units'
import { sqQuotes } from '@/app/lib/typography'
import UnitPageClient from './UnitPageClient'

// This tells Next.js which dynamic routes to pre-generate for static export
export function generateStaticParams() {
  return units.map((unit) => ({
    id: unit.id,
  }))
}

// The unit's name and description become the tab title and the text of a shared link
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params
  const unit = units.find(u => u.id === id)
  if (!unit) return { title: 'Knjiga boraca' }
  return { title: `${sqQuotes(unit.name)} · Knjiga boraca`, description: unit.description }
}

export default async function UnitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const unit = units.find(u => u.id === id)

  if (!unit) {
    return (
      <div className="container page-content">
        <h1 className="page-title">Jedinica nije pronađena</h1>
        <Link href="/" className="back-link">← Nazad na početnu</Link>
      </div>
    )
  }

  return <UnitPageClient unit={unit} />
}
