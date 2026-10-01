'use client'

import { useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import type { ShownPortrait } from '@/app/data/portraits'
import { standInFor } from '@/app/lib/standIn'
import StandInPortrait from './StandInPortrait'
import PhotoLightbox from './PhotoLightbox'

// The soldier's portrait as a small 3:4 print: his or her photograph where we have one (it opens large over the
// page), otherwise an anonymous outline of a partisan in a cap
export default function SoldierPortrait({ soldier, unitId, portrait, className }: {
  soldier: Soldier
  unitId?: string
  portrait: ShownPortrait | null
  className: string
}) {
  const [open, setOpen] = useState(false)
  if (portrait) {
    // the opened photo outside the print: the print is its own layer (z-index), which would keep it under the
    // record's close button and its Prethodni / Sledeći bar
    return (
      <>
        <figure className={className}>
          <button type="button" className="portrait-open" onClick={() => setOpen(true)} aria-label="Otvori fotografiju">
            <img src={portrait.src} alt="" style={{ objectPosition: `50% ${portrait.focus}%` }} />
          </button>
        </figure>
        {open && (
          <PhotoLightbox src={portrait.large ?? portrait.src} name={soldier.full_name} credit={portrait.credit}
            href={portrait.href} onClose={() => setOpen(false)} />
        )}
      </>
    )
  }
  return (
    <figure className={`${className} is-standin`} title="Fotografija ovog borca nije poznata">
      <StandInPortrait silhouette={standInFor(soldier, unitId)} />
    </figure>
  )
}
