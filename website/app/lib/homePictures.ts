import index from '@/app/data/portrait-index.json'
import { sources } from '@/app/data/sources'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import { ONE_PICTURE, photoOf, type PortraitEntry, type Portraits } from './railPhotos'

// Server only: what the home page shows of the portraits and books, worked out when the page is built, so that its
// script doesn't carry the portraits' index and the list of books

export interface HomePictures {
  /** The wartime portraits that have a photo, in data/wartimePortraits.ts's order */
  faces: string[]
  /** Their index entries */
  portraits: Portraits
  /** How many portraits the Galerija shows (one per person) */
  photoCount: number
  /** The books with a picture of their cover, for the Izvori door */
  books: { id: string; thumbnail: string }[]
  bookCount: number
}

export function homePictures(): HomePictures {
  const all = index as Portraits
  const portraits: Portraits = {}
  for (const id of WARTIME_PORTRAITS) {
    if (!all[id]) continue
    const { f, y, h, same }: PortraitEntry = all[id]
    // the source's address only where it tells one picture (pictureOf)
    portraits[id] = { f, ...(y != null && { y }), ...(h && ONE_PICTURE.test(h) && { h }), ...(same && { same }) }
  }
  return {
    faces: WARTIME_PORTRAITS.filter((id) => photoOf(id, portraits)),
    portraits,
    photoCount: Object.values(all).filter((p) => !p.same).length,
    books: sources.filter((s) => s.thumbnail).map(({ id, thumbnail }) => ({ id, thumbnail })),
    bookCount: sources.length,
  }
}
