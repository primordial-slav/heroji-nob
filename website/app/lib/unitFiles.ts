import fs from 'fs'
import path from 'path'
import type { LifeEvent, Soldier } from './types'

// Server only: a unit's data file (public/<dataFile>), read once per change of the file
const cache = new Map<string, { mtime: number; soldiers: Soldier[] }>()

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
const eventCache = new Map<string, { mtime: number; events: Record<string, LifeEvent[]> }>()

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
