import { placeSplit } from '@/app/lib/placeFiles'

// A chunk of places with their people (app/lib/placeFiles.ts), written as a static file at build time; any other
// address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return placeSplit().chunks.map((_, n) => ({ n: String(n) }))
}

export async function GET(_request: Request, { params }: { params: Promise<{ n: string }> }) {
  const { n } = await params
  const chunk = placeSplit().chunks[Number(n)]
  if (!chunk) return new Response('Not found', { status: 404 })
  return Response.json(chunk)
}
