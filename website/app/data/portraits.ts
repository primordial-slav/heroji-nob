import type { Soldier } from '@/app/lib/types'
import { contributionsFor } from '@/app/data/family'

// Photographs of the soldiers themselves, for the record popup and the memorial card: what a family sent through
// "Znam ovog borca" (data/family.ts) comes first, then portraits from a book or the znaci.org gallery listed here.
// A soldier without one gets a stand-in outline (lib/standIn.ts).
export interface Portrait {
  soldierId: string
  file: string          // in website/public/portreti/
  credit: string        // who or where it comes from: 'znaci.org, fotografija 11685'
  href?: string         // the source's page
  focus?: number        // the face's height in the photo, as object-position y (percent; default 30)
}

export const portraits: Portrait[] = []

export interface ShownPortrait {
  src: string
  credit: string
  href?: string
  focus: number
}

export function portraitFor(soldier: Soldier): ShownPortrait | null {
  const ids = [soldier.soldier_id, ...(soldier.other_sources ?? []).map((o) => o.soldier_id)].filter(Boolean) as string[]
  const family = contributionsFor(soldier.soldier_id, ids.slice(1)).find((c) => c.photo)
  if (family?.photo) return { src: `/porodica/${family.photo}`, credit: family.from, focus: 30 }
  const own = portraits.find((p) => ids.includes(p.soldierId))
  return own ? { src: `/portreti/${own.file}`, credit: own.credit, href: own.href, focus: own.focus ?? 30 } : null
}
