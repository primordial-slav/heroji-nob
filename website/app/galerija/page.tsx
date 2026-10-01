import { units } from '@/app/data/units'
import index from '@/app/data/portrait-index.json'
import { RECORDS_PER_PART } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'
import GalleryClient, { type GalleryItem } from './GalleryClient'

export const metadata = {
  title: 'Galerija — Knjiga boraca',
  description: 'Fotografije boraca: lica iz knjiga jedinica i iz fotogalerije znaci.org.',
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

export default function GalerijaPage() {
  const items = galleryItems()
  return (
    <div className="container page-content">
      <h1 className="page-title">Galerija</h1>
      <GalleryClient items={items} />
    </div>
  )
}
