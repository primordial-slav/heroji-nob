'use client'

import { memo, useCallback, useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from 'react'
import { LAND, SHEET } from '../map1941'
import { project } from '../projection'
import base from '../mapa.module.css'
import styles from './bataljon.module.css'
import { BETWEEN, EPISODES, SOURCE, type Episode, type Force, type LL, type Mark, type Pos, type Region, type Side, type Step } from './episodes'
import { lightOf, seasonOf, type Phase } from './light'

// A battalion's war as the book tells it, episode by episode: a close-up sheet in the main map's hand (ink on paper,
// the unit in red), the episode's card beside it, and the episodes along the months above. The sheet is in
// kilometres from its region's middle (terrain/<region>.ts); a view is the point at its middle and how many sheet
// units a kilometre takes

// Each region's ground, loaded when an episode there is first opened (the others follow in the background)
type Terrain = typeof import('./terrain/kapela')
const TERRAIN: Record<Region, () => Promise<Terrain>> = {
  kapela: () => import('./terrain/kapela'),
  kosinj: () => import('./terrain/kosinj'),
  glina: () => import('./terrain/glina'),
  slunj: () => import('./terrain/slunj'),
  dvor: () => import('./terrain/dvor'),
  lovinac: () => import('./terrain/lovinac'),
  gracac: () => import('./terrain/gracac'),
}
// the ground the sheet being drawn stands on, as Sheet last set it (like W and H)
let TR: Terrain

// The sheet is as large as the room the page gives it, a unit to a screen pixel, so its lettering always prints at
// the size it is set in (Sheet sets W and H as it renders; everything drawn in that render reads them)
let W = 1000
let H = 720
// the title block, the overview map and the key, as Sheet last set them: what lies under them gets no label
let FURNITURE: Box[] = []
// where the page fills the screen, sheet and card side by side and nothing to scroll
const FILL = '(min-width: 52rem) and (min-height: 32rem)'
const FRAME = 10, INNER = 14
const PAD = { l: 34, r: 34, t: 74, b: 34 }
type Pt = { x: number; y: number }
type View = { cx: number; cy: number; z: number }
type Box = [number, number, number, number]

const km = ([lon, lat]: LL): Pt => ({ x: (lon - TR.REGION.lon0) * TR.REGION.kx, y: (TR.REGION.lat0 - lat) * TR.REGION.ky })
const overlaps = (a: Box, b: Box) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]

function fitBox([w, s, e, n]: [number, number, number, number]): View {
  const a = km([w, n]), b = km([e, s])
  const z = Math.min((W - PAD.l - PAD.r) / (b.x - a.x), (H - PAD.t - PAD.b) / (b.y - a.y))
  const tx = PAD.l + (W - PAD.l - PAD.r) / 2, ty = PAD.t + (H - PAD.t - PAD.b) / 2
  return { cx: (a.x + b.x) / 2 - (tx - W / 2) / z, cy: (a.y + b.y) / 2 - (ty - H / 2) / z, z }
}
const toSheet = (v: View) => (p: Pt): Pt => ({ x: (p.x - v.cx) * v.z + W / 2, y: (p.y - v.cy) * v.z + H / 2 })
const seen = (v: View, grow = 0): Box => {
  const hw = W / (2 * v.z) + grow, hh = H / (2 * v.z) + grow
  return [v.cx - hw, v.cy - hh, v.cx + hw, v.cy + hh]
}

// every step of every episode, in order: what the arrows and the timeline walk through
const STEPS = EPISODES.flatMap((ep, e) => ep.steps.map((s, i) => ({ ep, e, s, i })))

// Who an enemy is, from the words that name it: Italians, the NDH's ustaše, gendarmes and domobrani, the Chetniks,
// the Germans. "Vojnici" alone are the episode's enemy
const FORCE_NAMES: Record<Force, string> = { it: 'Italijani', ndh: 'ustaše, oružnici, domobrani', cet: 'četnici', de: 'Nemci' }
function forceOf(text: string): Force | null {
  if (/ital|talij/i.test(text)) return 'it'                  // the book writes both Italijani and Talijani
  if (/četni/i.test(text)) return 'cet'
  if (/usta|oružni|domobran|žandar|milicion/i.test(text)) return 'ndh'
  if (/nemac|nemc|nemač/i.test(text)) return 'de'
  return null
}

// ---------- the view, moving ----------

// a test of the sheets (window.__bataljonTest) skips the moves, which a hidden window never finishes
const reducedMotion = () => typeof window !== 'undefined' && (window.matchMedia('(prefers-reduced-motion: reduce)').matches
  || Boolean((window as unknown as { __bataljonTest?: unknown }).__bataljonTest))

