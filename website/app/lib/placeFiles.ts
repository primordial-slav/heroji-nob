import fs from 'fs'
import path from 'path'
import { PLACE_CHUNK_BYTES, placeShard, type PlaceRow } from './relations'

// Server only: the places index (public/relations/places.json, written by scripts/build_relations.py) cut into the
// small files the record dialog loads (app/places/): a soldier's id leads to a shard that says which chunk his place
// is in and where, and the chunk holds the place with its people. So opening a record loads two small files instead
// of every place. Read once per change of the index.

interface PlaceSplit {
  /** The places, about PLACE_CHUNK_BYTES of them a chunk, a large place alone */
  chunks: PlaceRow[][]
  /** For each shard of ids (placeShard), where each soldier's place is: [chunk, place in it] */
  where: Map<string, Record<string, [number, number]>>
}

let cached: { mtime: number; split: PlaceSplit } | null = null

export function placeSplit(): PlaceSplit {
  const file = path.join(process.cwd(), 'public', 'relations', 'places.json')
  const mtime = fs.statSync(file).mtimeMs
  if (cached && cached.mtime === mtime) return cached.split
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
  cached = { mtime, split: { chunks, where } }
  return cached.split
}
