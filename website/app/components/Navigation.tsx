'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

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
            Home
          </Link>
          <Link href="/about" className={isActive('/about')}>
            About
          </Link>
          <Link href="/contact" className={isActive('/contact')}>
            Contact
          </Link>
        </div>
      </div>
    </nav>
  )
}
