import { units } from '@/app/data/units'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import { eachListedOnce, encodeRow, type PlacedRow } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'
import type { Soldier } from '@/app/lib/types'

// The soldiers whose portraits drift up the home page's margins (components/PortraitRails.tsx), as the home page
// lists them, so the faces get their names without the page loading every soldier. Written as a static file at
// build time.
export const dynamic = 'force-static'

export function GET() {
  const lists = units.map((unit) => readUnitFile(unit.dataFile).map((soldier) => ({ ...soldier, unit: unit.name })))
  const starts = lists.reduce<number[]>((at, list) => [...at, at[at.length - 1] + list.length], [0])
  const listed: { soldier: Soldier; also: string[]; at: number }[] = []
  eachListedOnce(lists, (soldier, also, at) => listed.push({ soldier, also, at }))

  // As PortraitRails finds them: a portrait is filed under the soldier's own id, or under one his entry had before
  const byId = new Map<string, number>()
  listed.forEach(({ soldier }, k) => {
    byId.set(soldier.soldier_id, k)
    for (const o of soldier.other_sources ?? []) if (o.soldier_id && !byId.has(o.soldier_id)) byId.set(o.soldier_id, k)
  })
  // In the order of the list, so the page's own lookup among them finds each as it would among everyone
  const wanted = [...new Set(WARTIME_PORTRAITS.map((id) => byId.get(id)).filter((k): k is number => k !== undefined))]
    .sort((a, b) => a - b)
  const people: PlacedRow[] = wanted.map((k) => {
    const { soldier, also, at } = listed[k]
    const u = starts.findIndex((start, i) => at >= start && at < starts[i + 1])
    const entry: PlacedRow = { unit: units[u].id, position: at - starts[u], row: encodeRow(soldier) }
    if (also.length) entry.also = also
    return entry
  })
  return Response.json(people)
}
