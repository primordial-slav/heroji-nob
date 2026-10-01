import SourcesPage, { sourcesMetadata } from '../../../views/SourcesPage'
import type { Lang } from '../../../i18n/config'

export async function generateMetadata({ params }: { params: Promise<{ lang: string }> }) {
  return sourcesMetadata((await params).lang as Lang)
}

export default async function Page({ params }: { params: Promise<{ lang: string }> }) {
  return <SourcesPage lang={(await params).lang as Lang} />
}
