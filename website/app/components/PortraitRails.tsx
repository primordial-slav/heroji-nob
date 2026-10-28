'use client'

import { useEffect, useMemo, useState } from 'react'
import railVez from '@/app/data/railVez.json'
import type { Soldier } from '@/app/lib/types'
import { CAPPED_SETS, frameFor, vezProps } from '@/app/lib/vez'
import { useT } from '@/app/i18n/LangContext'
import { photoOf, pictureOf } from '@/app/lib/railPhotos'
import type { HomePictures } from '@/app/lib/homePictures'

// Wartime portraits drifting slowly up the empty margins beside the home page column, on screens wide enough to
// have margins (globals.css hides them below 84rem), in a new order on every visit. Pointing at a face or focusing
// it stops the drift, and a click opens the soldier's record.

interface Face {
  id: string
  src: string
  focus: number
  soldier?: Soldier
  /** His embroidered frame (lib/vez.ts), the one his record shows */
  frame: number
}

// Each face's set of frames, where it has one (scripts/build_vez.py)
const RAIL_VEZ = railVez as Record<string, number>

// A new order on every visit
function shuffled<T>(items: T[]): T[] {
  const out = [...items]
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

function RailFace({ face, onOpen }: { face: Face; onOpen: (soldier: Soldier) => void }) {
  const { soldier } = face
  const img = (
    <span className="rail-print vez" {...vezProps(face.frame)}>
      <img src={face.src} alt="" loading="lazy" style={{ objectPosition: `50% ${face.focus}%` }} />
    </span>
  )
  // A face whose record the lists don't have shows without a name or a link
  if (!soldier) return <span className="rail-face">{img}</span>
  return (
    <button type="button" className="rail-face" onClick={() => onOpen(soldier)}>
      {img}
      <span className="rail-name"><b>{soldier.last_name}</b> {soldier.first_name}</span>
    </button>
  )
}

interface PortraitRailsProps {
  pictures: HomePictures
  soldiers: Soldier[]
  onOpen: (soldier: Soldier) => void
}

export default function PortraitRails({ pictures, soldiers, onOpen }: PortraitRailsProps) {
  const { faces: ids, portraits } = pictures
  const t = useT()
  // Shuffled in the browser once the page is there, so the server's HTML and the first render agree; the
  // order then stays put while the lists load
  const [order, setOrder] = useState<string[] | null>(null)
  useEffect(() => setOrder(shuffled(ids)), [ids])

  // A portrait is filed under the soldier's own id, or under the id his entry had before it was merged
  const byId = useMemo(() => {
    const map = new Map<string, Soldier>()
    for (const s of soldiers) {
      map.set(s.soldier_id, s)
      for (const o of s.other_sources ?? []) if (o.soldier_id && !map.has(o.soldier_id)) map.set(o.soldier_id, s)
    }
    return map
  }, [soldiers])

  // Every face once: one picture once, and one person once, whether the index says so (`same`) or the lists do
  // (two ids of a soldier linked across units lead to the same record). The faces wait for the lists, so the
  // last rule holds from the start and each comes with its name. Of the Italians, Germans and Hungarians, one face
  // at most.
  const faces = useMemo<Face[]>(() => {
    if (!order || soldiers.length === 0) return []
    const seen = new Set<string>()
    const people = new Set<Soldier>()
    const out: Face[] = []
    let capped = 0
    for (const id of order) {
      const keys = [pictureOf(id, portraits), `person/${portraits[id]?.same ?? id}`]
      const soldier = byId.get(id)
      if (keys.some((k) => seen.has(k)) || (soldier && people.has(soldier))) continue
      const set = RAIL_VEZ[id] ?? null
      if (set !== null && CAPPED_SETS.has(set) && capped++ > 0) continue
      keys.forEach((k) => seen.add(k))
      if (soldier) people.add(soldier)
      const frame = frameFor(set, soldier ? `${soldier.last_name} ${soldier.first_name}` : id)
      out.push({ id, ...photoOf(id, portraits)!, soldier, frame })
    }
    return out
  }, [order, byId, soldiers.length, portraits])
  if (!faces.length) return null

  const sides = [faces.filter((_, i) => i % 2 === 0), faces.filter((_, i) => i % 2 === 1)]
  return (
    <aside className="rails" aria-label={t.home.rails}>
      {sides.map((side, i) => (
        <div key={i} className="rail-col">
          <div className="rail-window">
            <div className="rail-track">
              <div className="rail-set">
                {side.map((f) => <RailFace key={f.id} face={f} onOpen={onOpen} />)}
              </div>
              {/* The same faces again, so the drift loops without a seam: out of reach of the keyboard and
                  screen readers, which have the first set */}
              <div className="rail-set" inert>
                {side.map((f) => <RailFace key={f.id} face={f} onOpen={onOpen} />)}
              </div>
            </div>
          </div>
        </div>
      ))}
    </aside>
  )
}
