import fs from 'fs'
import path from 'path'
import { PLACE_CHUNK_BYTES, placeShard, type PlaceRow } from './relations'

// The places index (public/relations/places.json, written by scripts/build_relations.py) cut into the small files
// the record dialog loads (lib/dataFiles.ts; scripts/prepare-data.ts writes them): a soldier's id leads to a shard
// that says which chunk his place is in and where, and the chunk holds the place with its people. So opening a record
// loads two small files instead of every place. The shard also gives each soldier's set of embroidered frames
// (data/vez-sets.json, written by scripts/build_vez.py; lib/vez.ts), a number and no more.

interface PlaceSplit {
  /** The places, about PLACE_CHUNK_BYTES of them a chunk, a large place alone */
  chunks: PlaceRow[][]
  /** For each shard of ids (placeShard), where each soldier's place is: [chunk, place in it] */
  where: Map<string, Record<string, [number, number]>>
  /** For each shard of ids, each soldier's set of frames (none where he has the neutral set) */
  vez: Map<string, Record<string, number>>
}

export const PLACES_FILE = path.join('public', 'relations', 'places.json')
export const VEZ_FILE = path.join('data', 'vez-sets.json')

export function placeSplit(): PlaceSplit {
  const file = path.join(process.cwd(), PLACES_FILE)
  const vezFile = path.join(process.cwd(), VEZ_FILE)
  const doc: { files: string[]; places: [string, string, [string, string, number, string][]][] } =
    JSON.parse(fs.readFileSync(file, 'utf8'))
  const chunks: PlaceRow[][] = []
  const where = new Map<string, Record<string, [number, number]>>()
  let size = Infinity
  for (const [village, municipality, rows] of doc.places) {
    const place: PlaceRow = [village, municipality, rows.map(([id, name, f, years]) => [id, name, doc.files[f], years])]
    const bytes = JSON.stringify(place).length
    if (size + bytes > PLACE_CHUNK_BYTES) {
      chunks.push([])
      size = 0
    }
    const chunk = chunks.length - 1
    const at = chunks[chunk].push(place) - 1
    size += bytes
    for (const [id] of rows) {
      const shard = placeShard(id)
      let ids = where.get(shard)
      if (!ids) where.set(shard, (ids = {}))
      ids[id] = [chunk, at]
    }
  }
  const vez = new Map<string, Record<string, number>>()
  for (const [id, set] of Object.entries(JSON.parse(fs.readFileSync(vezFile, 'utf8')) as Record<string, number>)) {
    const shard = placeShard(id)
    let ids = vez.get(shard)
    if (!ids) vez.set(shard, (ids = {}))
    ids[id] = set
  }
  return { chunks, where, vez }
}
