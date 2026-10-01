'use client'

import { useLayoutEffect, useRef, useState } from 'react'
import Link from 'next/link'
import type { Unit } from '@/app/data/units'
import { useLang, useLocalePath, useT } from '@/app/i18n/LangContext'
import { unitName } from '@/app/i18n/units'

// Soldiers of the 2. krajiška brigade walking away through snow: the figures sit on the right,
// the snow on the left stays nearly flat red, so the heading and the search field read cleanly.
// If that unit is missing, the band stays plain red.
const BAND_UNIT_ID = '2-krajiska-brigada'

export default function BandPhoto({ units }: { units: Unit[] }) {
  const t = useT()
  const lang = useLang()
  const to = useLocalePath()
  const ref = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)
  const unit = units.find((u) => u.id === BAND_UNIT_ID)

  // The photograph also runs under the site header, so the band reads as one picture
  useLayoutEffect(() => {
    const header = document.querySelector<HTMLElement>('header.masthead')
    const band = ref.current
    if (!header || !band) return
    const place = () => {
      band.style.top = `${-header.offsetHeight}px`
    }
    place()
    setReady(true)
    const observer = new ResizeObserver(place)
    observer.observe(header)
    return () => observer.disconnect()
  }, [unit])

  if (!unit) return null

  return (
    <>
      <div ref={ref} className="band-photo" data-ready={ready ? '' : undefined}>
        <img src={unit.image} alt="" />
      </div>
      <p className="band-credit">
        {t.home.bandCredit} <Link href={to(`/units/${unit.id}`)}>{unitName(unit, lang)}</Link>
      </p>
    </>
  )
}
