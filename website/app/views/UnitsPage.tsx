import UnitsBrowser from '@/app/components/UnitsBrowser'
import { messagesFor } from '@/app/i18n'
import { pageMetadata } from '@/app/i18n/metadata'
import type { Lang } from '@/app/i18n/config'

export function unitsMetadata(lang: Lang) {
  const t = messagesFor(lang).unitsPage
  return pageMetadata(lang, '/jedinice', { title: t.title, description: t.description })
}

// The Jedinice page, /jedinice, in every language: every unit under the year it was formed, each card leading to the
// unit's own page. The home page no longer lists them; its "Jedinice" door leads here.
export default function UnitsPage({ lang }: { lang: Lang }) {
  return (
    <div className="container page-content">
      <h1 className="page-title">{messagesFor(lang).unitsPage.title}</h1>
      <UnitsBrowser />
    </div>
  )
}
