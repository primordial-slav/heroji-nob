'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import ThemeToggle from './ThemeToggle'

export default function Navigation() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    return pathname === path ? 'nav-link active' : 'nav-link'
  }

  return (
    <nav className="navigation">
      <div className="container">
        <div className="nav-links">
          <Link href="/" className={isActive('/')}>
            Početna
          </Link>
          <Link href="/about" className={isActive('/about')}>
            O nama
          </Link>
          <Link href="/contact" className={isActive('/contact')}>
            Kontakt
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </nav>
  )
}
