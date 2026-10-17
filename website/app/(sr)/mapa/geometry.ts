// Shared by the map's state, sheet and controls: dates on the war's month axis, the route as a smooth line, its
// arrowheads, numbered events kept apart, and the frame that fits an area onto the sheet

import { SHEET } from './map1941'

export type Pt = { x: number; y: number }
// move: on a leg away from the fighting (to rest, by train), drawn thin and without arrows
export type Sample = Pt & { t: number; move?: boolean }

// ---------- dates ----------

export const MONTH_NAMES = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']
export const MONTHS_IN = ['januaru', 'februaru', 'martu', 'aprilu', 'maju', 'junu', 'julu', 'avgustu', 'septembru', 'oktobru', 'novembru', 'decembru']
// December 1941, when the first brigade was formed, to May 1945: one axis for every unit, each using its own stretch
export const MONTHS = Array.from({ length: 42 }, (_, i) => `${1941 + Math.floor((11 + i) / 12)}-${String(((11 + i) % 12) + 1).padStart(2, '0')}`)
export const monthName = (ym: string) => `${MONTH_NAMES[Number(ym.slice(5)) - 1]} ${ym.slice(0, 4)}.`

export const day = (iso: string) => Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, iso.length > 7 ? +iso.slice(8, 10) : 15) / 864e5
export const monthEnd = (ym: string) => Date.UTC(+ym.slice(0, 4), +ym.slice(5, 7), 0) / 864e5
export const monthStart = (ym: string) => Date.UTC(+ym.slice(0, 4), +ym.slice(5, 7) - 1, 1) / 864e5
// a day's place among MONTHS (December 1941 is 0)
export const monthIndex = (t: number) => {
  const d = new Date(t * 864e5)
  return (d.getUTCFullYear() - 1941) * 12 + d.getUTCMonth() - 11
}
// how strongly something drawn `age` months ago still shows on the timeline: the month itself whole, the one before
// at a little over half, then fading fast (a third, a fifth, a ninth) to a trace that is never quite gone
export const fade = (age: number) => (age <= 0 ? 1 : Math.max(0.06, 0.55 * Math.exp(-(age - 1) / 1.9)))

export const YEARS = ['1941–42', '1943', '1944', '1945'] as const
export type Year = (typeof YEARS)[number]
// a line for each year, told apart by pattern as on a one-colour plate
export const DASH: Record<Year, string | undefined> = { '1941–42': undefined, '1943': '9 5', '1944': '13 4 2.5 4', '1945': '0.1 5' }
export const yearOf = (t: number): Year => {
  const y = new Date(t * 864e5).getUTCFullYear()
  return y <= 1942 ? '1941–42' : (String(y) as Year)
}

// ---------- the route's line ----------

// Centripetal Catmull-Rom: a smooth line through every waypoint that doesn't loop where they crowd
function curvePoint(p0: Pt, p1: Pt, p2: Pt, p3: Pt, u: number): Pt {
  const gap = (a: Pt, b: Pt) => Math.max(1e-3, Math.sqrt(Math.hypot(b.x - a.x, b.y - a.y)))
  const t0 = 0, t1 = t0 + gap(p0, p1), t2 = t1 + gap(p1, p2), t3 = t2 + gap(p2, p3)
  const t = t1 + (t2 - t1) * u
  const mix = (a: Pt, b: Pt, ta: number, tb: number): Pt => {
    const f = (t - ta) / (tb - ta)
    return { x: a.x + (b.x - a.x) * f, y: a.y + (b.y - a.y) * f }
  }
  const a1 = mix(p0, p1, t0, t1), a2 = mix(p1, p2, t1, t2), a3 = mix(p2, p3, t2, t3)
  return mix(mix(a1, a2, t0, t2), mix(a2, a3, t1, t3), t1, t2)
}

export function sampleRoute(route: { x: number; y: number; date: string; kind?: string }[]): Sample[] {
  const pts = route.map(w => ({ x: w.x, y: w.y, t: day(w.date) }))
  const out: Sample[] = []
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]
    const steps = Math.max(1, Math.ceil(Math.hypot(p2.x - p1.x, p2.y - p1.y) / 2))
    const move = route[i + 1].kind === 'transfer'
    for (let k = 0; k < steps; k++) {
      const u = k / steps
      out.push({ ...curvePoint(p0, p1, p2, p3, u), t: p1.t + (p2.t - p1.t) * u, ...(move && { move }) })
    }
  }
  out.push(pts[pts.length - 1])
  return out
}

