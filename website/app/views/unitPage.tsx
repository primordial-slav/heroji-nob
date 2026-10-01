import type { Metadata } from 'next'
import Link from 'next/link'
import { units } from '@/app/data/units'
import UnitPageClient from './UnitPageClient'
import { ArrowLeftIcon } from '@/app/components/Icons'
import { messagesFor } from '@/app/i18n'
import { pageMetadata } from '@/app/i18n/metadata'
import { unitDescription, unitName } from '@/app/i18n/units'
import { localePath, type Lang } from '@/app/i18n/config'
import { FIRST_PAGE } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'

// A unit's page, /units/<id>, in every language. Only the units below exist: any other id is a 404
// (each route sets dynamicParams = false), not a page rendered (and stored) on request.

export function unitParams() {
  return units.map((unit) => ({ id: unit.id }))
}

// The unit's name and description become the tab title and the text of a shared link
export function unitMetadata(lang: Lang, id: string): Metadata {
  const unit = units.find((u) => u.id === id)
  if (!unit) return { title: messagesFor(lang).site.name }
  return pageMetadata(lang, `/units/${unit.id}`, { title: unitName(unit, lang), description: unitDescription(unit, lang) })
}

export default function UnitPage({ lang, id }: { lang: Lang; id: string }) {
  const unit = units.find((u) => u.id === id)

  if (!unit) {
    const t = messagesFor(lang).unit
    return (
      <div className="container page-content">
        <h1 className="page-title">{t.notFound}</h1>
        <Link href={localePath(lang, '/')} className="back-link"><ArrowLeftIcon size={16} /> {t.backHome}</Link>
      </div>
    )
  }

  // The first page of the list is in the page itself, so it shows before the list has loaded
  const soldiers = readUnitFile(unit.dataFile)
  return <UnitPageClient unit={unit} firstPage={soldiers.slice(0, FIRST_PAGE)} total={soldiers.length} />
}
