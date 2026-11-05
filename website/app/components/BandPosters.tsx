'use client'

import { useEffect, useState } from 'react'
import s from './BandPosters.module.css'

// One poster on a wall: its index in `ids`, how far from the column, from the band's top, height, width, tilt in degrees
type Spot = [number, number, number, number, number, number]
type Wall = { v: number; left: Spot[]; right: Spot[] }
type Walls = { ids: string[]; walls: Wall[] }

const PERIOD_MS = 30_000 // how long a wall stays up
const FADE_MS = 3_000 // the walls' fade in BandPosters.module.css
const WIDE = '(min-width: 1400px)' // where the margins can hold a poster, as in the CSS: below that nothing loads
const printOf = (id: string) => `/plakati-band/${id}.webp`

function Margin({ side, spots, ids, leaving }: { side: 'left' | 'right'; spots: Spot[]; ids: string[]; leaving: boolean }) {
  const fromColumn = side === 'left' ? 'right' : 'left'
  return (
    <div className={`${s.margin} ${s[side]} ${leaving ? s.leaving : ''}`} aria-hidden="true">
      {spots.map(([poster, o, y, h, w, turn]) => (
        <img
          key={poster}
          className={s.poster}
          src={printOf(ids[poster])}
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

function shuffled(n: number) {
  const order = Array.from({ length: n }, (_, i) => i)
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[order[i], order[j]] = [order[j], order[i]]
  }
  return order
}

// Its next wall's prints, those the margins are wide enough to show, so that it fades in whole
function loadPrints(wall: Wall, ids: string[]) {
  const margin = document.querySelector<HTMLElement>(`.${s.margin}`)?.clientWidth ?? 0
  const decoding = [...wall.left, ...wall.right]
    .filter(([, o]) => o < margin)
    .map(([poster]) => {
      const img = new Image()
      img.src = printOf(ids[poster])
      return img.decode().catch(() => undefined)
    })
  const patience = new Promise((done) => setTimeout(done, 8_000))
  return Promise.race([Promise.all(decoding), patience])
}

// The Partisans' wartime posters, faint, pasted in the band's margins as on a wall. The wall changes slowly, in an order of
// its own on each visit (app/data/bandWalls.json, scripts/make_band_walls.py), and only while someone can see it. Nothing
// moves when it changes, it only fades, so a visitor who asks for less motion gets it too.
export default function BandPosters() {
  const [data, setData] = useState<Walls | null>(null)
  const [shown, setShown] = useState<{ current: number; leaving: number | null }>({ current: 0, leaving: null })

  useEffect(() => {
    const wide = window.matchMedia(WIDE)
    let cancelled = false
    let started = false
    let timer: ReturnType<typeof setTimeout> | undefined
    let fade: ReturnType<typeof setTimeout> | undefined

    const start = async () => {
      if (started || !wide.matches) return
      started = true
      const walls = (await import('@/app/data/bandWalls.json')).default as Walls
      if (cancelled) return
      const order = shuffled(walls.walls.length)
      let at = 0
      setData(walls)
      setShown({ current: order[0], leaving: null })

      const inView = () => {
        const band = document.querySelector('.band-photo')
        return !document.hidden && wide.matches && !!band && band.getBoundingClientRect().bottom > 0
      }
      const next = async () => {
        if (inView()) {
          const coming = order[(at + 1) % order.length]
          await loadPrints(walls.walls[coming], walls.ids)
          if (cancelled) return
          at += 1
          setShown((was) => ({ current: coming, leaving: was.current }))
          fade = setTimeout(() => setShown((was) => ({ ...was, leaving: null })), FADE_MS)
        }
        timer = setTimeout(next, PERIOD_MS)
      }
      timer = setTimeout(next, PERIOD_MS)
    }

    start()
    wide.addEventListener('change', start)
    return () => {
      cancelled = true
      wide.removeEventListener('change', start)
      clearTimeout(timer)
      clearTimeout(fade)
    }
  }, [])

  if (!data) return null
  const layers = shown.leaving === null ? [shown.current] : [shown.leaving, shown.current]
  return (
    <>
      {layers.map((i) => {
        const wall = data.walls[i]
        const leaving = i === shown.leaving
        return (
          <div key={wall.v} data-wall={wall.v}>
            <Margin side="left" spots={wall.left} ids={data.ids} leaving={leaving} />
            <Margin side="right" spots={wall.right} ids={data.ids} leaving={leaving} />
          </div>
        )
      })}
    </>
  )
}