// From one frame to the next in about two thirds of a second, the zoom eased in its logarithm; a long way between
// two close-ups first draws back far enough to show both
function useMovingView(target: View, ease: boolean) {
  const [v, setV] = useState(target)
  const cur = useRef(target)
  useEffect(() => {
    const from = cur.current, to = target
    if (!ease || reducedMotion() || (Math.abs(from.cx - to.cx) < 1e-6 && Math.abs(from.cy - to.cy) < 1e-6 && from.z === to.z)) {
      cur.current = to; setV(to); return
    }
    const dist = Math.hypot(to.cx - from.cx, to.cy - from.cy)
    const wide = Math.min(from.z, to.z, (W * 0.8) / Math.max(dist * 1.4, 1e-6))
    const dip = Math.max(0, Math.log(Math.min(from.z, to.z)) - Math.log(wide))
    const dur = 620 + Math.min(600, dip * 380)
    const t0 = performance.now()
    let raf = 0
    const tick = (now: number) => {
      const u = Math.min(1, (now - t0) / dur)
      const e = u < 0.5 ? 4 * u * u * u : 1 - (-2 * u + 2) ** 3 / 2
      const z = Math.exp(Math.log(from.z) * (1 - e) + Math.log(to.z) * e - 4 * e * (1 - e) * dip)
      const next = { cx: from.cx + (to.cx - from.cx) * e, cy: from.cy + (to.cy - from.cy) * e, z }
      cur.current = next
      setV(next)
      if (u < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target.cx, target.cy, target.z, ease])     // eslint-disable-line react-hooks/exhaustive-deps
  // the reader's own moves follow the hand at once
  return ease ? v : target
}

// how far the reader may enlarge or draw back, and keep the region in the frame
const Z_MIN = 18, Z_MAX = 520
function held(v: View): View {
  const [x0, y0, x1, y1] = TR.REGION.bounds
  const z = Math.min(Z_MAX, Math.max(Z_MIN, v.z))
  return { z, cx: Math.min(x1, Math.max(x0, v.cx)), cy: Math.min(y1, Math.max(y0, v.cy)) }
}

// ---------- the ground ----------

// The ground in kilometres, drawn once for the area a move between two frames passes over: its lines keep their
// width in sheet units through the zoom (a width divided by z on each group)
const Ground = memo(function Ground({ area, t }: { area: Box; t: Terrain }) {
  const inside = (b: number[]) => overlaps(b as Box, area)
  return (
    <>
      <g className={styles.contours}>
        {t.CONTOURS.filter(c => inside(c.b)).map((c, i) => <path key={i} d={c.d} className={c.i ? styles.contourIndex : undefined} />)}
      </g>
      <g className={styles.lakes}>{t.LAKES.filter(l => inside(l.b)).map((l, i) => <path key={i} d={l.d} />)}</g>
      <g className={styles.rivers}>
        {t.RIVERS.filter(r => inside(r.b)).map((r, i) => <path key={i} d={r.d} className={r.big ? styles.riverBig : undefined} />)}
      </g>
      <g className={styles.roadsMinor}>{t.ROADS.filter(r => r.c >= 3 && inside(r.b)).map((r, i) => <path key={i} d={r.d} className={r.c === 4 ? styles.track : undefined} />)}</g>
      {/* the main roads cased, a paper line between two ink ones */}
      <g className={styles.roadsCase}>{t.ROADS.filter(r => r.c <= 2 && inside(r.b)).map((r, i) => <path key={i} d={r.d} />)}</g>
      <g className={styles.roadsFill}>{t.ROADS.filter(r => r.c <= 2 && inside(r.b)).map((r, i) => <path key={i} d={r.d} />)}</g>
      {/* the railway as the old sheets draw it, black and white in turn; a tunnel a fine dashed line */}
      <g className={styles.railTunnel}>{t.RAIL.filter(r => r.tunnel && inside(r.b)).map((r, i) => <path key={i} d={r.d} />)}</g>
      <g className={styles.railCase}>{t.RAIL.filter(r => !r.tunnel && inside(r.b)).map((r, i) => <path key={i} d={r.d} />)}</g>
      <g className={styles.railFill}>{t.RAIL.filter(r => !r.tunnel && inside(r.b)).map((r, i) => <path key={i} d={r.d} />)}</g>
    </>
  )
})

// widths in sheet units, whatever the zoom
function groundStyle(z: number) {
  const px = (n: number) => `${(n / z).toFixed(5)}`
  return {
    '--w-contour': px(0.45), '--w-index': px(0.8), '--w-river': px(0.7), '--w-river-big': px(1.4),
    '--w-road-minor': px(0.65), '--w-track': px(0.45), '--d-track': `${px(3)} ${px(2.2)}`,
    '--w-road-case': px(2.6), '--w-road-fill': px(1.2),
    '--w-rail-case': px(2.6), '--w-rail-fill': px(1.3), '--d-rail': `${px(5)} ${px(5)}`,
    '--w-tunnel': px(0.9), '--d-tunnel': `${px(2)} ${px(2)}`, '--w-lake': px(0.7),
  } as CSSProperties
}

// The book's own spelling where the map's sources write a place otherwise (today's names, mostly)
const AS_IN_BOOK: Record<string, string> = {
  'Križpolje': 'Krišpolje', 'Kunić': 'Kunić-Selo',
  'Bakovac Kosinjski': 'Kosinjski Bakovac', 'Drenovac Banski': 'Drenovac', 'Donji Klasnić': 'Klasnić', 'Rudići': 'Rudić',
  'Slunjčica': 'Slušnica', 'Golubovac Divuški': 'Golubovac', 'Novi Grad': 'Bosanski Novi',
  'Hrvatska Kostajnica': 'Kostajnica', 'Kostajnica': 'Bosanska Kostajnica', 'Bagunica': 'Bogunica',
  'Rudopolje Bruvanjsko': 'Rudopolje', 'Brezovac Dobroselski': 'Brezovac', 'Pavlovac Vrebački': 'Pavlovac',
}
const bookName = (n: string) => AS_IN_BOOK[n] ?? n

// ---------- lettering on the ground ----------

// The heights worth a name: a mountain's top, with no higher named peak within 2.5 km; closer in, the lesser tops
// with none within 1.2 km. Worked out once a region
type Peak = Terrain['PEAKS'][number]
const PEAK_SETS = new Map<string, { summits: Peak[]; tops: Peak[] }>()
function peaksOf(t: Terrain) {
  let p = PEAK_SETS.get(t.REGION.key)
  if (!p) {
    const dominant = (r: number) => t.PEAKS.filter(a => !t.PEAKS.some(o => o.h > a.h && Math.hypot(o.x - a.x, o.y - a.y) < r))
    p = { summits: dominant(2.5), tops: dominant(1.2) }
    PEAK_SETS.set(t.REGION.key, p)
  }
  return p
}

// How much the sheet names, by how far the reader has enlarged it past the step's own frame (k): at the frame the
// towns, the villages, the episode's own places and a few summits; the hamlets from half again as large; at two and
// a half times the lesser tops and more hamlets. The localities only where the episode names them
function detail(k: number) {
  const { summits, tops } = peaksOf(TR)
  return {
    hamlets: k >= 2.5 ? 24 : k >= 1.5 ? 10 : 0,
    peaks: k >= 2.5 ? tops : summits,
    mostPeaks: k >= 2.5 ? 12 : k >= 1.5 ? 8 : 5,
  }
}

// A name the episode's text uses is one place: of the sheet's places of that name the largest, then the one nearest
// the ground its marks stand on. Its namesakes go unnamed, lest the reader take them for it (OSM has a hamlet Udbina
// by Vrebac and three hamlets Baste on the Lovinac sheet)
type Place = Terrain['PLACES'][number]
function namedPlaces(ep: Episode): Map<string, Place> {
  const wanted = new Set(ep.places)
  const ground: Pt[] = []
  const walk = (x: unknown) => {
    if (!Array.isArray(x) && (typeof x !== 'object' || x === null)) return
    if (Array.isArray(x) && x.length === 2 && typeof x[0] === 'number' && typeof x[1] === 'number') ground.push(km(x as LL))
    else for (const y of Object.values(x)) walk(y)
  }
  walk([ep.base, ep.steps])
  const off = (p: Place) => Math.min(...ground.map(g => Math.hypot(p.x - g.x, p.y - g.y)))
  const best = new Map<string, Place>()
  for (const p of TR.PLACES) {
    if (!wanted.has(p.name)) continue
    const b = best.get(p.name)
    if (!b || p.r < b.r || (p.r === b.r && off(p) < off(b))) best.set(p.name, p)
  }
  return best
}

// Places, stations and heights, each named only where its name finds room, the episode's own places first; with
// the room the marks' labels and the sheet's furniture already took
// f: how much larger the lettering is than at the step's own frame (it grows as the reader enlarges the map)
function groundLabels(v: View, ep: Episode, taken: Box[], f: number, k: number): ReactNode[] {
  const T = toSheet(v)
  const box = seen(v, 0.3)
  const out: ReactNode[] = []
  const placed: Box[] = [...taken]
  const fits = (b: Box) => b[0] > INNER + 2 && b[2] < W - INNER - 2 && b[1] > INNER + 2 && b[3] < H - INNER - 2 && !placed.some(o => overlaps(o, b))
  const named = namedPlaces(ep)
  // the towns and villages always, the hamlets only close in and not too many, the localities only where the
  // episode names them
  const d = detail(k)
  const maxRank = d.hamlets ? 2 : 1
  const places = TR.PLACES.filter(p => p.x > box[0] && p.x < box[2] && p.y > box[1] && p.y < box[3])
    .filter(p => named.has(p.name) ? named.get(p.name) === p : p.r <= maxRank)
    .sort((a, b) => Number(named.has(b.name)) - Number(named.has(a.name)) || a.r - b.r)
  let hamlets = 0
  for (const p of places) {
    if (p.r >= 2 && !named.has(p.name) && hamlets >= d.hamlets) continue
    const at = T(p), name = bookName(p.name), key = named.has(p.name)
    const size = (p.r === 0 ? 16 : p.r === 1 ? 13.5 : p.r === 2 ? 11.8 : 10.6) * f
    const fs = key ? size + 1.4 * f : size
    const w = name.length * fs * 0.5
    // the name to the right of its mark, else to the left, else above
    const tries: [number, number, 'start' | 'end' | 'middle'][] = [[at.x + 5 * f, at.y + fs * 0.35, 'start'], [at.x - 5 * f, at.y + fs * 0.35, 'end'], [at.x, at.y - 5 * f, 'middle']]
    let done = false
    for (const [x, y, anchor] of tries) {
      const x0 = anchor === 'start' ? x : anchor === 'end' ? x - w : x - w / 2
      const b: Box = [x0 - 1, y - fs * 0.85, x0 + w + 1, y + fs * 0.25]
      const mark: Box = [at.x - 2.6, at.y - 2.6, at.x + 2.6, at.y + 2.6]
      if (!fits(b) || placed.some(o => overlaps(o, mark))) continue
      placed.push(b, mark)
      if (p.r >= 2 && !named.has(p.name)) hamlets++
      out.push(
        <g key={`p${p.name}${p.x}`}>
          {p.r <= 1 ? <circle cx={at.x} cy={at.y} r={p.r === 0 ? 3.2 : 2.3} className={base.markOpen} /> : <circle cx={at.x} cy={at.y} r={1.3} className={base.markFull} />}
          {p.r === 0 && <circle cx={at.x} cy={at.y} r={1} className={base.markFull} />}
          <text x={x} y={y} textAnchor={anchor} fontSize={fs} className={`${styles.halo} ${p.r >= 2 && !key ? styles.placeSmall : ''}`}>{name}</text>
          <text x={x} y={y} textAnchor={anchor} fontSize={fs} className={p.r >= 2 && !key ? styles.placeSmall : key ? styles.placeKey : undefined}>{name}</text>
        </g>,
      )
      done = true
      break
    }
    void done
  }
  // the stations by the line, a short bar across it
  for (const s of TR.STATIONS) {
    if (s.x < box[0] || s.x > box[2] || s.y < box[1] || s.y > box[3]) continue
    const at = T(s)
    const b: Box = [at.x - 3.5, at.y - 3.5, at.x + 3.5, at.y + 3.5]
    if (placed.some(o => overlaps(o, b))) continue
    placed.push(b)
    out.push(<rect key={`s${s.name}`} x={at.x - 3.4} y={at.y - 1.7} width={6.8} height={3.4} className={styles.station} />)
  }
  // the named heights, the highest first, a fine triangle and the height under the name
  if (v.z >= 40) {
    const peaks = d.peaks.filter(p => p.x > box[0] && p.x < box[2] && p.y > box[1] && p.y < box[3]).sort((a, b) => b.h - a.h)
    let named = 0
    for (const p of peaks) {
      if (named >= d.mostPeaks) break
      const at = T(p)
      const w = Math.max(p.name.length * 10.6 * f * 0.5, 22 * f)
      const b: Box = [at.x - w / 2 - 1, at.y - 3.5, at.x + w / 2 + 1, at.y + 24 * f]
      if (!fits(b)) continue
      placed.push(b)
      named++
      out.push(
        <g key={`h${p.name}${p.x}`} className={styles.peak}>
          <path d={`M${at.x} ${at.y - 2.6}l2.4 4.2h-4.8z`} />
          <text x={at.x} y={at.y + 12.5 * f} textAnchor="middle" fontSize={10.6 * f}>{p.name}</text>
          <text x={at.x} y={at.y + 23 * f} textAnchor="middle" fontSize={9.6 * f} className={styles.peakHeight}>{p.h}</text>
        </g>,
      )
    }
  }
  return out
}

// ---------- the marks ----------

// a seeded wobble, so a unit's place reads as drawn by hand and stays the same drawing every time
function wobble(seed: number) {
  let s = seed
  return () => { s = (s * 16807) % 2147483647; return s / 2147483647 }
}

// a closed smooth line through points (Catmull-Rom as cubic Béziers)
function closedCurve(pts: Pt[]) {
  const n = pts.length
  let d = `M${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n]
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 }
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 }
    d += `C${c1.x.toFixed(1)} ${c1.y.toFixed(1)} ${c2.x.toFixed(1)} ${c2.y.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`
  }
  return d + 'Z'
}

function openCurve(pts: Pt[]) {
  if (pts.length < 3) return pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join('')
  let d = `M${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 }
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 }
    d += `C${c1.x.toFixed(1)} ${c1.y.toFixed(1)} ${c2.x.toFixed(1)} ${c2.y.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`
  }
  return d
}

// a point and the way the line runs at a fraction of its length
function along(pts: Pt[], f: number): { p: Pt; a: number } {
  const seg = pts.slice(1).map((p, i) => Math.hypot(p.x - pts[i].x, p.y - pts[i].y))
  const total = seg.reduce((s, x) => s + x, 0)
  let run = f * total
  for (let i = 0; i < seg.length; i++) {
    if (run <= seg[i] || i === seg.length - 1) {
      const u = seg[i] ? Math.min(1, run / seg[i]) : 0
      const a = pts[i], b = pts[i + 1]
      return { p: { x: a.x + (b.x - a.x) * u, y: a.y + (b.y - a.y) * u }, a: Math.atan2(b.y - a.y, b.x - a.x) }
    }
    run -= seg[i]
  }
  return { p: pts[0], a: 0 }
}

const OFF: Record<Pos, [number, number, 'start' | 'middle' | 'end']> = {
  n: [0, -9, 'middle'], ne: [7, -7, 'start'], e: [9, 4, 'start'], se: [7, 14, 'start'],
  s: [0, 17, 'middle'], sw: [-7, 14, 'end'], w: [-9, 4, 'end'], nw: [-7, -7, 'end'],
}

// the battalion, the brigade's other battalions, the other partisan units (brigades, odredi), the enemy
const ink = (side: Side) => (side === 'enemy' ? styles.enemy : side === 'own' ? styles.own : side === 'ally' ? styles.ally : styles.friend)

// a mark's label, its room taken at once (the ground's names are set after the marks' and keep off them)
// the sides a label may take, nearest first to the one asked for
const SIDES: Pos[] = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
const sidesFrom = (lp: Pos): Pos[] => {
  const i = SIDES.indexOf(lp)
  return [0, 1, -1, 2, -2, 3, -3, 4].map(d => SIDES[(i + d + 8) % 8])
}

// A mark's label, its room taken at once (the ground's names are set after the marks' and keep off them). It stands
// on the side the data asks for, else on the nearest side where it covers no other label and none of the sheet's
// furniture; `around` gives an area's middle and size, so the label stands off its edge on whichever side it takes.
// A mark off the sheet gets no label: half a word at the frame's edge says nothing
function label(at: Pt, text: string, lp: Pos = 'e', side: Side, base: number, boxes: Box[], f = 1, force: Force | null = null,
  around?: { c: Pt; r: number }) {
  const mark = around ? around.c : at
  if (mark.x < INNER || mark.x > W - INNER || mark.y < INNER || mark.y > H - INNER) return null
  if (FURNITURE.some(b => mark.x > b[0] && mark.x < b[2] && mark.y > b[1] && mark.y < b[3])) return null
  const size = base * f
  const w = text.length * size * 0.5
  const place = (pos: Pos) => {
    const [ox, oy, anchor] = OFF[pos]
    const from = around
      ? { x: around.c.x + (pos === 'n' || pos === 's' ? 0 : Math.sign(ox) * around.r * 0.85), y: around.c.y + Math.sign(oy) * around.r * 0.55 }
      : at
    let x = from.x + ox * f, y = from.y + oy * f
    const left = anchor === 'start' ? x : anchor === 'end' ? x - w : x - w / 2
    // moved in where it would run past the frame
    x += Math.max(0, INNER + 6 - left) - Math.max(0, left + w - (W - INNER - 6))
    y += Math.max(0, INNER + 6 + size - y) - Math.max(0, y - (H - INNER - 6))
    const x0 = anchor === 'start' ? x : anchor === 'end' ? x - w : x - w / 2
    return { x, y, anchor, box: [x0 - 2, y - size * 0.85, x0 + w + 2, y + size * 0.3] as Box }
  }
  const tries = sidesFrom(lp).map(place)
  const free = tries.find(t => !boxes.some(o => overlaps(o, t.box))) ?? tries[0]
  boxes.push(free.box)
  const { x, y, anchor } = free
  return (
    <g key="label">
      <text x={x} y={y} textAnchor={anchor} fontSize={size} className={styles.halo}
        style={HALO ? { stroke: HALO.mark(x) } : undefined}>{text}</text>
      <text x={x} y={y} textAnchor={anchor} fontSize={size} className={`${styles.markLabel} ${ink(side)}`}
        style={force ? { fill: `var(--force-${force}-ink)` } : undefined}>{text}</text>
    </g>
  )
}

// Crossed sabres, the maps' sign for a fight, centred on 0,0
function Sabres() {
  return (
    <>
      <path d="M-6.5 6.5L6 -6M-5.4 2.9L-2.9 5.4M6.5 6.5L-6 -6M2.9 5.4L5.4 2.9" />
      <circle cx={-6.6} cy={6.6} r={0.9} />
      <circle cx={6.6} cy={6.6} r={0.9} />
    </>
  )
}

// One mark as the book sketches draw them: the battalion red and filled, the other partisan units red in outline,
// the enemy in ink
// an enemy mark's colour: its own, else its label's, else its episode's
const forceFor = (m: { force?: Force; label?: string }, foe: Force): Force => m.force ?? forceOf(m.label ?? '') ?? foe
const tinted = (force: Force) => ({ '--mark': `var(--force-${force}-ink)` }) as CSSProperties

function markShape(m: Mark, v: View, boxes: Box[], seed: number, f: number, foe: Force): ReactNode {
  const T = (ll: LL) => toSheet(v)(km(ll))
  switch (m.t) {
    case 'area': {
      const c = T(m.at), rnd = wobble(seed + 7)
      const rot = ((m.rot ?? 0) * Math.PI) / 180
      const pts: Pt[] = Array.from({ length: 14 }, (_, i) => {
        const a = (i / 14) * Math.PI * 2, f = 0.9 + rnd() * 0.2
        const x = Math.cos(a) * m.rx * v.z * f, y = Math.sin(a) * m.ry * v.z * f
        return { x: c.x + x * Math.cos(rot) - y * Math.sin(rot), y: c.y + x * Math.sin(rot) + y * Math.cos(rot) }
      })
      const r = Math.max(m.rx, m.ry) * v.z
      const lp = m.lp ?? 'e'
      const cls = m.side === 'own' ? styles.areaOwn : m.side === 'friend' ? styles.areaFriend : m.side === 'ally' ? styles.areaAlly : styles.areaEnemy
      const text = m.label && (m.guess ? `${m.label} (?)` : m.label)
      const force = m.side === 'enemy' ? forceFor(m, foe) : null
      return (
        <g>
          {force && <path d={closedCurve(pts)} className={m.guess ? styles.tintGuess : styles.tint} style={{ fill: `var(--force-${force})` }} />}
          <path d={closedCurve(pts)} className={`${cls} ${m.guess ? styles.areaGuess : ''}`}
            style={force ? { stroke: `var(--force-${force}-ink)` } : undefined} />
          {text && label(c, text, lp, m.side, m.side === 'own' ? 14.5 : m.side === 'ally' ? 13.4 : 12.8, boxes, f, force, { c, r })}
        </g>
      )
    }
    case 'move': {
      const pts = m.path.map(T)
      const end = pts[pts.length - 1], prev = pts[pts.length - 2]
      const a = Math.atan2(end.y - prev.y, end.x - prev.x) * 180 / Math.PI
      const force = m.side === 'enemy' ? forceFor(m, foe) : null
      const tint = force ? tinted(force) : undefined
      const cls = `${styles.move} ${ink(m.side)} ${styles[`move_${m.kind}`] ?? ''} ${m.side === 'own' ? styles.moveOwn : m.side === 'ally' ? styles.moveAlly : ''} ${m.guess ? styles.moveGuess : ''}`
      const head = m.kind === 'caught'
        ? <path d="M-5 -5L5 5M5 -5L-5 5" className={styles.caughtCross} />
        : m.kind === 'stopped'
          ? <path d="M0 -6.5V6.5" className={`${styles.moveBar} ${ink(m.side)}`} style={tint} />
          : m.kind === 'back'
            ? <path d="M-7 -4.6L0 0L-7 4.6" className={`${styles.moveOpenHead} ${ink(m.side)}`} style={tint} />
            : <path d={m.kind === 'fire' ? 'M1.5 0L-5 -2.6L-5 2.6Z' : 'M3 0L-7.5 -4.6L-5.3 0L-7.5 4.6Z'}
                className={`${styles.moveHead} ${ink(m.side)}`} style={tint} />
      const lab = m.label ? along(pts, m.at ?? 0.5).p : null
      return (
        <g>
          <path d={openCurve(pts)} className={cls} style={tint} />
          <g transform={`translate(${end.x.toFixed(1)} ${end.y.toFixed(1)}) rotate(${a.toFixed(0)}) scale(${m.side === 'own' ? 1.3 : 1.18})`}>{head}</g>
          {lab && m.label && label(lab, m.guess ? `${m.label} (?)` : m.label, m.lp, m.side, m.side === 'ally' ? 13 : 12.4, boxes, f, force)}
        </g>
      )
    }
    case 'ambush': {
      // the arc's middle faces the way the enemy comes; three strokes of fire reach across toward it
      const c = T(m.at), to = T(m.face)
      const dir = Math.atan2(to.y - c.y, to.x - c.x), r = 11 * Math.sqrt(f)
      const pt = (ang: number, rr: number) => `${(c.x + Math.cos(ang) * rr).toFixed(1)} ${(c.y + Math.sin(ang) * rr).toFixed(1)}`
      const arc = `M${pt(dir - 1.25, r)}A${r.toFixed(1)} ${r.toFixed(1)} 0 0 1 ${pt(dir + 1.25, r)}`
      const ticks = [-0.6, 0, 0.6].map(d => `M${pt(dir + d, r + 2)}L${pt(dir + d * 0.7, r + 9 * Math.sqrt(f))}`).join('')
      return (
        <g>
          <path d={arc} className={styles.ambush} />
          <path d={ticks} className={styles.ambushFire} />
          {m.label && label(c, m.guess ? `${m.label} (?)` : m.label, m.lp, 'own', 11.6, boxes, f)}
        </g>
      )
    }
    case 'post': {
      const p = T(m.at), s = (m.small ? 2.3 : 3) * Math.sqrt(f)
      return (
        <g>
          <rect x={p.x - s} y={p.y - s} width={2 * s} height={2 * s} className={m.taken ? styles.postTaken : m.guess ? styles.postGuess : styles.post}
            style={m.taken || m.guess ? { stroke: `var(--force-${forceFor(m, foe)}-ink)` } : { fill: `var(--force-${forceFor(m, foe)}-ink)` }} />
          {m.taken && <path d={`M${p.x - s - 2} ${p.y - s - 2}L${p.x + s + 2} ${p.y + s + 2}M${p.x + s + 2} ${p.y - s - 2}L${p.x - s - 2} ${p.y + s + 2}`} className={styles.takenCross} />}
          {label(p, m.guess ? `${m.label} (?)` : m.label, m.lp, 'enemy', m.small ? 11.6 : 12.4, boxes, f, forceFor(m, foe))}
        </g>
      )
    }
    case 'train': {
      const p = T(m.at)
      return (
        <g>
          <rect x={p.x - 6} y={p.y - 2.6} width={12} height={5.2} rx={1} className={m.armoured ? styles.trainArmoured : styles.train}
            style={m.armoured ? { fill: `var(--force-${forceFor(m, foe)}-ink)`, stroke: `var(--force-${forceFor(m, foe)}-ink)` } : { stroke: `var(--force-${forceFor(m, foe)}-ink)` }} />
          {label(p, m.guess ? `${m.label} (?)` : m.label, m.lp, 'enemy', 11.8, boxes, f, forceFor(m, foe))}
        </g>
      )
    }
    case 'cut': {
      const pts = m.path.map(T)
      const len = pts.slice(1).reduce((s, p, i) => s + Math.hypot(p.x - pts[i].x, p.y - pts[i].y), 0)
      const n = Math.max(2, Math.round(len / 7))
      const xs = Array.from({ length: n }, (_, i) => along(pts, n === 1 ? 0.5 : i / (n - 1)).p)
      const mid = along(pts, 0.5).p
      return (
        <g>
          <path d={xs.map(p => `M${(p.x - 2.6).toFixed(1)} ${(p.y - 2.6).toFixed(1)}l5.2 5.2m0 -5.2l-5.2 5.2`).join('')} className={styles.cut} />
          {m.label && label(mid, m.guess ? `${m.label} (?)` : m.label, m.lp, 'own', 11.8, boxes, f)}
        </g>
      )
    }
    case 'fight': {
      const p = T(m.at)
      return <g transform={`translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) scale(${(0.78 * Math.sqrt(f)).toFixed(2)})`} className={styles.sabres}><Sabres /></g>
    }
    case 'kota': {
      const p = T(m.at)
      return (
        <g>
          <path d={`M${p.x} ${p.y - 3.2}l3 5.2h-6z`} className={styles.kota} />
          {label(p, m.guess ? `${m.label} (?)` : m.label, m.lp, 'enemy', 11.8, boxes, f)}
        </g>
      )
    }
    case 'spot': {
      const p = T(m.at)
      return (
        <g>
          <circle cx={p.x} cy={p.y} r={2.6} className={styles.spot} />
          {label(p, m.guess ? `${m.label} (?)` : m.label, m.lp, 'enemy', 11.4, boxes, f)}
        </g>
      )
    }
  }
}

// ---------- the sheet's furniture ----------

const TITLE_TOP = INNER + 12

function ScaleBar({ x, y, z }: { x: number; y: number; z: number }) {
  const kmLen = [0.5, 1, 2, 5, 10].find(k => k * z >= 64) ?? 10
  const step = (kmLen * z) / 4
  return (
    <g className={base.scale}>
      {[0, 1, 2, 3].map(i => (
        <rect key={i} x={x - kmLen * z + i * step} y={y} width={step} height={3} className={i % 2 === 0 ? base.markFull : base.markOpen} />
      ))}
      {[0, kmLen / 2, kmLen].map(k => (
        <text key={k} x={x - kmLen * z + k * z} y={y + 11} textAnchor="middle" fontSize={7}>{String(k).replace('.', ',')}</text>
      ))}
      <text x={x + 5} y={y + 11} fontSize={7}>km</text>
    </g>
  )
}

// The whole country in small, in a corner, with a red spot where the episode is
const LOC_W = 118, LOC_S = LOC_W / SHEET.width, LOC_H = SHEET.height * LOC_S
function Locator({ at, x, y }: { at: LL; x: number; y: number }) {
  const [px, py] = project(at[0], at[1]).map(n => Math.round(n * LOC_S * 10) / 10)
  return (
    <g transform={`translate(${x} ${y})`} className={base.locator}>
      <rect width={LOC_W} height={LOC_H} className={base.locatorPaper} />
      <g transform={`scale(${LOC_S})`}><path d={LAND[0]} className={base.locatorLand} /></g>
      <circle cx={px} cy={py} r={6} className={styles.locatorHalo} />
      <circle cx={px} cy={py} r={3.2} className={styles.locatorSpot} />
    </g>
  )
}

const KEY_ROWS: [ReactNode, string][] = [
  [<path key="o" d="M2 -4.5C8 -6 16 -5 18 -1S12 5 6 4.5S-1 -2 2 -4.5Z" className={styles.areaOwn} />, 'Drugi bataljon'],
  [<path key="f" d="M2 -4.5C8 -6 16 -5 18 -1S12 5 6 4.5S-1 -2 2 -4.5Z" className={styles.areaFriend} />, 'ostali bataljoni brigade'],
  [<path key="l" d="M2 -4.5C8 -6 16 -5 18 -1S12 5 6 4.5S-1 -2 2 -4.5Z" className={styles.areaAlly} />, 'druge brigade i odredi'],
  [<g key="a"><path d="M0 0H15" className={`${styles.move} ${styles.own} ${styles.moveOwn}`} /><path d="M18 0L8 -4.4L10 0L8 4.4Z" className={`${styles.moveHead} ${styles.own}`} /></g>, 'napad'],
  [<g key="m"><path d="M0 0H15" className={`${styles.move} ${styles.own} ${styles.moveOwn} ${styles.move_march}`} /><path d="M18 0L8 -4.4L10 0L8 4.4Z" className={`${styles.moveHead} ${styles.own}`} /></g>, 'pokret (put približan)'],
  [<g key="z"><path d="M4 -7A8 8 0 0 1 4 7" className={styles.ambush} /><path d="M13 -4L17 -6M14 0L19 0M13 4L17 6" className={styles.ambushFire} /></g>, 'zaseda'],
  [<g key="u"><path d="M0 0H15" className={`${styles.move} ${styles.enemy}`} style={tinted('it')} /><path d="M13 -5L23 5M23 -5L13 5" className={styles.caughtCross} /></g>, 'neprijatelj upao u zasedu, razbijen'],
  [<g key="b"><path d="M0 0H17" className={`${styles.move} ${styles.own} ${styles.move_back}`} /><path d="M13 -4L19 0L13 4" className={`${styles.moveOpenHead} ${styles.own}`} /></g>, 'povlačenje'],
  [<g key="s"><path d="M0 0H18" className={`${styles.move} ${styles.enemy}`} /><path d="M18 -5.5V5.5" className={`${styles.moveBar} ${styles.enemy}`} /></g>, 'napad zaustavljen'],
  [<g key="v"><path d="M0 0H15" className={`${styles.move} ${styles.enemy} ${styles.move_fire}`} /><path d="M18 0L12 -2.4L12 2.4Z" className={`${styles.moveHead} ${styles.enemy}`} /></g>, 'vatra'],
  ...(['it', 'ndh', 'cet', 'de'] as Force[]).map(k => [
    <g key={k}><path d="M2 -4.5C8 -6 16 -5 18 -1S12 5 6 4.5S-1 -2 2 -4.5Z" className={styles.tint} style={{ fill: `var(--force-${k})` }} />
      <path d="M2 -4.5C8 -6 16 -5 18 -1S12 5 6 4.5S-1 -2 2 -4.5Z" className={styles.areaEnemy} /></g>, FORCE_NAMES[k]] as [ReactNode, string]),
  [<path key="g" d="M2 -4.5C8 -6 16 -5 18 -1S12 5 6 4.5S-1 -2 2 -4.5Z" className={`${styles.areaEnemy} ${styles.areaGuess}`} />, 'neprijatelj, verovatan položaj (?)'],
  [<g key="p"><rect x={7} y={-3} width={6} height={6} className={styles.post} /></g>, 'utvrđena zgrada, posada'],
  [<g key="t"><rect x={7} y={-3} width={6} height={6} className={styles.postTaken} /><path d="M5 -5L15 5M15 -5L5 5" className={styles.takenCross} /></g>, 'zauzeta posada'],
  [<g key="x" transform="translate(10 0) scale(0.6)" className={styles.sabres}><Sabres /></g>, 'borba'],
  [<path key="c" d="M2.4 -2.6l5.2 5.2m0 -5.2l-5.2 5.2M12.4 -2.6l5.2 5.2m0 -5.2l-5.2 5.2" className={styles.cut} />, 'porušena pruga, prekopana cesta'],
  [<g key="r"><path d="M0 0H20" className={styles.keyRailCase} /><path d="M0 0H20" className={styles.keyRailFill} /></g>, 'pruga'],
  [<g key="h"><path d="M0 0H20" className={styles.keyContour} /></g>, 'izohipse na 50 m'],
  [<g key="l" transform="translate(10 0) scale(0.62)"><PhaseSign phase="night" /></g>, 'doba dana po satu ili rečima knjige'],
]

const SEASON_CLASS = {
  summer: styles.seasonSummer, earlyAutumn: styles.seasonEarlyAutumn, autumn: styles.seasonAutumn, lateAutumn: styles.seasonLateAutumn,
  winter: styles.seasonWinter,
}
// the hours that shade the sheet (the day's light leaves it as it is); each layer fades in and out on its own
const LIGHTS: Phase[] = ['night', 'dawn', 'golden', 'dusk']
const LIGHT_CLASS: Record<Phase, string> = {
  night: styles.lightNight, dawn: styles.lightDawn, golden: styles.lightGolden, dusk: styles.lightDusk, day: '',
}

// The halo round a label is the paper as it shows under that label, so it reads as a gap in the lines and not as a
// white patch: the paper with the season's tint over it, and for the units' labels, which lie above the hour's light,
// that light too (at dawn and dusk the light at the label's place across the sheet). The tints multiply, as in the
// CSS, whose colours are read from the page; their strengths are bataljon.module.css's
type RGB = [number, number, number]
const SEASON_TINT: Partial<Record<ReturnType<typeof seasonOf>, [string, number]>> = {
  earlyAutumn: ['--season-early-autumn', 0.16], autumn: ['--season-autumn', 0.2],
  lateAutumn: ['--season-late-autumn', 0.22], winter: ['--season-winter', 0.2],
}
const LIGHT_TINT = { night: 0.4, nightDark: 0.55, golden: 0.18, low: 0.32 }
function rgbOf(css: string): RGB | null {
  const s = css.trim()
  const h = s.match(/^#([0-9a-f]{6})$/i)
  if (h) return [0, 2, 4].map(i => parseInt(h[1].slice(i, i + 2), 16)) as RGB
  const r = s.match(/^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i)
  return r ? [+r[1], +r[2], +r[3]] : null
}
const multiply = (c: RGB, t: RGB, a: number): RGB => c.map((v, i) => v * (1 - a + (a * t[i]) / 255)) as RGB
const mixed = (a: RGB, b: RGB, k: number): RGB => a.map((v, i) => v + (b[i] - v) * k) as RGB
const hex = (c: RGB) => `#${c.map(v => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('')}`
type Halo = { ground: string; mark: (x: number) => string }
let HALO: Halo | null = null

function haloOf(el: Element, season: ReturnType<typeof seasonOf>, phase: Phase | undefined): Halo | null {
  const cs = getComputedStyle(el)
  const v = (name: string) => rgbOf(cs.getPropertyValue(name))
  const paper = v('--surface')
  if (!paper) return null
  const tint = SEASON_TINT[season]
  const seasoned = tint && v(tint[0]) ? multiply(paper, v(tint[0])!, tint[1]) : paper
  const ground = hex(seasoned)
  const night = v('--light-night'), golden = v('--light-golden'), low = v('--light-low-sun')
  const dark = paper[0] + paper[1] + paper[2] < 3 * 128
  if (phase === 'night' && night) {
    const c = hex(multiply(seasoned, night, dark ? LIGHT_TINT.nightDark : LIGHT_TINT.night))
    return { ground, mark: () => c }
  }
  if (phase === 'golden' && golden) {
    const c = hex(multiply(seasoned, golden, LIGHT_TINT.golden))
    return { ground, mark: () => c }
  }
  if ((phase === 'dawn' || phase === 'dusk') && night && low) {
    // dawn: the night still in the west, the sun in the east; dusk the other way round
    const [west, east] = phase === 'dawn' ? [night, low] : [low, night]
    return { ground, mark: (x: number) => hex(multiply(seasoned, mixed(west, east, Math.max(0, Math.min(1, x / W))), LIGHT_TINT.low)) }
  }
  return { ground, mark: () => ground }
}

// The step's light by the date in the title block: a moon, the sun high, low, or half over the horizon (rising and
// setting are told apart by a small arrow). Drawn about (0, 0), some 16 units across
function PhaseSign({ phase }: { phase: Phase }) {
  if (phase === 'night') return <path d="M2.5 -6.5A6.6 6.6 0 1 0 6.4 4.3A5.2 5.2 0 1 1 2.5 -6.5Z" className={styles.phaseFill} />
  if (phase === 'day') {
    return (
      <g className={styles.phaseLine}>
        <circle r={3.2} />
        {[0, 45, 90, 135, 180, 225, 270, 315].map(a => (
          <path key={a} d="M0 -5.2V-7.4" transform={`rotate(${a})`} />
        ))}
      </g>
    )
  }
  if (phase === 'golden') {
    return (
      <g className={styles.phaseLine}>
        <path d="M-7.5 4.5H7.5" />
        <circle cy={-0.6} r={3} />
        {[-60, -30, 0, 30, 60].map(a => <path key={a} d="M0 -4.6V-6.3" transform={`translate(0 -0.6) rotate(${a})`} />)}
      </g>
    )
  }
  return (
    <g className={styles.phaseLine}>
      <path d="M-7.5 2.5H7.5" />
      <path d="M-3.6 2.5A3.6 3.6 0 0 1 3.6 2.5" />
      {[-50, 0, 50].map(a => <path key={a} d="M0 -2.4V-4" transform={`translate(0 2.5) rotate(${a}) translate(0 -2.6)`} />)}
      <path d={phase === 'dawn' ? 'M5.6 -3.2l1.6 -1.8 1.6 1.8' : 'M5.6 -5l1.6 1.8 1.6 -1.8'} />
    </g>
  )
}

const TAB_W = 112, TAB_H = 22, KEY_W = 196, KEY_ROW = 13

function MapKey({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  const heading = (w: number, up: boolean) => (
    <g role="button" tabIndex={0} aria-expanded={open} aria-label={open ? 'Sklopi tumač znakova' : 'Otvori tumač znakova'}
      className={base.keyTab} onClick={onToggle}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle() } }}>
      <rect width={w} height={TAB_H} className={base.keyTabHit} />
      <text x={10} y={14.5} fontSize={7.5} letterSpacing="0.35em">TUMAČ ZNAKOVA</text>
      <path d={up ? `M${w - 16} 13.5l4 -4 4 4` : `M${w - 16} 9.5l4 4 4 -4`} className={base.keyChevron} />
    </g>
  )
  if (!open) {
    return (
      <g transform={`translate(${INNER + 8} ${H - INNER - 8 - TAB_H})`} className={base.lettering}>
        <rect width={TAB_W} height={TAB_H} className={base.legendFrame} />
        {heading(TAB_W, true)}
      </g>
    )
  }
  const h = 28 + KEY_ROWS.length * KEY_ROW
  return (
    <g transform={`translate(${INNER + 8} ${H - INNER - 8 - h})`} className={base.lettering}>
      <rect width={KEY_W} height={h} className={base.legendFrame} />
      {heading(KEY_W, false)}
      {KEY_ROWS.map(([mark, text], i) => (
        <g key={text} transform={`translate(10 ${28 + i * KEY_ROW})`}>
          {mark}
          <text x={28} y={2.8} fontSize={7.8}>{text}</text>
        </g>
      ))}
    </g>
  )
}

