import MemorialCard from '../../../views/MemorialCard'
import { cardMetadata } from '../../../i18n/metadata'
import type { Lang } from '../../../i18n/config'

export async function generateMetadata({ params }: { params: Promise<{ lang: string }> }) {
  return cardMetadata((await params).lang as Lang)
}

export default function KarticaPage() {
  return <MemorialCard />
}
