import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../lib/db'
import { loadAllSoldiers, getRandomSoldiers } from '../../lib/soldiers'
import { detectSuspicious, detectDuplicates } from '../../lib/heuristics'
import { getBrigadeCode, getBrigadeName } from '../../lib/brigades'
import type { SoldierSample } from '../../lib/types'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const type = searchParams.get('type') || 'random'
  const count = Math.min(parseInt(searchParams.get('count') || '10', 10), 50)

  const db = getDb()

  // Get already-reviewed soldier IDs
  const reviewed = db.prepare('SELECT soldier_id FROM reviews').all() as { soldier_id: string }[]
  const reviewedIds = new Set(reviewed.map(r => r.soldier_id))

  if (type === 'random') {
    const soldiers = getRandomSoldiers(count, reviewedIds)
    const samples: SoldierSample[] = soldiers.map(s => {
      const code = getBrigadeCode(s.soldier_id)
      return {
        soldier: s,
        brigadeName: getBrigadeName(code),
        brigadeCode: code,
        flags: [],
      }
    })
    return NextResponse.json({ samples })
  }

  // Suspicious samples
  const { soldiers } = loadAllSoldiers()
  const duplicates = detectDuplicates(soldiers)

  const suspicious: SoldierSample[] = []

  for (const soldier of soldiers) {
    if (reviewedIds.has(soldier.soldier_id)) continue

    const flags = detectSuspicious(soldier)
    if (duplicates.has(soldier.soldier_id)) {
      flags.push('duplicate_name')
    }

    if (flags.length > 0) {
      const code = getBrigadeCode(soldier.soldier_id)
      suspicious.push({
        soldier,
        brigadeName: getBrigadeName(code),
        brigadeCode: code,
        flags,
      })
    }
  }

  // Shuffle and take N
  for (let i = suspicious.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [suspicious[i], suspicious[j]] = [suspicious[j], suspicious[i]]
  }

  return NextResponse.json({ samples: suspicious.slice(0, count) })
}