// ---------- what stands, step by step ----------

// A unit's place, a strongpoint, a dug-up road and a height stand until a later step draws them again; a move, a
// fight, a train and an ambush belong to their own step alone
const STANDS = new Set<Mark['t']>(['area', 'post', 'cut', 'kota', 'spot'])

// which unit or thing a mark is, so a later step's mark of it takes its place: an area by the unit its label names
// ("II bat., 150" and an unlabelled area of the battalion are both the II), a strongpoint by its name before the
// colon ("sisaljka: 13 zarobljenih" is the sisaljka)
function standKey(m: Mark): string {
  const head = (t?: string) => (t ?? '').split(/,| bat| \(|:/)[0].trim()
  if (m.id && STANDS.has(m.t)) return `${m.t}:id:${m.id}`
  switch (m.t) {
    case 'area': return `area:${m.side}:${head(m.label) || (m.side === 'own' ? 'II' : m.side)}`
    case 'post': return `post:${head(m.label)}`
    case 'cut': return `cut:${m.label ?? m.path.map(p => p.join(',')).join(' ')}`
    case 'kota': return `kota:${m.label}`
    case 'spot': return `spot:${m.label}`
    default: return ''
  }
}

// each standing thing as the last step up to this one drew it, with the label an earlier step gave it if this one
// gives none (the battalion drawn again without its name is still the II)
function standingAt(ep: Episode, si: number): Map<string, { m: Mark; k: number }> {
  const out = new Map<string, { m: Mark; k: number }>()
  ep.steps.slice(0, si + 1).forEach((s, k) => s.marks.forEach(m => {
    if (!STANDS.has(m.t)) return
    const key = standKey(m)
    const before = out.get(key)?.m as (Mark & { label?: string; lp?: Pos }) | undefined
    const own = m as Mark & { label?: string; lp?: Pos }
    const label = own.label ?? before?.label
    out.set(key, { m: (label && !own.label ? { ...m, label, lp: before?.lp } : m) as Mark, k })
  }))
  // a thing drawn with `until` is gone from that step on: an enemy's piece of a town once the town is his again whole
  for (const [key, { m }] of out) if (m.until !== undefined && si >= m.until) out.delete(key)
  return out
}

// the same hand-drawn wobble for a unit wherever it is drawn
const seedOf = (key: string) => [...key].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 2147483647, 7) || 7

