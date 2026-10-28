import { placeSplit } from '@/app/lib/placeFiles'

// For a shard of ids (app/lib/placeFiles.ts): which chunk of places each soldier's place is in (w), and each
// soldier's set of embroidered frames (v), written as a static file at build time; any other address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  const { where, vez } = placeSplit()
  return [...new Set([...where.keys(), ...vez.keys()])].map((shard) => ({ shard }))
}

export async function GET(_request: Request, { params }: { params: Promise<{ shard: string }> }) {
  const { shard } = await params
  const { where, vez } = placeSplit()
  return Response.json({ w: where.get(shard) ?? {}, v: vez.get(shard) ?? {} })
}
