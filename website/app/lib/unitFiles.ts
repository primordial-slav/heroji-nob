import fs from 'fs'
import path from 'path'
import type { LifeEvent, Soldier } from './types'

// Server only: a unit's data file (public/<dataFile>), read once per change of the file. The caches live on
// globalThis: Next compiles each page and route into a bundle of its own, each with its own copy of this module,
// and a cache per copy held the whole data once for every route that read it (about 1 GB each under next dev)
const shared = globalThis as unknown as {
  unitFileCache?: Map<string, { mtime: number; soldiers: Soldier[] }>
  lifeEventCache?: Map<string, { mtime: number; events: Record<string, LifeEvent[]> }>
}
const cache = (shared.unitFileCache ??= new Map())

export function readUnitFile(dataFile: string): Soldier[] {
  const file = path.join(process.cwd(), 'public', dataFile)
  const mtime = fs.statSync(file).mtimeMs
  const cached = cache.get(dataFile)
  if (cached && cached.mtime === mtime) return cached.soldiers
  const soldiers: Soldier[] = JSON.parse(fs.readFileSync(file, 'utf8'))
  cache.set(dataFile, { mtime, soldiers })
  return soldiers
}

// The dated steps of the unit's soldiers who have a line (data/life-events/<dataFile>, written by
// scripts/extract_life_events.py), by soldier_id; a unit none of whose soldiers has one has no file
const eventCache = (shared.lifeEventCache ??= new Map())

export function readLifeEvents(dataFile: string): Record<string, LifeEvent[]> {
  const file = path.join(process.cwd(), 'data', 'life-events', dataFile)
  if (!fs.existsSync(file)) return {}
  const mtime = fs.statSync(file).mtimeMs
  const cached = eventCache.get(dataFile)
  if (cached && cached.mtime === mtime) return cached.events
  const events: Record<string, LifeEvent[]> = JSON.parse(fs.readFileSync(file, 'utf8'))
  eventCache.set(dataFile, { mtime, events })
  return events
}
