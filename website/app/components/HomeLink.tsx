'use client'

import Link from 'next/link'
import type { ComponentProps } from 'react'

export const HOME_RESET = 'knjiga:home-reset'

// A link to the home page that also clears its search: on the home page itself
// the link goes nowhere, and Next keeps the typed search (see page.tsx)
export default function HomeLink({ onClick, ...props }: Omit<ComponentProps<typeof Link>, 'href'>) {
  return (
    <Link
      {...props}
      href="/"
      onClick={(e) => {
        onClick?.(e)
        window.dispatchEvent(new Event(HOME_RESET))
      }}
    />
  )
}
