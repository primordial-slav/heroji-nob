import { familyContributions } from '@/app/data/family'

// The home page's wartime portraits (the margins, PortraitRails, and the Galerija door, HomeDoors). The page is
// given only these portraits' index entries (lib/homePictures.ts), not the whole data/portrait-index.json.

// `same`: the id of the record whose portrait this one repeats (one person in several units' books)
export type PortraitEntry = { f: string; y?: number; h?: string; same?: string }
export type Portraits = Record<string, PortraitEntry>

// A soldier's photo as his record shows it: a family's first (public/porodica/), else a book's (public/portreti/)
export function photoOf(id: string, index: Portraits): { src: string; focus: number } | null {
  const family = familyContributions.find((c) => c.soldierId === id && c.photo)
  if (family) return { src: `/porodica/${family.photo}`, focus: 30 }
  return index[id] ? { src: `/portreti/${index[id].f}`, focus: index[id].y ?? 30 } : null
}

// Which picture an id shows, so one picture filed under two ids (a man in two units' lists, each record with
// its copy) shows once: a Commons file or a znaci gallery photo is one picture; a book page prints several
// people's photos, so there the file decides
export const ONE_PICTURE = /commons\.wikimedia\.org\/wiki\/File:|znaci\.org\/fotografija\.php\?br=/
export function pictureOf(id: string, index: Portraits): string {
  const family = familyContributions.find((c) => c.soldierId === id && c.photo)
  if (family) return `porodica/${family.photo}`
  const entry = index[id]
  return entry?.h && ONE_PICTURE.test(entry.h) ? entry.h : `portreti/${entry?.f}`
}
