import GalleryPage, { galleryMetadata } from '../../../views/GalleryPage'
import type { Lang } from '../../../i18n/config'

export async function generateMetadata({ params }: { params: Promise<{ lang: string }> }) {
  return galleryMetadata((await params).lang as Lang)
}

export default async function Page({ params }: { params: Promise<{ lang: string }> }) {
  return <GalleryPage lang={(await params).lang as Lang} />
}
