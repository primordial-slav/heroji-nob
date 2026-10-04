import { encodeRow, SEARCH_INDEX_PARTS, type SearchIndex } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// A part of the home page's search list (app/lib/searchIndex.ts), written as a static file at build time; any
// other address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return SEARCH_INDEX_PARTS.map((_, part) => ({ part: String(part) }))
}

export async function GET(_request: Request, { params }: { params: Promise<{ part: string }> }) {
  const units = SEARCH_INDEX_PARTS[Number((await params).part)]
  if (!units) return new Response('Not found', { status: 404 })
  const index: SearchIndex = Object.fromEntries(units.map((unit) => [unit.dataFile, readUnitFile(unit.dataFile).map(encodeRow)]))
  return Response.json(index)
}
