'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import HomeLink from './HomeLink'

const LINKS = [
  { href: '/', label: 'Početna' },
  { href: '/izvori', label: 'Izvori' },
]

export default function Navigation() {
  const pathname = usePathname()

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' || pathname.startsWith('/units') : pathname === href

  return (
    <nav className="nav" aria-label="Glavna navigacija">
      {LINKS.map(({ href, label }) => {
        const props = {
          className: isActive(href) ? 'nav-link active' : 'nav-link',
          'aria-current': isActive(href) ? ('page' as const) : undefined,
          children: label,
        }
        return href === '/' ? <HomeLink key={href} {...props} /> : <Link key={href} href={href} {...props} />
      })}
    </nav>
  )
}
