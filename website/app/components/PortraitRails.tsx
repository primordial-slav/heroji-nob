'use client'

import { useEffect, useMemo, useState } from 'react'
import index from '@/app/data/portrait-index.json'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import { familyContributions } from '@/app/data/family'
import type { Soldier } from '@/app/lib/types'
import { useT } from '@/app/i18n/LangContext'

// Wartime portraits drifting slowly up the empty margins beside the home page column, on screens wide enough to
// have margins (globals.css hides them below 84rem), in a new order on every visit. Pointing at a face or focusing
// it stops the drift, and a click opens the soldier's record.

// `same`: the id of the record whose portrait this one repeats (one person in several units' books)
const INDEX = index as Record<string, { f: string; y?: number; h?: string; same?: string }>

// A soldier's photo as his record shows it: a family's first (public/porodica/), else a book's (public/portreti/)
export function photoOf(id: string): { src: string; focus: number } | null {
  const family = familyContributions.find((c) => c.soldierId === id && c.photo)
  if (family) return { src: `/porodica/${family.photo}`, focus: 30 }
  return INDEX[id] ? { src: `/portreti/${INDEX[id].f}`, focus: INDEX[id].y ?? 30 } : null
}

// Which picture an id shows, so one picture filed under two ids (a man in two units' lists, each record with
// its copy) shows once: a Commons file or a znaci gallery photo is one picture; a book page prints several
// people's photos, so there the file decides
const ONE_PICTURE = /commons\.wikimedia\.org\/wiki\/File:|znaci\.org\/fotografija\.php\?br=/
function pictureOf(id: string): string {
  const family = familyContributions.find((c) => c.soldierId === id && c.photo)
  if (family) return `porodica/${family.photo}`
  const entry = INDEX[id]
  return entry?.h && ONE_PICTURE.test(entry.h) ? entry.h : `portreti/${entry?.f}`
}

interface Face {
  id: string
  src: string
  focus: number
  soldier?: Soldier
}

// A new order on every visit
function shuffled<T>(items: T[]): T[] {
  const out = [...items]
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

// Each print wears one of six thin embroidered frames (public/vez/, scripts/make_vez_frames.py), in turn down a
// column, so no two neighbours match
const FRAMES = 6

function RailFace({ face, frame, onOpen }: { face: Face; frame: number; onOpen: (soldier: Soldier) => void }) {
  const { soldier } = face
  const img = (
    <span className="rail-print" data-okvir={frame}>
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
  soldiers: Soldier[]
  onOpen: (soldier: Soldier) => void
}

export default function PortraitRails({ soldiers, onOpen }: PortraitRailsProps) {
  const t = useT()
  // Shuffled in the browser once the page is there, so the server's HTML and the first render agree; the
  // order then stays put while the lists load
  const [order, setOrder] = useState<string[] | null>(null)
  useEffect(() => setOrder(shuffled(WARTIME_PORTRAITS.filter((id) => photoOf(id)))), [])

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
  // last rule holds from the start and each comes with its name.
  const faces = useMemo<Face[]>(() => {
    if (!order || soldiers.length === 0) return []
    const seen = new Set<string>()
    const people = new Set<Soldier>()
    const out: Face[] = []
    for (const id of order) {
      const keys = [pictureOf(id), `person/${INDEX[id]?.same ?? id}`]
      const soldier = byId.get(id)
      if (keys.some((k) => seen.has(k)) || (soldier && people.has(soldier))) continue
      keys.forEach((k) => seen.add(k))
      if (soldier) people.add(soldier)
      out.push({ id, ...photoOf(id)!, soldier })
    }
    return out
  }, [order, byId, soldiers.length])
  if (!faces.length) return null

  const sides = [faces.filter((_, i) => i % 2 === 0), faces.filter((_, i) => i % 2 === 1)]
  return (
    <aside className="rails" aria-label={t.home.rails}>
      {sides.map((side, i) => (
        <div key={i} className="rail-col">
          <div className="rail-window">
            <div className="rail-track">
              <div className="rail-set">
                {side.map((f, j) => <RailFace key={f.id} face={f} frame={((j + i * 3) % FRAMES) + 1} onOpen={onOpen} />)}
              </div>
              {/* The same faces again, so the drift loops without a seam: out of reach of the keyboard and
                  screen readers, which have the first set */}
              <div className="rail-set" inert>
                {side.map((f, j) => <RailFace key={f.id} face={f} frame={((j + i * 3) % FRAMES) + 1} onOpen={onOpen} />)}
              </div>
            </div>
          </div>
        </div>
      ))}
    </aside>
  )
}
