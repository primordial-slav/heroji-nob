import fs from 'fs'
import path from 'path'
import { BRIGADE_MAP, getBrigadeCode } from './brigades'
import type { Soldier } from './types'

const DATA_DIR = path.join(process.cwd(), '..', 'website', 'public')

let cache: { soldiers: Soldier[], byBrigade: Map<number, Soldier[]> } | null = null

export function loadAllSoldiers(): { soldiers: Soldier[], byBrigade: Map<number, Soldier[]> } {
  if (cache) return cache

  const allSoldiers: Soldier[] = []
  const byBrigade = new Map<number, Soldier[]>()

  for (const [codeStr, config] of Object.entries(BRIGADE_MAP)) {
    const code = parseInt(codeStr, 10)
    const filePath = path.join(DATA_DIR, config.dataFile)

    if (!fs.existsSync(filePath)) {
      console.warn(`Missing data file: ${filePath}`)
      continue
    }

    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8')) as Soldier[]
    byBrigade.set(code, data)
    allSoldiers.push(...data)
  }

  cache = { soldiers: allSoldiers, byBrigade }
  return cache
}

export function getSoldierById(soldierId: string): Soldier | undefined {
  const { soldiers } = loadAllSoldiers()
  return soldiers.find(s => s.soldier_id === soldierId)
}

export function getRandomSoldiers(count: number, excludeIds: Set<string>): Soldier[] {
  const { soldiers } = loadAllSoldiers()
  const available = soldiers.filter(s => !excludeIds.has(s.soldier_id))

  // Fisher-Yates shuffle on a copy, take first N
  const shuffled = [...available]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }

  return shuffled.slice(0, count)
}
