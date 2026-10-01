import { units } from '@/app/data/units'
import { encodeRow } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// A unit page's list (app/lib/searchIndex.ts): the unit's soldiers in the search index's short form, written as a
// static file at build time; any other address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return units.map((unit) => ({ unit: unit.id }))
}

export async function GET(_request: Request, { params }: { params: Promise<{ unit: string }> }) {
  const { unit: id } = await params
  const unit = units.find((u) => u.id === id)
  if (!unit) return new Response('Not found', { status: 404 })
  return Response.json(readUnitFile(unit.dataFile).map(encodeRow))
}
