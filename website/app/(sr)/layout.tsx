import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import SiteShell from '../components/SiteShell'
import { messagesFor } from '../i18n'

// The site in Serbo-Croatian, at the plain addresses: /, /units/<id>, /izvori, /kartica.
// The other languages have their own root layout, (intl)/[lang]/layout.tsx.

const t = messagesFor('sr')

export const metadata: Metadata = { title: t.site.name, description: t.site.description }

export default function SerboCroatianLayout({ children }: { children: ReactNode }) {
  return <SiteShell lang="sr">{children}</SiteShell>
}
