'use client'

import type { MouseEvent, ReactNode } from 'react'
import type { Soldier } from '@/app/lib/types'
import { recordPath } from '@/app/lib/records'
import { useLang } from '@/app/i18n/LangContext'

/** A click that should open in place: not a middle click or one with a key held, which the browser takes to a new tab */
export function isPlainClick(e: MouseEvent): boolean {
  return e.button === 0 && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey
}

/**
 * A soldier in a list: a link to his record's own address, so it can be opened in a new tab or held on a phone, where
 * a plain click opens the dialog in place.
 */
export default function RecordLink({ soldier, onOpen, className, children }: {
  soldier: Soldier
  onOpen: (soldier: Soldier) => void
  className: string
  children: ReactNode
}) {
  const lang = useLang()
  return (
    <a
      href={recordPath(soldier.soldier_id, lang)}
      className={className}
      onClick={(e) => {
        if (!isPlainClick(e)) return
        e.preventDefault()
        onOpen(soldier)
      }}
    >
      {children}
    </a>
  )
}
