'use client'

import Link from 'next/link'
import type { ComponentProps } from 'react'
import { useLocalePath } from '@/app/i18n/LangContext'

export const HOME_RESET = 'knjiga:home-reset'

// A link to the home page (in the page's language) that also clears its search: on the home page itself
// the link goes nowhere, and Next keeps the typed search (see views/HomePage.tsx)
export default function HomeLink({ onClick, ...props }: Omit<ComponentProps<typeof Link>, 'href'>) {
  const to = useLocalePath()
  return (
    <Link
      {...props}
      href={to('/')}
      onClick={(e) => {
        onClick?.(e)
        window.dispatchEvent(new Event(HOME_RESET))
      }}
    />
  )
}
