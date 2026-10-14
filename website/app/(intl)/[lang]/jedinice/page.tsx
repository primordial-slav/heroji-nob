import UnitsPage, { unitsMetadata } from '../../../views/UnitsPage'
import type { Lang } from '../../../i18n/config'

export async function generateMetadata({ params }: { params: Promise<{ lang: string }> }) {
  return unitsMetadata((await params).lang as Lang)
}

export default async function Page({ params }: { params: Promise<{ lang: string }> }) {
  return <UnitsPage lang={(await params).lang as Lang} />
}
