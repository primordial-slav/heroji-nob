import HomePage from '../../views/HomePage'
import { homePictures } from '@/app/lib/homePictures'
import { pageMetadata } from '../../i18n/metadata'
import type { Lang } from '../../i18n/config'

export async function generateMetadata({ params }: { params: Promise<{ lang: string }> }) {
  return pageMetadata((await params).lang as Lang, '/')
}

export default function Page() {
  return <HomePage pictures={homePictures()} />
}
