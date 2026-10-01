'use client'

import { useEffect, useMemo, useState } from 'react'
import index from '@/app/data/portrait-index.json'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import type { Soldier } from '@/app/lib/types'
import { useT } from '@/app/i18n/LangContext'

// Wartime portraits drifting slowly up the empty margins beside the home page column, on screens wide enough to
// have margins (globals.css hides them below 84rem). The order changes every day. Pointing at a face or focusing
// it stops the drift, and a click opens the soldier's record.

const INDEX = index as Record<string, { f: string; y?: number }>

interface Face {
  id: string
  src: string
  focus: number
  soldier?: Soldier
}

// The same order all day, another tomorrow
function shuffled<T>(items: T[], seed: string): T[] {
  let h = 2166136261
  for (const c of seed) h = Math.imul(h ^ c.charCodeAt(0), 16777619)
  const out = [...items]
  for (let i = out.length - 1; i > 0; i--) {
    h = Math.imul(h ^ (h >>> 15), 2246822507) ^ Math.imul(h ^ (h >>> 13), 3266489909)
    const j = (h >>> 0) % (i + 1)
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

function RailFace({ face, onOpen }: { face: Face; onOpen: (soldier: Soldier) => void }) {
  const { soldier } = face
  const img = <img src={face.src} alt="" loading="lazy" style={{ objectPosition: `50% ${face.focus}%` }} />
  // Until the lists have loaded the name isn't known yet: the face shows, without a name or a link
  if (!soldier) return <span className="rail-face">{img}</span>
  return (
    <button type="button" className="rail-face" onClick={() => onOpen(soldier)}>
      {img}
      <span className="rail-name"><b>{soldier.last_name}</b> {soldier.first_name}</span>
    </button>
  )
}

interface PortraitRailsProps {
  soldiers: Soldier[]
  onOpen: (soldier: Soldier) => void
}

export default function PortraitRails({ soldiers, onOpen }: PortraitRailsProps) {
  const t = useT()
  const [day, setDay] = useState<string | null>(null)
  useEffect(() => setDay(new Date().toDateString()), [])

  // A portrait is filed under the soldier's own id, or under the id his entry had before it was merged
  const byId = useMemo(() => {
    const map = new Map<string, Soldier>()
    for (const s of soldiers) {
      map.set(s.soldier_id, s)
      for (const o of s.other_sources ?? []) if (o.soldier_id && !map.has(o.soldier_id)) map.set(o.soldier_id, s)
    }
    return map
  }, [soldiers])

  const faces = useMemo<Face[]>(
    () => (day ? shuffled(WARTIME_PORTRAITS.filter((id) => INDEX[id]), day) : []).map((id) => ({
      id, src: `/portreti/${INDEX[id].f}`, focus: INDEX[id].y ?? 30, soldier: byId.get(id),
    })),
    [day, byId],
  )
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
