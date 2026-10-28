'use client'

import { useEffect, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import type { ShownPortrait } from '@/app/data/portraits'
import { standInFor } from '@/app/lib/standIn'
import { vezSetOf } from '@/app/lib/relations'
import { frameFor, vezProps } from '@/app/lib/vez'
import railVez from '@/app/data/railVez.json'
import StandInPortrait from './StandInPortrait'
import PhotoLightbox from './PhotoLightbox'
import { useT } from '@/app/i18n/LangContext'

const RAIL_VEZ = railVez as Record<string, number>

// The soldier's portrait as a small 3:4 print: his or her photograph where we have one (it opens large over the
// page), otherwise an anonymous outline of a partisan in a cap. In the record (framed) the print wears the soldier's
// embroidered frame (lib/vez.ts), the one his face wears on the home page's margins.
export default function SoldierPortrait({ soldier, unitId, portrait, className, framed = false }: {
  soldier: Soldier
  unitId?: string
  portrait: ShownPortrait | null
  className: string
  framed?: boolean
}) {
  const [open, setOpen] = useState(false)
  const t = useT().record
  const id = soldier.soldier_id
  const name = `${soldier.last_name} ${soldier.first_name}`
  // A margin face's set is known at once; any other soldier's comes with his place files
  const [set, setSet] = useState<{ id: string; set: number | null } | null>(null)
  useEffect(() => {
    if (!framed || id in RAIL_VEZ) return
    let live = true
    vezSetOf(id).then((found) => { if (live) setSet({ id, set: found }) })
    return () => { live = false }
  }, [framed, id])
  const known = framed && (id in RAIL_VEZ ? { id, set: RAIL_VEZ[id] } : set?.id === id ? set : null)
  const frame = known ? vezProps(frameFor(known.set, name)) : null
  const look = frame ? `${className} vez` : className

  if (portrait) {
    // the opened photo outside the print: the print is its own layer (z-index), which would keep it under the
    // record's close button and its Prethodni / Sledeći bar
    return (
      <>
        <figure className={look} {...frame}>
          <button type="button" className="portrait-open" onClick={() => setOpen(true)} aria-label={t.openPhoto}>
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
    <figure className={`${look} is-standin`} title={t.photoUnknown} {...frame}>
      <StandInPortrait silhouette={standInFor(soldier, unitId)} />
    </figure>
  )
}
