'use client'

import { useEffect } from 'react'
import dynamic from 'next/dynamic'

// The record dialog, with the books' descriptions, the portraits' index and the PDF viewer, is most of a page's
// script; the pages load it apart, once the browser is idle after the page has shown, or on the first click
const load = () => import('./SoldierModal')

const SoldierModal = dynamic(load, { ssr: false })
export default SoldierModal

export function usePreloadSoldierModal() {
  useEffect(() => {
    const idle = window.requestIdleCallback
    if (idle) {
      const id = idle(() => void load(), { timeout: 4000 })
      return () => window.cancelIdleCallback(id)
    }
    const id = window.setTimeout(() => void load(), 2000)
    return () => window.clearTimeout(id)
  }, [])
}
