import Link from 'next/link'
import { units } from '@/app/data/units'
import UnitPageClient from './UnitPageClient'

// This tells Next.js which dynamic routes to pre-generate for static export
export function generateStaticParams() {
  return units.map((unit) => ({
    id: unit.id,
  }))
}

export default async function UnitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const unit = units.find(u => u.id === id)

  if (!unit) {
    return (
      <div className="page-content">
        <h1 className="page-title">Jedinica nije pronađena</h1>
        <Link href="/" className="back-link">← Nazad na početnu</Link>
      </div>
    )
  }

  return <UnitPageClient unit={unit} />
}
