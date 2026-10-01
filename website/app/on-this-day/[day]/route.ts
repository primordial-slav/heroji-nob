import { units } from '@/app/data/units'
import { dayKey, encodeRow, listOnce, type PlacedRow } from '@/app/lib/searchIndex'
import { wartimeDeath } from '@/app/lib/deathDay'
import { readUnitFile } from '@/app/lib/unitFiles'
import type { Soldier } from '@/app/lib/types'

// "Na današnji dan" (components/OnThisDay.tsx) for each day of the year, /on-this-day/<MM-DD>: the soldiers who
// fell, died or went missing on it during the war, each soldier once, as the home page lists them. Written as
// static files at build time, so the home page loads only the visitor's day; any other address is a 404.
export const dynamic = 'force-static'
export const dynamicParams = false

const DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

export function generateStaticParams() {
  return DAYS_IN_MONTH.flatMap((days, m) => Array.from({ length: days }, (_, d) => ({ day: dayKey(m + 1, d + 1) })))
}

// Every day's list, worked out once and again only when a data file changes (under `next dev`)
let built: { files: Soldier[][]; days: Map<string, PlacedRow[]> } | null = null

function fallenByDay(): Map<string, PlacedRow[]> {
  const files = units.map((unit) => readUnitFile(unit.dataFile))
  if (built && built.files.every((file, i) => file === files[i])) return built.days

  const where = new Map<string, { unit: string; position: number }>()
  const lists = units.map((unit, u) => files[u].map((soldier, position) => {
    where.set(soldier.soldier_id, { unit: unit.id, position })
    return { ...soldier, unit: unit.name }
  }))
  const days = new Map<string, PlacedRow[]>()
  for (const soldier of listOnce(lists)) {
    const death = wartimeDeath(soldier)
    if (!death) continue
    const entry: PlacedRow = { ...where.get(soldier.soldier_id)!, row: encodeRow(soldier) }
    if (soldier.also_units) entry.also = soldier.also_units
    const key = dayKey(death.month, death.day)
    const day = days.get(key)
    if (day) day.push(entry)
    else days.set(key, [entry])
  }
  built = { files, days }
  return days
}

export async function GET(_request: Request, { params }: { params: Promise<{ day: string }> }) {
  const { day } = await params
  return Response.json(fallenByDay().get(day) ?? [])
}
