import fs from 'fs'
import path from 'path'
import type { Soldier } from './types'

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
