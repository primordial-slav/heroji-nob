import { units } from '@/app/data/units'
import { RECORDS_PER_PART } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// Full records for the home page, RECORDS_PER_PART at a time (app/lib/searchIndex.ts), written as static files
// at build time; any other address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return units.flatMap((unit) => {
    const parts = Math.ceil(readUnitFile(unit.dataFile).length / RECORDS_PER_PART)
    return Array.from({ length: parts }, (_, part) => ({ unit: unit.id, part: String(part) }))
  })
}

export async function GET(_request: Request, { params }: { params: Promise<{ unit: string; part: string }> }) {
  const { unit: id, part } = await params
  const unit = units.find((u) => u.id === id)
  const start = Number(part) * RECORDS_PER_PART
  if (!unit || !Number.isInteger(start)) return new Response('Not found', { status: 404 })
  return Response.json(readUnitFile(unit.dataFile).slice(start, start + RECORDS_PER_PART))
}
