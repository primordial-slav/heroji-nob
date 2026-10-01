import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import SiteShell from '../../components/SiteShell'
import { messagesFor } from '../../i18n'
import { PREFIXED_LANGS, type Lang } from '../../i18n/config'
import { missingUnitTexts } from '../../i18n/units'
import { missingSourceTexts } from '../../i18n/sources'
import { units } from '../../data/units'
import { sources } from '../../data/sources'

// The site in Slovene, Macedonian and English: /sl, /mk/units/<id>, /en/izvori. Only these three exist;
// any other first segment is not a language (static routes such as /izvori come first anyway).
export const dynamicParams = false

export function generateStaticParams() {
  // A unit or book added without its text in these languages shows its Serbo-Croatian text there: say so at build
  const missing = [...missingUnitTexts(units.map((u) => u.id)), ...missingSourceTexts(sources.map((s) => s.id))]
  if (missing.length) {
    console.warn(`Not yet written in every language (i18n/units.ts, i18n/sources.ts): ${missing.join(', ')}`)
  }
  return PREFIXED_LANGS.map((lang) => ({ lang }))
}

export async function generateMetadata({ params }: { params: Promise<{ lang: string }> }): Promise<Metadata> {
  const t = messagesFor((await params).lang as Lang)
  return { title: t.site.name, description: t.site.description }
}

export default async function LanguageLayout({ children, params }: { children: ReactNode; params: Promise<{ lang: string }> }) {
  const { lang } = await params
  return <SiteShell lang={lang as Lang}>{children}</SiteShell>
}
