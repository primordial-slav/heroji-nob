import { placeSplit } from '@/app/lib/placeFiles'

// Which chunk of places each soldier of a shard of ids is in (app/lib/placeFiles.ts), written as a static file at
// build time; any other address is a 404
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return [...placeSplit().where.keys()].map((shard) => ({ shard }))
}

export async function GET(_request: Request, { params }: { params: Promise<{ shard: string }> }) {
  const { shard } = await params
  return Response.json(placeSplit().where.get(shard) ?? {})
}
