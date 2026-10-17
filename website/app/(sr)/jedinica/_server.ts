import { readFileSync } from 'node:fs'
import path from 'node:path'
import index from '@/app/data/portrait-index.json'
import { readUnitFile } from '@/app/lib/unitFiles'
import type { Fate, Post } from './_parts'

/** The posts a unit's own entries name (scripts/make_unit_overview.py) */
export function readPosts(id: string): Post[] {
  const file = path.join(process.cwd(), 'app', '(sr)', 'jedinica', '_data', `${id}.posts.json`)
  try {
    return JSON.parse(readFileSync(file, 'utf-8')) as Post[]
  } catch {
    return []
  }
}

export type Rec = Record<string, string> & { other_sources?: { soldier_id?: string; unit_file?: string }[] }

/** The unit's records, by id, and each one's fate */
export function readRecords(dataFile: string): { list: Rec[]; byId: Map<string, Rec>; fates: Map<string, Fate> } {
  const list = readUnitFile(dataFile) as unknown as Rec[]
  return {
    list,
    byId: new Map(list.map((r) => [r.soldier_id, r])),
    fates: new Map(list.map((r) => [r.soldier_id, { type: r.death_type ?? '', date: r.death_date ?? '', place: r.death_place ?? '' }])),
  }
}

const PORTRAITS = index as Record<string, { f: string; same?: string }>

/** A soldier's portrait: his own record's, or one a record linked to his has (the same man in another unit's book) */
export function portraitOf(rec: Rec | undefined): string | undefined {
  if (!rec) return undefined
  const ids = [rec.soldier_id, ...(rec.other_sources ?? []).filter((o) => o.unit_file).map((o) => o.soldier_id ?? '')]
  const hit = ids.find((i) => PORTRAITS[i])
  return hit ? `/portreti/${PORTRAITS[hit].f}` : undefined
}
