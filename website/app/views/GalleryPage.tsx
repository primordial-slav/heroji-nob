import { units } from '@/app/data/units'
import index from '@/app/data/portrait-index.json'
import { RECORDS_PER_PART } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'
import { messagesFor } from '@/app/i18n'
import { pageMetadata } from '@/app/i18n/metadata'
import type { Lang } from '@/app/i18n/config'
import GalleryClient, { type GalleryItem } from './GalleryClient'

export function galleryMetadata(lang: Lang) {
  const t = messagesFor(lang).gallery
  return pageMetadata(lang, '/galerija', { title: t.title, description: t.description })
}

const PORTRAITS = index as Record<string, { f: string }>

// Built from the unit files (at build time, fresh on each request under next dev), so each portrait knows which
// slice of its unit's records (/records/<unit>/<part>) holds the soldier's full record
function galleryItems(): GalleryItem[] {
  const items: GalleryItem[] = []
  for (const unit of units) {
    readUnitFile(unit.dataFile).forEach((s, i) => {
      const portrait = PORTRAITS[s.soldier_id]
      if (portrait) {
        items.push({ id: s.soldier_id, name: s.full_name, unit: unit.id, part: Math.floor(i / RECORDS_PER_PART), file: portrait.f })
      }
    })
  }
  return items
}

// The Galerija page, /galerija, in every language
export default function GalleryPage({ lang }: { lang: Lang }) {
  const items = galleryItems()
  return (
    <div className="container page-content">
      <h1 className="page-title">{messagesFor(lang).gallery.title}</h1>
      <GalleryClient items={items} />
    </div>
  )
}
