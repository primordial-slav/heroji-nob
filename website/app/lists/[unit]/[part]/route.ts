import { units } from '@/app/data/units'
import { encodeRow, unitSlices } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// A unit page's list (app/lib/searchIndex.ts): the unit's soldiers in the search index's short form, written as a
// static file at build time, in the search list's slices of the unit (one for all but the largest units:
// /lists/<unit id>/0); any other address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return units.flatMap((unit) => unitSlices(unit).map((_, part) => ({ unit: unit.id, part: String(part) })))
}

export async function GET(_request: Request, { params }: { params: Promise<{ unit: string; part: string }> }) {
  const { unit: id, part } = await params
  const unit = units.find((u) => u.id === id)
  const slice = unit && unitSlices(unit)[Number(part)]
  if (!unit || !slice) return new Response('Not found', { status: 404 })
  return Response.json(readUnitFile(unit.dataFile).slice(slice.start, slice.end).map(encodeRow))
}
