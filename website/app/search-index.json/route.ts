import { units } from '@/app/data/units'
import { encodeRow, type SearchIndex } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// The home page's search list (app/lib/searchIndex.ts), written as a static file at build time
export const dynamic = 'force-static'

export function GET() {
  const index: SearchIndex = Object.fromEntries(
    units.map((unit) => [unit.dataFile, readUnitFile(unit.dataFile).map(encodeRow)]),
  )
  return Response.json(index)
}