// ---------- the sheet ----------

function Sheet({ ep, si, t }: { ep: Episode; si: number; t: Terrain }) {
  TR = t
  const step = ep.steps[si]
  // the room the page gives the sheet, where it fills the screen; elsewhere the sheet keeps its own shape
  const room = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ w: 1000, h: 720, measured: false })
  useEffect(() => {
    const el = room.current
    if (!el) return
    const mq = window.matchMedia(FILL)
    const measure = () => {
      const w = Math.round(el.clientWidth)
      if (!w) return
      const h = mq.matches ? Math.round(el.clientHeight) : Math.round(w * 0.72)
      setSize(o => (o.measured && o.w === w && o.h === h ? o : { w: Math.max(280, w), h: Math.max(240, h), measured: true }))
    }
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    mq.addEventListener('change', measure)
    measure()
    return () => { ro.disconnect(); mq.removeEventListener('change', measure) }
  }, [])
  W = size.w
  H = size.h
  const TITLE_RIGHT = W - INNER - 14
  const fitted = useMemo(() => fitBox(step.view ?? ep.view), [ep, step, size])
  // the reader's frame, from the buttons, Shift and the wheel, or a drag; until the step changes or "Vrati okvir"
  const [manual, setManual] = useState<View | null>(null)
  useEffect(() => setManual(null), [ep, si])
  const target = manual ?? fitted
  const v = useMovingView(target, !manual)
  // the lettering grows as the map is enlarged, more slowly than the map, so more names find room as they grow
  const k = v.z / fitted.z
  const f = Math.min(1.9, Math.max(0.85, k ** 0.45))
  // the ground is drawn for the area a move passes over: the last frame's and this one's
  const last = useRef(target)
  const [area, setArea] = useState<Box>(() => seen(target, 1))
  useEffect(() => {
    const a = seen(last.current, 1), b = seen(target, 1)
    last.current = target
    setArea([Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])])
  }, [fitted])                                    // eslint-disable-line react-hooks/exhaustive-deps
  // and grown when the reader moves past it
  useEffect(() => {
    const s = seen(v)
    if (s[0] < area[0] || s[1] < area[1] || s[2] > area[2] || s[3] > area[3]) setArea(seen(v, 3))
  }, [v, area])

  const wrap = useRef<HTMLDivElement>(null)
  const live = useRef({ v, setManual })
  live.current = { v, setManual }
  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const at = (e: { clientX: number; clientY: number }) => {
      const r = el.getBoundingClientRect()
      return { x: ((e.clientX - r.left) / r.width) * W, y: ((e.clientY - r.top) / r.height) * H }
    }
    // Shift and the wheel, or a pinch on a touchpad (the browser sends it as the wheel with Ctrl), enlarge at the
    // pointer: the place under it stays under it
    const onWheel = (e: WheelEvent) => {
      if (!e.shiftKey && !e.ctrlKey) return
      const d = e.deltaY || e.deltaX
      if (!d) return
      e.preventDefault()
      const { v: cur, setManual: set } = live.current
      const p = at(e)
      const z = Math.min(Z_MAX, Math.max(Z_MIN, cur.z * Math.exp(-d * (e.deltaMode === 1 ? 0.08 : e.ctrlKey ? 0.01 : 0.002))))
      const wx = (p.x - W / 2) / cur.z + cur.cx, wy = (p.y - H / 2) / cur.z + cur.cy
      set(held({ z, cx: wx - (p.x - W / 2) / z, cy: wy - (p.y - H / 2) / z }))
    }
    let drag: { x: number; y: number; v: View; moved: boolean } | null = null
    const onDown = (e: PointerEvent) => {
      if (e.pointerType !== 'mouse' || e.button !== 0) return
      if ((e.target as Element).closest('button, [role="button"], a')) return
      const p = at(e)
      drag = { x: p.x, y: p.y, v: live.current.v, moved: false }
    }
    const onMove = (e: PointerEvent) => {
      if (!drag) return
      const p = at(e)
      if (!drag.moved && Math.hypot(p.x - drag.x, p.y - drag.y) < 4) return
      drag.moved = true
      el.classList.add(base.dragging)
      const d0 = drag.v
      live.current.setManual(held({ z: d0.z, cx: d0.cx - (p.x - drag.x) / d0.z, cy: d0.cy - (p.y - drag.y) / d0.z }))
    }
    const onUp = () => { el.classList.remove(base.dragging); drag = null }
    const noDrag = (e: DragEvent) => e.preventDefault()
    el.addEventListener('dragstart', noDrag)
    el.addEventListener('wheel', onWheel, { passive: false })
    el.addEventListener('pointerdown', onDown)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      el.removeEventListener('dragstart', noDrag)
      el.removeEventListener('wheel', onWheel)
      el.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [])
  const zoomBy = (f: number) => setManual(held({ ...v, z: v.z * f }))

  const [keyOpen, setKeyOpen] = useState(false)
  useEffect(() => { try { setKeyOpen(window.localStorage.getItem('bataljon-tumac') === '1') } catch { /* folded */ } }, [])
  const toggleKey = () => setKeyOpen(o => {
    try { window.localStorage.setItem('bataljon-tumac', o ? '0' : '1') } catch { /* not kept */ }
    return !o
  })

  // the title block: the battalion, its brigade, then the step's day large and its hour
  const when = step.time ?? step.when ?? ''
  const light = lightOf(ep, si)
  const season = seasonOf(step.date)
  // the halos' colours (haloOf), from the page's colours once the sheet is drawn, and again when the theme changes
  const svgRef = useRef<SVGSVGElement>(null)
  const [theme, setTheme] = useState(0)
  useEffect(() => {
    const bump = () => setTheme(n => n + 1)
    const mo = new MutationObserver(bump)
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => mo.disconnect()
  }, [])
  const [halo, setHalo] = useState<Halo | null>(null)
  useEffect(() => {
    if (svgRef.current) setHalo(haloOf(svgRef.current, season, light?.phase))
  }, [season, light?.phase, theme])
  HALO = halo
  const titleW = 268
  const titleBox: Box = [TITLE_RIGHT - titleW, TITLE_TOP - 6, TITLE_RIGHT + 6, TITLE_TOP + 86]
  // the country in small goes to the corner this step's marks leave emptiest: bottom right, else top left (under the
  // zoom buttons), else bottom left (over the key's folded tab)
  const locBox: Box = useMemo(() => {
    const T = toSheet(v)
    const pts: Pt[] = []
    const add = (m: Mark) => {
      if ('path' in m) m.path.forEach(ll => pts.push(T(km(ll))))
      if (m.t !== 'move' && 'at' in m) pts.push(T(km(m.at)))   // a move's 'at' is where its label sits along it
    }
    ep.base.forEach(add)
    standingAt(ep, si).forEach(({ m }) => add(m))
    step.marks.forEach(add)
    const corners: Box[] = [
      [W - INNER - 10 - LOC_W, H - INNER - 10 - LOC_H, W - INNER - 10, H - INNER - 10],
      [INNER + 10, INNER + 46, INNER + 10 + LOC_W, INNER + 46 + LOC_H],
      ...(keyOpen ? [] : [[INNER + 10, H - INNER - 18 - TAB_H - LOC_H, INNER + 10 + LOC_W, H - INNER - 18 - TAB_H] as Box]),
    ]
    const count = (b: Box) => pts.filter(p => p.x > b[0] - 10 && p.x < b[2] + 10 && p.y > b[1] - 10 && p.y < b[3] + 10).length
    return corners.reduce((best, c) => (count(c) < count(best) ? c : best), corners[0])
  }, [ep, si, step, keyOpen, size, fitted])      // eslint-disable-line react-hooks/exhaustive-deps
  const keyBox: Box = [INNER + 4, H - INNER - 12 - (keyOpen ? 28 + KEY_ROWS.length * KEY_ROW : TAB_H), INNER + 12 + (keyOpen ? KEY_W : TAB_W), H - INNER - 4]
  const middle = ep.view
  const at: LL = [(middle[0] + middle[2]) / 2, (middle[1] + middle[3]) / 2]

  // the marks: what stands through the episode; where each unit and strongpoint stands now, as the last step that
  // drew it left it; and this step's own actions, which are gone at the next
  const boxes: Box[] = [titleBox, locBox, keyBox]
  FURNITURE = [titleBox, locBox, keyBox]
  const marks: ReactNode[] = []
  ep.base.forEach((m, i) => {
    if (m.until === undefined || si < m.until) marks.push(<g key={`b${i}`} className={styles.baseMark}>{markShape(m, v, boxes, i + 1, f, ep.foe)}</g>)
  })
  const standing = standingAt(ep, si)
  for (const [key, { m, k }] of standing) {
    marks.push(<g key={`s${key}`} className={k === si ? styles.nowMark : undefined}>{markShape(m, v, boxes, seedOf(key), f, ep.foe)}</g>)
  }
  step.marks.forEach((m, i) => {
    if (!STANDS.has(m.t)) marks.push(<g key={`n${si}-${i}`} className={styles.nowMark}>{markShape(m, v, boxes, si * 31 + i + 3, f, ep.foe)}</g>)
  })
  const labels = groundLabels(v, ep, boxes, f, k)
  const ground = `translate(${(W / 2 - v.cx * v.z).toFixed(2)} ${(H / 2 - v.cy * v.z).toFixed(2)}) scale(${v.z.toFixed(4)})`

  return (
    <div className={styles.sheetColumn}>
      <div className={`${base.scroller} ${styles.room}`} ref={room}>
      <div className={`${base.sheetWrap} ${styles.sheetWrap}`} ref={wrap}>
        <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className={`${base.sheet} ${styles.sheet}`} role="img" aria-label={`${ep.title}, ${step.date}`}
          style={{ ...(size.measured ? {} : { visibility: 'hidden' as const }), ...(halo ? { '--halo-ground': halo.ground } as CSSProperties : {}) }}>
          <defs>
            {/* the enemy's ground, hatched as on the books' one-colour sketches */}
            <pattern id="bat-hatch" width="4.2" height="4.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)" className={styles.hatch}>
              <line x1="0.5" y1="0" x2="0.5" y2="4.2" />
            </pattern>
            <filter id="bat-ink" x="-1%" y="-1%" width="102%" height="102%">
              <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="1" seed="7" result="grain" />
              <feDisplacementMap in="SourceGraphic" in2="grain" scale="0.8" xChannelSelector="R" yChannelSelector="G" />
            </filter>
            <clipPath id="bat-inside"><rect x={INNER} y={INNER} width={W - 2 * INNER} height={H - 2 * INNER} /></clipPath>
            {/* the low sun's light from the side it stands on: in the east at dawn, in the west at dusk */}
            <linearGradient id="bat-dawn" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0" className={styles.dawnWest} /><stop offset="1" className={styles.dawnEast} />
            </linearGradient>
            <linearGradient id="bat-dusk" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0" className={styles.duskWest} /><stop offset="1" className={styles.duskEast} />
            </linearGradient>
          </defs>
          <rect width={W} height={H} className={base.paper} />
          {/* the season, by the step's month: the paper yellows through the autumn */}
          <rect width={W} height={H} className={`${styles.season} ${SEASON_CLASS[season]}`} />
          <g clipPath="url(#bat-inside)">
            <g filter="url(#bat-ink)">
              <g transform={ground} style={groundStyle(v.z)}><Ground area={area} t={t} /></g>
            </g>
            <g className={base.lettering}>{labels}</g>
            {/* the light of the hour over the ground and its names, under the units, which stay legible */}
            <g aria-hidden="true">
              {LIGHTS.map(p => (
                <rect key={p} width={W} height={H} className={`${styles.light} ${LIGHT_CLASS[p]}`}
                  fill={p === 'dawn' ? 'url(#bat-dawn)' : p === 'dusk' ? 'url(#bat-dusk)' : undefined}
                  style={{ opacity: light?.phase === p ? 1 : 0 }} />
              ))}
            </g>
            <g className={base.lettering} filter="url(#bat-ink)">{marks}</g>
            <MapKey open={keyOpen} onToggle={toggleKey} />
            <Locator at={at} x={locBox[0]} y={locBox[1]} />
            <g className={base.lettering}>
              <rect x={titleBox[0]} y={titleBox[1]} width={titleBox[2] - titleBox[0]} height={titleBox[3] - titleBox[1]} className={base.titlePaper} />
              <text x={TITLE_RIGHT} y={TITLE_TOP + 12} textAnchor="end" fontSize={12.5} letterSpacing="0.06em">DRUGI BATALJON „PEKIŠA VUKSAN“</text>
              <text x={TITLE_RIGHT} y={TITLE_TOP + 25} textAnchor="end" fontSize={9.6} letterSpacing="0.06em">PRVE LIČKE PROLETERSKE BRIGADE</text>
              <text x={TITLE_RIGHT} y={TITLE_TOP + 52} textAnchor="end" fontSize={25} letterSpacing="0.02em" className={styles.titleDate}>{step.date}</text>
              {when && <text x={TITLE_RIGHT} y={TITLE_TOP + 66} textAnchor="end" fontSize={10.5} className={step.time ? styles.titleTime : styles.titleWhen}>{when}</text>}
              {light && (
                <g transform={`translate(${titleBox[0] + 20} ${TITLE_TOP + 45})`} className={styles.phaseSign}>
                  <title>{light.why}</title>
                  <circle r={10} className={styles.phaseHit} />
                  <PhaseSign phase={light.phase} />
                </g>
              )}
              <ScaleBar x={TITLE_RIGHT - 12} y={TITLE_TOP + 74} z={v.z} />
            </g>
          </g>
          <rect x={FRAME} y={FRAME} width={W - 2 * FRAME} height={H - 2 * FRAME} className={base.frameOuter} />
          <rect x={INNER} y={INNER} width={W - 2 * INNER} height={H - 2 * INNER} className={base.frameInner} />
        </svg>
        <div className={base.zoomTools}>
          <button type="button" className={base.zoomButton} aria-label="Uvećaj kartu" title="Uvećaj (Shift i točkić)" onClick={() => zoomBy(1.6)}>+</button>
          <button type="button" className={base.zoomButton} aria-label="Umanji kartu" title="Umanji (Shift i točkić)" onClick={() => zoomBy(1 / 1.6)}>−</button>
          {manual && <button type="button" className={base.resetView} onClick={() => setManual(null)}>Vrati okvir</button>}
        </div>
      </div>
      </div>
      <p className={styles.sheetHint}>Strelice ← → menjaju korak. Shift i točkić (ili dva prsta na dodirnoj podlozi) uvećavaju kartu, a prevlačenje mišem je pomera.</p>
    </div>
  )
}

