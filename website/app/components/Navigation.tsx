'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import HomeLink from './HomeLink'
import { splitPath } from '@/app/i18n/config'
import { useLocalePath, useT } from '@/app/i18n/LangContext'

export default function Navigation() {
  const t = useT()
  const to = useLocalePath()
  const { path } = splitPath(usePathname())
  const links = [
    { href: '/', label: t.nav.home },
    { href: '/jedinice', label: t.nav.units },
    { href: '/galerija', label: t.nav.gallery },
    { href: '/izvori', label: t.nav.sources },
  ]

  // a unit's own page belongs to Jedinice
  const isActive = (href: string) =>
    href === '/jedinice' ? path === href || path.startsWith('/units') : path === href

  return (
    <nav className="nav" aria-label={t.nav.label}>
      {links.map(({ href, label }) => {
        const props = {
          className: `nav-link${href === '/' ? ' nav-link-home' : ''}${isActive(href) ? ' active' : ''}`,
          'aria-current': isActive(href) ? ('page' as const) : undefined,
          children: label,
        }
        return href === '/' ? <HomeLink key={href} {...props} /> : <Link key={href} href={to(href)} {...props} />
      })}
    </nav>
  )
}
