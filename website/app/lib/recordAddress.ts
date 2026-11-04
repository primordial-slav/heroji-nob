import { wherePath } from './dataFiles'

// A record's own address needs only its id: where the record is comes from small files scripts/prepare-data.ts writes
// (public/data/where/<first 7 digits of the id>.json), read by the page and by the route that answers the address
// (lib/recordAnswer.ts) alike, so that neither has to wake the search for it.

/** A thousand ids' records: their unit and, by the id's last 3 digits, the slice of its records (lib/dataFiles.ts) that
 * holds each. An id merged into another record, which old links may still use, gives that record's id with the slice. */
export interface WhereShard {
  u: string
  p: Record<string, number | [number, string]>
}

export interface RecordPlace {
  unit: string
  /** The record's id, which is another than the one asked for where that one was merged into it */
  id: string
  part: number
}

export const isRecordId = (id: string) => /^\d{10}$/.test(id)

export function placeIn(shard: WhereShard, id: string): RecordPlace | null {
  const at = shard.p[id.slice(7)]
  if (at === undefined) return null
  return Array.isArray(at) ? { unit: shard.u, id: at[1], part: at[0] } : { unit: shard.u, id, part: at }
}

/** Where the record of an id is, null if there is none */
export async function locateRecord(id: string): Promise<RecordPlace | null> {
  if (!isRecordId(id)) return null
  const response = await fetch(wherePath(id))
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`${wherePath(id)}: ${response.status}`)
  return placeIn(await response.json(), id)
}
