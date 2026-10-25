import { encodeRow, SEARCH_INDEX_PARTS, type SearchIndex } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// A part of the home page's search list (app/lib/searchIndex.ts), written as a static file at build time; any
// other address is a 404. A part holds whole units, or a slice of a large one's rows.
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return SEARCH_INDEX_PARTS.map((_, part) => ({ part: String(part) }))
}

export async function GET(_request: Request, { params }: { params: Promise<{ part: string }> }) {
  const slices = SEARCH_INDEX_PARTS[Number((await params).part)]
  if (!slices) return new Response('Not found', { status: 404 })
  const index: SearchIndex = Object.fromEntries(
    slices.map(({ unit, start, end }) => [unit.dataFile, readUnitFile(unit.dataFile).slice(start, end).map(encodeRow)]))
  return Response.json(index)
}
