import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import SiteShell from '../components/SiteShell'
import { siteMetadata } from '../i18n/metadata'
import { SerboCroatian } from '../i18n/LangContext'

// The site in Serbo-Croatian, at the plain addresses: /, /units/<id>, /izvori, /kartica.
// The other languages have their own root layout, (intl)/[lang]/layout.tsx.

export const metadata: Metadata = siteMetadata('sr')

export default function SerboCroatianLayout({ children }: { children: ReactNode }) {
  return <SiteShell lang="sr" Language={SerboCroatian}>{children}</SiteShell>
}
