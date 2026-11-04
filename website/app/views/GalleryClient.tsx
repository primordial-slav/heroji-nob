'use client'

import { useEffect, useRef, useState } from 'react'
import { units } from '@/app/data/units'
import type { Soldier } from '@/app/lib/types'
import { recordsPath } from '@/app/lib/searchIndex'
import { recordPath } from '@/app/lib/records'
import { useBackClosesRecord } from '@/app/lib/useBackClosesRecord'
import { isPlainClick } from '@/app/components/RecordLink'
import SoldierModal, { usePreloadSoldierModal } from '@/app/components/LazySoldierModal'
import { useLang, useT } from '@/app/i18n/LangContext'

const UNIT_BY_ID = new Map(units.map((unit) => [unit.id, unit]))

export interface GalleryItem {
  id: string
  name: string
  unit: string     // the unit's id
  part: number     // the slice of the unit's records that holds him (recordsPath)
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
  usePreloadSoldierModal()
  const t = useT().gallery
  const lang = useLang()
  // shuffled in the browser only: the page is built once, and the server's order would show for a moment
  const [order, setOrder] = useState<GalleryItem[] | null>(null)
  const [selected, setSelected] = useState<Soldier | null>(null)
  const opening = useRef<string | null>(null)

  useEffect(() => setOrder(shuffled(items)), [items])

  const close = () => { opening.current = null; setSelected(null) }
  useBackClosesRecord(selected?.soldier_id, close)

  const open = async (item: GalleryItem) => {
    opening.current = item.id
    const unit = UNIT_BY_ID.get(item.unit)
    try {
      const response = await fetch(recordsPath(item.unit, item.part))
      const records: Soldier[] = response.ok ? await response.json() : []
      const record = records.find((r) => r.soldier_id === item.id)
      if (record && opening.current === item.id) setSelected({ ...record, unit: unit?.name })
    } catch {
      // the portrait stays; nothing opens
    }
  }

  return (
    <>
      <ul className="gallery-grid" aria-label={t.label(items.length)}>
        {(order ?? []).map((item) => {
          const unit = UNIT_BY_ID.get(item.unit)
          return (
            <li key={item.id}>
              <a
                href={recordPath(item.id, lang)}
                className="gallery-tile"
                title={item.name}
                onClick={(e) => {
                  if (!isPlainClick(e)) return
                  e.preventDefault()
                  open(item)
                }}
              >
                <img src={`/portreti/${item.file}`} alt={item.name} loading="lazy" />
                <span className="gallery-name">{item.name}</span>
              </a>
            </li>
          )
        })}
      </ul>

      {selected && (
        <SoldierModal
          key={selected.soldier_id}
          soldier={selected}
          onClose={close}
        />
      )}
    </>
  )
}
