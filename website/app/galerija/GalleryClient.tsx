'use client'

import { useEffect, useRef, useState } from 'react'
import { units } from '@/app/data/units'
import type { Soldier } from '@/app/lib/types'
import SoldierModal from '@/app/components/SoldierModal'

export interface GalleryItem {
  id: string
  name: string
  unit: string     // the unit's id
  part: number     // the slice of the unit's records that holds him (/records/<unit>/<part>)
  file: string     // in /portreti/
}

// A new order on every visit, so no face is always first
function shuffled<T>(items: T[]): T[] {
  const out = [...items]
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

export default function GalleryClient({ items }: { items: GalleryItem[] }) {
  // shuffled in the browser only: the page is built once, and the server's order would show for a moment
  const [order, setOrder] = useState<GalleryItem[] | null>(null)
  const [selected, setSelected] = useState<Soldier | null>(null)
  const opening = useRef<string | null>(null)

  useEffect(() => setOrder(shuffled(items)), [items])

  const open = async (item: GalleryItem) => {
    opening.current = item.id
    const unit = units.find((u) => u.id === item.unit)
    try {
      const response = await fetch(`/records/${item.unit}/${item.part}`)
      const records: Soldier[] = response.ok ? await response.json() : []
      const record = records.find((r) => r.soldier_id === item.id)
      if (record && opening.current === item.id) setSelected({ ...record, unit: unit?.name })
    } catch {
      // the portrait stays; nothing opens
    }
  }

  return (
    <>
      <ul className="gallery-grid" aria-label={`Fotografije boraca (${items.length})`}>
        {(order ?? []).map((item) => (
          <li key={item.id}>
            <button type="button" className="gallery-tile" onClick={() => open(item)} title={item.name}>
              <img src={`/portreti/${item.file}`} alt={item.name} loading="lazy" />
              <span className="gallery-name">{item.name}</span>
            </button>
          </li>
        ))}
      </ul>

      {selected && (
        <SoldierModal
          key={selected.soldier_id}
          soldier={selected}
          onClose={() => { opening.current = null; setSelected(null) }}
        />
      )}
    </>
  )
}
