'use client'

import { useEffect, useRef } from 'react'
import { useLang } from '@/app/i18n/LangContext'
import { RECORD_PARAM, recordPath } from './records'

/**
 * The browser's Back closes an open record, as it does on a phone everywhere else, instead of leaving the search.
 * Opening a record adds one step to the history, at the record's own address, however many records are then stepped
 * through in the dialog (the address follows them, so copying it gives the record's link), and closing it with the X or
 * Esc takes that step back off. The step under it is the page without the record, also when the page was opened at a
 * record's older address (/units/<unit>?borac=<id>).
 */
export function useBackClosesRecord(soldierId: string | undefined, close: () => void) {
  const lang = useLang()
  const closeRef = useRef(close)
  closeRef.current = close
  // Our step is on the history; Back has already taken it off
  const stepped = useRef(false)
  const wentBack = useRef(false)

  useEffect(() => {
    const onBack = () => {
      if (!stepped.current) return
      wentBack.current = true
      closeRef.current()
    }
    window.addEventListener('popstate', onBack)
    return () => window.removeEventListener('popstate', onBack)
  }, [])

  // Only on opening, stepping and closing, never when the page goes away with a record open: following a link out of
  // the record must not be undone
  useEffect(() => {
    if (soldierId && !stepped.current) {
      const under = new URL(window.location.href)
      under.searchParams.delete(RECORD_PARAM)
      window.history.replaceState(window.history.state, '', under)
      window.history.pushState(window.history.state, '', recordPath(soldierId, lang))
      stepped.current = true
    } else if (soldierId) {
      window.history.replaceState(window.history.state, '', recordPath(soldierId, lang))
    } else if (stepped.current) {
      stepped.current = false
      if (!wentBack.current) window.history.back()
      wentBack.current = false
    }
    // the language doesn't change while the page is open
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soldierId])
}