// ---------- the episodes along the months ----------

const dayOf = (iso: string) => Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) / 864e5
// the line runs from the first episode to a few days past the last episode or rest
const AXIS_FROM = dayOf('1942-07-02')
const AXIS_TO = Math.max(...EPISODES.map(ep => dayOf(ep.end)), ...BETWEEN.map(b => dayOf(b.end))) + 3
const MONTHS_AXIS = [['1942-07-02', 'jul 1942.'], ['1942-08-01', 'avgust'], ['1942-09-01', 'septembar'],
  ['1942-10-01', 'oktobar'], ['1942-11-01', 'novembar'], ['1942-12-01', 'decembar'], ['1943-01-01', 'januar 1943.'],
  ['1943-02-01', 'februar'], ['1943-03-01', 'mart']] as const

// The line is time, though not evenly: each episode's bar and name need their room, and the weeks between take what
// is left in proportion to their length. Names stand above and below the line in turn (the last one ends at its bar),
// so a name must clear the one two episodes before it; where July's three crowd together the days there widen
const NAME_CH = 7.1, NAME_GAP = 10, BAR_MIN = 12, GAP_MIN = 3
function axisOf(width: number) {
  const eps = EPISODES.map((ep, i) => ({ s: dayOf(ep.start), e: dayOf(ep.end) + 1, w: (String(i + 1).length + 1 + ep.short.length) * NAME_CH + 6 }))
  // the breakpoints: the axis's ends and every episode's start and end; segment j runs from ts[j] to ts[j + 1], bar k
  // is segment 2k + 1 and the gap before episode k is segment 2k
  const ts = [AXIS_FROM, ...eps.flatMap(x => [x.s, x.e]), AXIS_TO]
  const days = ts.slice(1).map((t, j) => t - ts[j])
  const min: number[] = days.map((_, j) => (j % 2 ? BAR_MIN : j && j < days.length - 1 ? GAP_MIN : 0))
  const total = days.reduce((a, b) => a + b, 0)
  let xs: number[] = []
  for (let round = 0; round < 400; round++) {
    const base = Math.max(0.15, (width - min.reduce((a, b) => a + b, 0)) / total)
    xs = [0]
    days.forEach((d, j) => xs.push(xs[j] + min[j] + base * d))
    const start = (k: number) => (k === eps.length - 1 ? xs[2 * k + 2] - eps[k].w : xs[2 * k + 1])
    const end = (k: number) => (k === eps.length - 1 ? xs[2 * k + 2] : xs[2 * k + 1] + eps[k].w)
    let short = false
    for (let k = 0; k + 2 < eps.length; k++) {
      const need = end(k) + NAME_GAP - start(k + 2)
      if (need > 0.5) { min[2 * (k + 2)] += need; short = true; break }
    }
    if (!short) break
  }
  // a day where two segments meet is the end of the first; an episode's start (`late`) is the start of the last, so
  // an episode that begins the day after another ends still stands its gap's width apart
  const px = (d: number, late = false) => {
    let j = -1
    for (let i = 0; i < ts.length - 1; i++) if (d >= ts[i] && d <= ts[i + 1]) { j = i; if (!late) break }
    j = Math.max(0, Math.min(days.length - 1, j))
    return xs[j] + (days[j] ? ((d - ts[j]) / days[j]) * (xs[j + 1] - xs[j]) : late ? xs[j + 1] - xs[j] : 0)
  }
  return { px, length: xs[xs.length - 1] }
}

