'use client'

import { createContext, useContext, useEffect, useMemo, useRef, useState, type MutableRefObject, type ReactNode } from 'react'
import {
  MONTHS, WHOLE, boxOf, day, fit, monthEnd, monthIndex, monthStart, placeNumbers, sampleRoute, toSheet, yearOf,
  type Pt, type Sample, type View, type Year, YEARS,
} from './geometry'
import { SHEET } from './map1941'
import { project } from './projection'
import { EVENT_R } from './units'
import { UNIT_ROUTES, type UnitRoute, type Waypoint } from './units'

// What the map page shows, kept in its address so a link can open it as it was (and a soldier's record can open
// his unit's way with the place he was killed marked). Kroz vreme is the page's own view, Ratni put is asked for:
//   ?jedinica=prva-licka&mesec=1943-06&cela=1&mesto=18.55,43.37&oznaka=Ime Prezime
//   ?prikaz=put&godina=1943

export type Variant = 'put' | 'vreme'

// The occupiers' colours: each zone is its power's colour at a low strength, a grey with a tinge of it. While they
// are being tried out (the panel under the map) they are kept in this browser
export type Power = 'de' | 'it' | 'hu' | 'bg' | 'al'
export const POWERS: { key: Power; name: string }[] = [
  { key: 'de', name: 'Nemačka' }, { key: 'it', name: 'Italija' }, { key: 'hu', name: 'Mađarska' },
  { key: 'bg', name: 'Bugarska' }, { key: 'al', name: 'Albanija (pripojeno)' },
]
export const DEFAULT_COLORS: Record<Power, string> = { de: '#1c1a18', it: '#2c5a37', hu: '#6c7a24', bg: '#6e4a2a', al: '#2f5b62' }
const COLOR_STORE = 'mapa-boje'
export type Marker = { x: number; y: number; label: string }

export type Initial = {
  unit?: string; view?: string; year?: string; month?: string
  whole?: boolean; place?: string; label?: string
}

// A unit with what the map draws from it: its numbered events, its route as a line, its months in the war
export type Unit = UnitRoute & { labelled: Waypoint[]; samples: Sample[]; first: number; last: number }
const derived = new Map<string, Unit>()
export function unitOf(key: string): Unit {
  let u = derived.get(key)
  if (!u) {
    const r = UNIT_ROUTES.find(x => x.key === key) ?? UNIT_ROUTES[0]
    u = {
      ...r,
      labelled: r.ROUTE.filter(w => w.label),
      samples: sampleRoute(r.ROUTE),
      first: Math.max(0, monthIndex(day(r.ROUTE[0].date))),
      last: Math.min(MONTHS.length - 1, monthIndex(day(r.ROUTE[r.ROUTE.length - 1].date))),
    }
    derived.set(key, u)
  }
  return u
}

type State = {
  unit: Unit; setUnit: (key: string) => void
  variant: Variant; setVariant: (v: Variant) => void
  year: Year | null; setYear: (y: Year | null) => void
  month: number; setMonth: (m: number | ((m: number) => number)) => void
  playing: boolean; setPlaying: (p: boolean) => void
  open: number | null; setOpen: (i: number | null) => void
  battle: string | null; setBattle: (key: string | null) => void   // a great battle's card (battles.ts)
  fight: number | null; setFight: (i: number | null) => void       // a fight's card, by its place in ROUTE
  partition: boolean                                  // the borders after the April war: always, for now
  whole: boolean; setWhole: (w: boolean) => void
  colors: Record<Power, string>; setColor: (p: Power, c: string) => void
  toneScale: number; setToneScale: (k: number) => void
  resetColors: () => void
  marker: Marker | null
  view: View                                         // the frame as drawn this moment (moving toward `target`)
  manual: View | null                                // a frame the reader zoomed or moved to (Shift and the wheel, a drag)
  setManual: (v: View | null) => void
  numbers: Pt[]                                       // where each numbered event sits on the sheet
}

const Ctx = createContext<State | null>(null)
export const useMap = () => {
  const s = useContext(Ctx)
  if (!s) throw new Error('map: no provider')
  return s
}

// The area a view should frame: the whole route, one year of it, or on the timeline the last months around the
// brigade, so the sheet follows it as the months go by
function targetView(unit: Unit, variant: Variant, year: Year | null, month: number, whole: boolean, marker: Marker | null): View {
  if (whole) return WHOLE
  let pts: Pt[] = unit.samples
  if (variant === 'put' && year) pts = unit.samples.filter(s => yearOf(s.t) === year)
  if (variant === 'vreme') {
    const from = monthStart(MONTHS[Math.max(unit.first, month - 4)]), to = monthEnd(MONTHS[month])
    const recent = unit.samples.filter(s => s.t >= from && s.t <= to)
    const before = unit.samples.filter(s => s.t <= to)
    pts = recent.length ? recent : before.slice(-1)
  }
  if (marker) pts = [...pts, marker]
  const box = boxOf(pts)
  return box ? fit(box, variant === 'vreme' ? 260 : 230) : WHOLE
}