/** A line cut where it changes from marching to moving away from the fighting, each piece sharing its first point
 * with the piece before so the line stays whole */
export function splitMoves<T extends Sample>(samples: T[]): { move: boolean; pts: T[] }[] {
  const runs: { move: boolean; pts: T[] }[] = []
  for (const s of samples) {
    const move = !!s.move, run = runs[runs.length - 1]
    if (run && run.move === move) run.pts.push(s)
    else runs.push({ move, pts: run ? [run.pts[run.pts.length - 1], s] : [s] })
  }
  return runs
}

export const pathOf = (pts: Pt[]) => pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join('')

// arrowheads along a line, every `every` units, pointing the way it runs
export function arrowsOf(pts: Pt[], every = 62, first = 34) {
  const out: { x: number; y: number; a: number }[] = []
  let next = first, run = 0
  for (let i = 1; i < pts.length; i++) {
    run += Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y)
    if (run >= next && i + 1 < pts.length) {
      const a = pts[Math.max(0, i - 2)], b = pts[Math.min(pts.length - 1, i + 2)]
      out.push({ x: pts[i].x, y: pts[i].y, a: (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI })
      next += every
    }
  }
  return out
}

// The numbered events, pushed apart where they crowd, each with a hair line back to its place when it had to move
export function placeNumbers(points: Pt[], r = 7): Pt[] {
  const pos = points.map(p => ({ ...p }))
  for (let it = 0; it < 60; it++) {
    let moved = false
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        const dx = pos[j].x - pos[i].x, dy = pos[j].y - pos[i].y
        const d = Math.hypot(dx, dy) || 0.01
        if (d < 2 * r + 1.5) {
          const push = (2 * r + 1.5 - d) / 2
          pos[i].x -= (dx / d) * push; pos[i].y -= (dy / d) * push
          pos[j].x += (dx / d) * push; pos[j].y += (dy / d) * push
          moved = true
        }
      }
    }
    if (!moved) break
  }
  return pos
}

// ---------- the frame ----------

// What the sheet shows: the point at its middle and how much it is enlarged. At z = 1 the whole country fills it
export type View = { cx: number; cy: number; z: number }
export const WHOLE: View = { cx: SHEET.width / 2, cy: SHEET.height / 2, z: 1 }
export const MAX_ZOOM = 3.2

// room kept clear at the sheet's edges, for the title block (top right) and the frame
const PAD = { left: 60, right: 60, top: 96, bottom: 56 }

// The view that fits a box of the map onto the sheet, never past the country's own frame
export function fit(box: [number, number, number, number], minSpan = 230): View {
  const { width: W, height: H } = SHEET
  let [x0, y0, x1, y1] = box
  const span = Math.max(x1 - x0, (y1 - y0) * (W / H))
  if (span < minSpan) {
    const grow = (minSpan - span) / 2
    x0 -= grow; x1 += grow
    y0 -= grow * (H / W); y1 += grow * (H / W)
  }
  const z = Math.max(1, Math.min(MAX_ZOOM, (W - PAD.left - PAD.right) / (x1 - x0), (H - PAD.top - PAD.bottom) / (y1 - y0)))
  // the box's middle goes to the middle of the free area, not of the sheet
  const tx = PAD.left + (W - PAD.left - PAD.right) / 2, ty = PAD.top + (H - PAD.top - PAD.bottom) / 2
  let cx = (x0 + x1) / 2 - (tx - W / 2) / z
  let cy = (y0 + y1) / 2 - (ty - H / 2) / z
  cx = Math.min(W - W / (2 * z), Math.max(W / (2 * z), cx))
  cy = Math.min(H - H / (2 * z), Math.max(H / (2 * z), cy))
  return { cx, cy, z }
}

export const boxOf = (pts: Pt[]): [number, number, number, number] | null => {
  if (!pts.length) return null
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
  for (const p of pts) {
    x0 = Math.min(x0, p.x); y0 = Math.min(y0, p.y); x1 = Math.max(x1, p.x); y1 = Math.max(y1, p.y)
  }
  return [x0, y0, x1, y1]
}

// a point of the map to its place on the sheet under a view
export const toSheet = (v: View) => (p: Pt): Pt => ({
  x: (p.x - v.cx) * v.z + SHEET.width / 2,
  y: (p.y - v.cy) * v.z + SHEET.height / 2,
})