function Timeline({ e, go }: { e: number; go: (e: number, s: number) => void }) {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(1000)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(() => setWidth(Math.round(el.parentElement?.clientWidth ?? el.clientWidth) - 16))
    ro.observe(el.parentElement ?? el)
    return () => ro.disconnect()
  }, [])
  const { px, length } = useMemo(() => axisOf(Math.max(736, width)), [width])
  const at = (d: number) => `${px(d).toFixed(1)}px`
  // the months' names and the rests between the episodes share the line's foot: a month that would run past the
  // line's end goes unnamed, and a rest gives way to a month's name, or goes when too little of it is left to read
  const monthW = (name: string) => name.length * 6.4 + 8
  const months = MONTHS_AXIS.filter(([d]) => dayOf(d) <= AXIS_TO).map(([d, name]) => ({ d, name, x: px(dayOf(d)) }))
    .filter(m => m.x + monthW(m.name) <= length + 2)
  const rests = BETWEEN.map(b => {
    let x0 = px(dayOf(b.start)), x1 = px(dayOf(b.end) + 1)
    for (const m of months) {
      const m1 = m.x + monthW(m.name)
      if (x0 < m1 && m.x < x1) {
        if (m.x - x0 > x1 - m1) x1 = m.x - 3
        else x0 = m1 + 3
      }
    }
    return { ...b, x0, x1 }
  }).filter(b => b.x1 - b.x0 >= 30)
  return (
    <nav className={styles.timeline} aria-label="Epizode">
      <div className={styles.axis} ref={ref} style={{ width: `${Math.ceil(length)}px` }}>
        {months.map(({ d, name, x }, i) => (
          <span key={d} className={i ? styles.monthMark : styles.monthMarkFirst} style={{ left: `${x.toFixed(1)}px` }}>{name}</span>
        ))}
        {Array.from({ length: AXIS_TO - AXIS_FROM + 1 }, (_, i) => (
          <i key={i} className={styles.dayTick} style={{ left: at(AXIS_FROM + i) }} />
        ))}
        {rests.map(b => (
          <span key={b.start} className={styles.between} style={{ left: `${b.x0.toFixed(1)}px`, width: `${(b.x1 - b.x0).toFixed(1)}px` }}
            title={b.label}>{b.label}</span>
        ))}
        {EPISODES.map((ep, i) => {
          const from = px(dayOf(ep.start), true), to = px(dayOf(ep.end) + 1)
          return (
            <button key={ep.key} type="button" className={i === e ? styles.episodeOn : styles.episode}
              style={{ left: `${from.toFixed(1)}px`, width: `${(to - from).toFixed(1)}px` }}
              aria-current={i === e ? 'step' : undefined} onClick={() => go(i, 0)}
              title={`${ep.title}, ${ep.dates}`}>
              <span className={styles.episodeBar} />
              <span className={i === EPISODES.length - 1 ? styles.episodeNameEnd : styles.episodeName}><b>{i + 1}</b> {ep.short}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

// ---------- forces and units in the text ----------

// A number of men: "oko 100 Italijana", "pedesetak ljudi", "43 oružnika", "sedmorica"; and a company or platoon the
// text names ("Treća četa", "Druga četa kordunaškog bataljona", "prvi vod"), on the battalion's red. The army's
// shorthand for them (3/II) is the map's; the text keeps the book's words
const NUM = String.raw`(?:\d+|jedan|jednog|dva|dve|tri|četiri|pet|šest|sedam|osam|devet|deset|dvanaest|petnaest|dvadeset|trideset|pedeset|sto|\p{L}*(?:desetak|naestak|stotinak|setak))`
const COUNT = new RegExp(String.raw`(?<!\p{L})(?:(?:oko|još|samo|više od|do|gotovo|preko|oficir i)\s+)?${NUM}\s+(?:Italijan\p{L}*|Talijan\p{L}*|vojnik\p{L}*|četnik\p{L}*|ustaš\p{L}*|oružnik\p{L}*|domobran\p{L}*|žandar\p{L}*|milicion\p{L}*|satnij\p{L}*|Nem(?:aca|ca|ac)|nemačk\p{L}*\s+tenk\p{L}*|tenk\p{L}*|bor(?:aca|ca)|ljudi|Kordunaša|zarobljen\p{L}*|mrtvih|ranjen\p{L}*|poginul\p{L}*|Ital\.)`, 'gu')
const GROUP = /(?<!\p{L})(?:\p{L}+orica|dvojica|trojica)(?!\p{L})/gu
const COMPANY = /(?<!\p{L})(?:Prv|Drug|Treć|Četvrt)(?:a|e|oj|u)\s+čet(?:a|e|i|u|om)(?:\s+(?:Prvog|Drugog|Trećeg|Četvrtog|kordunaškog|banijskog)\s+bataljona)?|(?<!\p{L})(?:Prv|Drug|Treć|Četvrt)(?:i|og|om|u)\s+vod\p{L}*/giu

function marked(text: string, foe: Force): ReactNode[] {
  type Hit = { a: number; b: number; node: (t: string, key: number) => ReactNode }
  const hits: Hit[] = []
  for (const m of text.matchAll(COUNT)) {
    const t = m[0]
    const side = /zarobljen|mrtvih|ranjen|poginul/i.test(t) ? 'n' : /bor(aca|ca)|ljudi|Kordunaša/.test(t) ? 'own' : forceOf(t) ?? foe
    hits.push({ a: m.index!, b: m.index! + t.length, node: (x, k) => <span key={k} className={styles.force} data-f={side}>{x}</span> })
  }
  for (const m of text.matchAll(GROUP)) {
    hits.push({ a: m.index!, b: m.index! + m[0].length, node: (x, k) => <span key={k} className={styles.force} data-f="n">{x}</span> })
  }
  for (const m of text.matchAll(COMPANY)) {
    hits.push({ a: m.index!, b: m.index! + m[0].length, node: (x, k) => <span key={k} className={styles.force} data-f="own">{x}</span> })
  }
  // the longest first where two overlap, then in reading order
  hits.sort((x, y) => x.a - y.a || (y.b - y.a) - (x.b - x.a))
  const out: ReactNode[] = []
  let at = 0, key = 0
  for (const h of hits) {
    if (h.a < at) continue
    if (h.a > at) out.push(text.slice(at, h.a))
    out.push(h.node(text.slice(h.a, h.b), key++))
    at = h.b
  }
  if (at < text.length) out.push(text.slice(at))
  return out
}

// ---------- the card ----------

const pdfPage = (book: number) => book + SOURCE.pdfOffset - SOURCE.missing.filter((p) => p < book).length

function People({ list, label }: { list: Episode['fallen']; label: string }) {
  if (!list?.length) return null
  return (
    <div className={styles.fact}>
      <p className={styles.factLabel}>{label}</p>
      <ul className={styles.people}>
        {list.map(p => {
          const [surname, ...given] = p.name.split(' ')
          const name = <><b>{surname}</b> {given.join(' ')}</>
          return (
            <li key={p.name}>
              {p.id ? <a href={`${SOURCE.unitPath}?borac=${p.id}`} target="_blank" rel="noopener" className={styles.person}>{name}</a>
                : <span className={styles.personPlain}>{name}</span>}
              {p.note && <span className={styles.personNote}>{p.note}</span>}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// The book's own words in a step, set in its italic: a quotation, three words or more with one in small letters
// („temeljito tako da se saobraćaj …“); a unit's name in quotes („Pekiša Vuksan“, „Genova cavalleria“) stays as it is
const QUOTE = /„[^„“]+“/g
const isQuotation = (q: string) => q.split(/\s+/).length >= 3 && /(?:^|\s)[„]?\p{Ll}/u.test(q)
function quoted(nodes: ReactNode[]): ReactNode[] {
  return nodes.flatMap((n, i) => {
    if (typeof n !== 'string') return [n]
    const out: ReactNode[] = []
    let at = 0
    for (const m of n.matchAll(QUOTE)) {
      if (!isQuotation(m[0])) continue
      if (m.index! > at) out.push(n.slice(at, m.index))
      out.push(<span key={`q${i}-${m.index}`} className={styles.quote}>{m[0]}</span>)
      at = m.index! + m[0].length
    }
    if (at < n.length) out.push(n.slice(at))
    return out
  })
}

// a step's button: its hour as printed, else the book's word for when (cut short by the row, whole on hover)
const stepLabel = (s: Step) => s.time ?? s.when ?? ''

function Card({ ep, e, si, go }: { ep: Episode; e: number; si: number; go: (e: number, s: number) => void }) {
  const flat = STEPS.findIndex(x => x.e === e && x.i === si)
  const prev = STEPS[flat - 1], next = STEPS[flat + 1]
  const [from, to] = ep.pages
  const step = ep.steps[si]
  const last = si === ep.steps.length - 1
  const light = lightOf(ep, si)
  return (
    <article className={styles.card} aria-live="polite">
      {/* first in the card, so the buttons stay where they are as the step's text grows and shrinks */}
      <div className={styles.stepNav}>
        <button type="button" className={styles.navButton} disabled={!prev} onClick={() => prev && go(prev.e, prev.i)}
          title="Strelica ←">‹ Prethodno</button>
        <span className={styles.navCount}>korak {si + 1} od {ep.steps.length}</span>
        <button type="button" className={styles.navButton} disabled={!next} onClick={() => next && go(next.e, next.i)}
          title="Strelica →">{next && next.e !== e ? 'Sledeća borba ›' : 'Sledeće ›'}</button>
      </div>
      <p className={styles.kicker}>{e + 1}. od {EPISODES.length} · {ep.dates}</p>
      <h2 className={styles.title}>{ep.title}</h2>
      {si === 0 && <p className={styles.about}>{quoted(marked(ep.about, ep.foe))}</p>}

      {/* the steps, a faint row to jump by; the step being read is the card's text, its day and hour on the sheet */}
      <ol className={styles.pips} aria-label="Koraci">
        {ep.steps.map((s, i) => (
          <li key={i}>
            <button type="button" className={i === si ? styles.pipOn : styles.pip} aria-current={i === si ? 'step' : undefined}
              onClick={() => go(e, i)} title={`${s.date}${stepLabel(s) ? `, ${stepLabel(s)}` : ''}`}>
              {stepLabel(s) || i + 1}
            </button>
          </li>
        ))}
      </ol>
      <p className={styles.stepBody}>{quoted(marked(step.text, ep.foe))}</p>
      <p className={styles.stepSource}>
        {SOURCE.author}, str. {from}–{to}{' '}
        <a href={`${SOURCE.pdf}#page=${pdfPage(from)}`} target="_blank" rel="noopener">otvori u knjizi</a>
      </p>

      {/* the rest folded, one line each; the outcome and the dead come with the last step, as the episode's end */}
      <div className={styles.rows}>
        {(step.notes?.length || light) ? (
          <details className={styles.row}>
            <summary>Kako je nacrtano</summary>
            <div className={styles.rowBody}>
              {step.notes?.map(x => <p key={x} className={styles.rowNote}>{x}</p>)}
              {light && <p className={styles.rowNote}>{light.why}</p>}
            </div>
          </details>
        ) : null}
        {si > 0 && (
          <details className={styles.row}>
            <summary>O borbi</summary>
            <div className={styles.rowBody}><p className={styles.rowNote}>{quoted(marked(ep.about, ep.foe))}</p></div>
          </details>
        )}
        <details className={styles.row}>
          <summary>Neprijatelj</summary>
          <ul className={styles.factList}>{ep.enemy.map(x => <li key={x}>{marked(x, ep.foe)}</li>)}</ul>
        </details>
        <details className={styles.row}>
          <summary>Naše snage</summary>
          <ul className={styles.factList}>{ep.friends.map(x => <li key={x}>{marked(x, ep.foe)}</li>)}</ul>
        </details>
        {last ? (
          <div className={styles.ending}>
            <div className={styles.fact}>
              <p className={styles.factLabel}>Ishod</p>
              <p className={styles.factText}>{quoted(marked(ep.result, ep.foe))}</p>
            </div>
            <People list={ep.fallen} label="Poginuli iz bataljona" />
            <People list={ep.wounded} label="Ranjeni" />
          </div>
        ) : (
          <p className={styles.rowLater}><span>Ishod i poginuli</span><span>posle poslednjeg koraka</span></p>
        )}
        <details className={styles.row}>
          <summary>Podaci karte</summary>
          <div className={styles.rowBody}>
            <p className={styles.rowNote}>
              {SOURCE.author}, <i>{SOURCE.title}</i>, {SOURCE.place}. Reljef: AWS Terrain Tiles (EU-DEM, Copernicus;
              SRTM). Pruga, ceste, vode i zaseoci: © OpenStreetMap (ODbL). Stanice: GeoNames (CC BY 4.0).
            </p>
          </div>
        </details>
      </div>
    </article>
  )
}

// ---------- the page ----------

export default function Battalion({ initial }: { initial: { epizoda?: string; korak?: string } }) {
  const start = Math.max(0, EPISODES.findIndex(x => x.key === initial.epizoda))
  const [pos, setPos] = useState(() => {
    const s = Math.max(0, Math.min(EPISODES[start].steps.length - 1, Number(initial.korak ?? 1) - 1 || 0))
    return { e: start, s }
  })
  const go = useCallback((e: number, s: number) => setPos({ e, s }), [])
  const ep = EPISODES[pos.e]
  // the regions' ground: this episode's first, then the others in the order the episodes come, one at a time
  const [ground, setGround] = useState<Partial<Record<Region, Terrain>>>({})
  useEffect(() => {
    let live = true
    const order = [ep.region, ...EPISODES.map(x => x.region)].filter((r, i, a) => a.indexOf(r) === i)
    ;(async () => {
      for (const r of order) {
        if (!live) return
        if (ground[r]) continue
        const t = await TERRAIN[r]()
        if (!live) return
        setGround(g => (g[r] ? g : { ...g, [r]: t }))
      }
    })()
    return () => { live = false }
  }, [ep.region])                                 // eslint-disable-line react-hooks/exhaustive-deps
  const terrain = ground[ep.region]
  // for a test of every sheet: window.__bataljonGo(episode, step), both from 0
  useEffect(() => { (window as unknown as { __bataljonGo?: typeof go }).__bataljonGo = go }, [go])

  // the address keeps the step, to come back to it or send it on
  useEffect(() => {
    const url = new URL(window.location.href)
    url.searchParams.set('epizoda', ep.key)
    url.searchParams.set('korak', String(pos.s + 1))
    window.history.replaceState(null, '', url)
  }, [ep.key, pos.s])

  // the arrows step through the steps, from one episode into the next
  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => {
      const t = ev.target as HTMLElement | null
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return
      ev.preventDefault()
      setPos(p => {
        const i = STEPS.findIndex(x => x.e === p.e && x.i === p.s) + (ev.key === 'ArrowRight' ? 1 : -1)
        const x = STEPS[Math.max(0, Math.min(STEPS.length - 1, i))]
        return { e: x.e, s: x.i }
      })
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // where the page fills the screen it ends at the window's foot: the room under the site's header
  const page = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = page.current
    if (!el) return
    const fit = () => {
      const top = el.getBoundingClientRect().top + window.scrollY
      el.style.setProperty('--fill-h', `${Math.max(480, window.innerHeight - top - 12)}px`)
    }
    fit()
    window.addEventListener('resize', fit)
    return () => window.removeEventListener('resize', fit)
  }, [])

  return (
    <div className={styles.page} ref={page}>
      <header className={styles.head}>
        <h1 className={styles.headTitle}>Drugi bataljon „Pekiša Vuksan“</h1>
        <p className={styles.headKicker}>Prva lička proleterska brigada „Marko Orešković“ · šta knjiga o brigadi piše o
          bataljonu, borba po borba · prvi nacrt, jul 1942. – mart 1943.</p>
      </header>
      <Timeline e={pos.e} go={go} />
      <div className={styles.layout}>
        {/* a new region is a new sheet: its own kilometres, its own frame */}
        {terrain ? <Sheet key={ep.region} ep={ep} si={pos.s} t={terrain} /> : (
          <div className={styles.sheetColumn}>
            <div className={`${base.scroller} ${styles.room} ${styles.loading}`}>Karta se učitava…</div>
          </div>
        )}
        <Card ep={ep} e={pos.e} si={pos.s} go={go} />
      </div>
    </div>
  )
}
