import type { Soldier } from '@/app/lib/types'
import { contributionsFor } from '@/app/data/family'
import index from '@/app/data/portrait-index.json'

// Photographs of the soldiers themselves, for the record popup and the memorial card: what a family sent through
// "Znam ovog borca" (data/family.ts) comes first, then the portraits printed in a soldier's own entry in a book
// (portrait-index.json and website/public/portreti/, by scripts/extract_book_portraits.py: only certain matches).
// A soldier without one gets a stand-in outline (lib/standIn.ts).

interface IndexEntry {
  f: string              // file in website/public/portreti/: the print
  v?: string             // the large photo, where the source is much bigger than the print
  c: string              // where it comes from
  h?: string             // the source's page
  y?: number             // the face's height in the photo, as object-position y (percent)
}

const PORTRAITS = index as Record<string, IndexEntry>

export interface ShownPortrait {
  src: string
  large?: string
  credit: string
  href?: string
  focus: number
}

export function portraitFor(soldier: Soldier): ShownPortrait | null {
  const ids = [soldier.soldier_id, ...(soldier.other_sources ?? []).map((o) => o.soldier_id)].filter(Boolean) as string[]
  const family = contributionsFor(soldier.soldier_id, ids.slice(1)).find((c) => c.photo)
  if (family?.photo) {
    const by = family.photoFrom || family.from || 'porodica' // a sender who did not allow his name: 'porodica'
    // the photo's caption ("U partizanskoj uniformi") stands with the portrait, in its credit line, not alone at the top
    // of the family's note (the user, 2026-11-23, Sarapa Ilija: "why here")
    return { src: `/porodica/${family.photo}`, credit: family.photoCaption ? `${family.photoCaption} · ${by}` : by, focus: 30 }
  }
  const own = ids.map((id) => PORTRAITS[id]).find(Boolean)
  return own
    ? { src: `/portreti/${own.f}`, large: own.v && `/portreti/${own.v}`, credit: own.c, href: own.h, focus: own.y ?? 30 }
    : null
}

/** The book's portrait a family's photo took the place of at the top of the record: it stays in the card's album, under
 *  the family's pieces, with the book's credit (the user, 2026-11-24, Antolović Josip: "leave the previous picture in the
 *  gallery"); the Galerija keeps it too, since it shows the books' portraits only */
export function replacedPortrait(soldier: Soldier): { file: string; large?: string; credit: string } | null {
  const ids = [soldier.soldier_id, ...(soldier.other_sources ?? []).map((o) => o.soldier_id)].filter(Boolean) as string[]
  if (!contributionsFor(soldier.soldier_id, ids.slice(1)).some((c) => c.photo)) return null
  const own = ids.map((id) => PORTRAITS[id]).find(Boolean)
  return own ? { file: own.f, large: own.v, credit: own.c } : null
}
