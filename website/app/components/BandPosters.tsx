'use client'

import { useEffect, useState } from 'react'
import s from './BandPosters.module.css'

// One poster on a wall: its index in `ids`, how far from the column, from the band's top, height, width, tilt in degrees
type Spot = [number, number, number, number, number, number]
type Wall = { v: number; left: Spot[]; right: Spot[] }
type Walls = { ids: string[]; walls: Wall[] }
type Chosen = { ids: string[]; wall: Wall }

const WIDE = '(min-width: 1400px)' // where the margins can hold a poster, as in the CSS: below that nothing loads
const LAST_WALL = 'bandWall'

// This page load's wall: moving between the site's pages keeps it, only a reload chooses again
let chosen: Chosen | null = null

// Any wall but the one the last load showed, so that a reload always changes it
function chooseWall(walls: Wall[]) {
  let last: string | null = null
  try {
    last = localStorage.getItem(LAST_WALL)
  } catch {}
  const others = walls.filter((wall) => String(wall.v) !== last)
  const wall = others[Math.floor(Math.random() * others.length)]
  try {
    localStorage.setItem(LAST_WALL, String(wall.v))
  } catch {}
  return wall
}

function Margin({ side, spots, ids }: { side: 'left' | 'right'; spots: Spot[]; ids: string[] }) {
  const fromColumn = side === 'left' ? 'right' : 'left'
  return (
    <div className={`${s.margin} ${s[side]}`} aria-hidden="true">
      {spots.map(([poster, o, y, h, w, turn]) => (
        <img
          key={poster}
          className={s.poster}
          src={`/plakati-band/${ids[poster]}.webp`}
          alt=""
          width={w}
          height={h}
          loading="lazy"
          decoding="async"
          style={{ [fromColumn]: o, top: y, width: w, height: h, rotate: `${turn}deg` }}
        />
      ))}
    </div>
  )
}

// The Partisans' wartime posters, faint, pasted in the band's margins as on a wall. A wall of its own for each page load
// (app/data/bandWalls.json, scripts/make_band_walls.py), chosen in the browser, since the page itself is prerendered.
export default function BandPosters() {
  const [shown, setShown] = useState<Chosen | null>(chosen)

  useEffect(() => {
    if (chosen) return
    const wide = window.matchMedia(WIDE)
    let cancelled = false
    const start = async () => {
      if (!wide.matches) return
      wide.removeEventListener('change', start)
      const { ids, walls } = (await import('@/app/data/bandWalls.json')).default as Walls
      if (cancelled) return
      chosen ??= { ids, wall: chooseWall(walls) }
      setShown(chosen)
    }
    start()
    wide.addEventListener('change', start)
    return () => {
      cancelled = true
      wide.removeEventListener('change', start)
    }
  }, [])

  if (!shown) return null
  return (
    <div data-wall={shown.wall.v}>
      <Margin side="left" spots={shown.wall.left} ids={shown.ids} />
      <Margin side="right" spots={shown.wall.right} ids={shown.ids} />
    </div>
  )
}