// The frame moves to its new place in a short ease, or jumps there for readers who asked for less motion and while
// the reader zooms or drags it (`jump`)
function useAnimatedView(target: View, jump: MutableRefObject<boolean>): View {
  const [view, setView] = useState(target)
  const from = useRef(target)
  const shown = useRef(target)
  useEffect(() => {
    const reduce = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const a = shown.current
    if (reduce || jump.current || (Math.abs(a.cx - target.cx) < 0.5 && Math.abs(a.cy - target.cy) < 0.5 && Math.abs(a.z - target.z) < 0.01)) {
      jump.current = false
      shown.current = target
      setView(target)
      return
    }
    from.current = a
    const start = performance.now(), duration = 650
    let raf = 0
    const step = (now: number) => {
      const k = Math.min(1, (now - start) / duration)
      const e = 1 - Math.pow(1 - k, 3)
      // the zoom eases on a log scale, so enlarging and reducing feel alike
      const z = Math.exp(Math.log(from.current.z) + (Math.log(target.z) - Math.log(from.current.z)) * e)
      const v = { cx: from.current.cx + (target.cx - from.current.cx) * e, cy: from.current.cy + (target.cy - from.current.cy) * e, z }
      shown.current = v
      setView(v)
      if (k < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target.cx, target.cy, target.z])               // eslint-disable-line react-hooks/exhaustive-deps
  return view
}

export function MapProvider({ initial, children }: { initial: Initial; children: ReactNode }) {
  const [unitKey, setUnitKey] = useState(UNIT_ROUTES.some(u => u.key === initial.unit) ? initial.unit! : UNIT_ROUTES[0].key)
  const unit = unitOf(unitKey)
  const [variant, setVariantState] = useState<Variant>(initial.view === 'put' ? 'put' : 'vreme')
  const [year, setYear] = useState<Year | null>((YEARS as readonly string[]).includes(initial.year ?? '') ? (initial.year as Year) : null)
  // the timeline starts where the unit does
  const startMonth = initial.month && MONTHS.includes(initial.month) ? MONTHS.indexOf(initial.month) : unit.first
  const [month, setMonth] = useState(Math.min(unit.last, Math.max(unit.first, startMonth)))
  const [playing, setPlaying] = useState(false)
  const [open, setOpen] = useState<number | null>(null)
  const [battle, setBattle] = useState<string | null>(null)
  const [fight, setFight] = useState<number | null>(null)
  const partition = true
  const [colors, setColors] = useState<Record<Power, string>>(DEFAULT_COLORS)
  const [toneScale, setToneScale] = useState(1)
  // the colours tried before, from this browser
  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem(COLOR_STORE) ?? 'null')
      if (saved?.colors) setColors({ ...DEFAULT_COLORS, ...saved.colors })
      if (typeof saved?.scale === 'number') setToneScale(saved.scale)
    } catch { /* the defaults */ }
  }, [])
  const keepColors = (c: Record<Power, string>, k: number) => {
    try { window.localStorage.setItem(COLOR_STORE, JSON.stringify({ colors: c, scale: k })) } catch { /* not kept */ }
  }
  const [manual, setManualState] = useState<View | null>(null)
  const jump = useRef(false)
  const [whole, setWhole] = useState(!!initial.whole)

  const marker = useMemo<Marker | null>(() => {
    const m = initial.place?.match(/^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/)
    if (!m) return null
    const [x, y] = project(Number(m[1]), Number(m[2]))
    return { x, y, label: initial.label ?? '' }
  }, [initial.place, initial.label])

  // the timeline plays a month every 1.8 s, time to read the month and see where the brigade went
  useEffect(() => {
    if (!playing) return
    const id = setInterval(() => {
      setMonth(m => {
        if (m >= unit.last) {
          setPlaying(false)
          return m
        }
        return m + 1
      })
    }, 1800)
    return () => clearInterval(id)
  }, [playing, unit.last])

  // on the timeline the arrow keys step through the months (not while a field or a menu has the keys)
  useEffect(() => {
    if (variant !== 'vreme') return
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return
      const t = e.target
      if (t instanceof HTMLElement && (t.isContentEditable || t.closest('input, textarea, select'))) return
      const step = e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : 0
      if (!step) return
      e.preventDefault()
      setPlaying(false)
      setMonth(m => Math.min(unit.last, Math.max(unit.first, m + step)))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [variant, unit.first, unit.last])

  // A frame the reader zoomed keeps its zoom as the months go by, but follows the brigade: when the month's road (or
  // where the brigade stands at its end) leaves the frame, the frame glides over to it
  const manualRef = useRef(manual)
  manualRef.current = manual
  useEffect(() => {
    const m = manualRef.current
    if (!m || variant !== 'vreme') return
    const to = monthEnd(MONTHS[month]), from = monthStart(MONTHS[month])
    const walked = unit.samples.filter(s => s.t <= to)
    const box = boxOf([...walked.filter(s => s.t >= from), ...walked.slice(-1)])
    if (!box) return
    const { width: W, height: H } = SHEET
    const hw = W / (2 * m.z), hh = H / (2 * m.z)
    // a margin inside the frame, so the road doesn't run along its edge
    const mx = hw * 0.15, my = hh * 0.15
    const seen = (x0: number, y0: number, x1: number, y1: number) =>
      x0 >= m.cx - hw + mx && x1 <= m.cx + hw - mx && y0 >= m.cy - hh + my && y1 <= m.cy + hh - my
    // the whole month's road if it fits the frame, else where the brigade ends the month
    const fits = box[2] - box[0] <= 2 * (hw - mx) && box[3] - box[1] <= 2 * (hh - my)
    const end = walked[walked.length - 1]
    if (fits ? seen(box[0], box[1], box[2], box[3]) : seen(end.x, end.y, end.x, end.y)) return
    const cx = Math.min(W - hw, Math.max(hw, fits ? (box[0] + box[2]) / 2 : end.x))
    const cy = Math.min(H - hh, Math.max(hh, fits ? (box[1] + box[3]) / 2 : end.y))
    setManualState({ z: m.z, cx, cy })                // no jump: the frame eases over
  }, [month, unit, variant])

  // close a card with Escape
  useEffect(() => {
    if (open === null && battle === null && fight === null) return
    const close = (e: KeyboardEvent) => { if (e.key === 'Escape') { setOpen(null); setBattle(null); setFight(null) } }
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [open, battle, fight])

  // keep the address in step, without a new history entry for every month
  useEffect(() => {
    const q = new URLSearchParams()
    if (unit.key !== UNIT_ROUTES[0].key) q.set('jedinica', unit.key)
    if (variant === 'vreme') q.set('mesec', MONTHS[month])
    else q.set('prikaz', 'put')
    if (variant === 'put' && year) q.set('godina', year)
    if (whole) q.set('cela', '1')
    if (initial.place) q.set('mesto', initial.place)
    if (initial.label) q.set('oznaka', initial.label)
    const url = `${window.location.pathname}${q.size ? `?${q}` : ''}`
    if (url !== `${window.location.pathname}${window.location.search}`) window.history.replaceState(null, '', url)
  }, [unit.key, variant, year, month, whole, initial.place, initial.label])

  const auto = useMemo(() => targetView(unit, variant, year, month, whole, marker),
    [unit, variant, year, month, whole, marker])
  // the reader's own frame wins until it is let go, or the unit, the view, the year or the whole country is asked for
  const target = manual ?? auto
  const view = useAnimatedView(target, jump)

  // the numbered events on the sheet, pushed apart there (they keep their size as the map is enlarged)
  const numbers = useMemo(() => placeNumbers(unit.labelled.map(toSheet(view)), EVENT_R + 0.6), [unit, view])

  const value: State = {
    unit,
    setUnit: key => {
      const u = unitOf(key)
      setUnitKey(key); setOpen(null); setBattle(null); setFight(null); setPlaying(false); setYear(null); setManualState(null)
      setMonth(m => Math.min(u.last, Math.max(u.first, m)))
    },
    variant, setVariant: v => { setVariantState(v); setPlaying(false); setOpen(null); setBattle(null); setFight(null); setManualState(null) },
    year, setYear: y => { setYear(y); setOpen(null); setManualState(null) },
    month, setMonth, playing, setPlaying, partition,
    // one card at a time: an event's, a great battle's or a fight's
    open, setOpen: i => { setOpen(i); if (i !== null) { setBattle(null); setFight(null) } },
    battle, setBattle: k => { setBattle(k); if (k !== null) { setOpen(null); setFight(null) } },
    fight, setFight: i => { setFight(i); if (i !== null) { setOpen(null); setBattle(null) } },
    whole, setWhole: w => { setWhole(w); setManualState(null) },
    colors, setColor: (p, c) => { const next = { ...colors, [p]: c }; setColors(next); keepColors(next, toneScale) },
    toneScale, setToneScale: k => { setToneScale(k); keepColors(colors, k) },
    resetColors: () => { setColors(DEFAULT_COLORS); setToneScale(1); keepColors(DEFAULT_COLORS, 1) },
    marker, view, numbers, manual,
    setManual: v => { jump.current = v !== null; setManualState(v) },
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
