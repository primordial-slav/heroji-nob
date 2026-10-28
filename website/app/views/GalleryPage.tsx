import { generatedPages } from '@/app/lib/generated'
import { messagesFor } from '@/app/i18n'
import { pageMetadata } from '@/app/i18n/metadata'
import type { Lang } from '@/app/i18n/config'
import GalleryClient from './GalleryClient'

export function galleryMetadata(lang: Lang) {
  const t = messagesFor(lang).gallery
  return pageMetadata(lang, '/galerija', { title: t.title, description: t.description })
}

// The Galerija page, /galerija, in every language. Its portraits, each knowing which slice of its unit's records holds
// the soldier's full record, are worked out from the unit files by scripts/prepare-data.ts (lib/generated.ts).
export default function GalleryPage({ lang }: { lang: Lang }) {
  const items = generatedPages()?.gallery ?? []
  return (
    <div className="container page-content">
      <h1 className="page-title">{messagesFor(lang).gallery.title}</h1>
      <GalleryClient items={items} />
    </div>
  )
}
