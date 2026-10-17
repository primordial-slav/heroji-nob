'use client'

import { memo, useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { CloseIcon } from '@/app/components/Icons'
import { formatNumber, plural } from '@/app/i18n/format'
import styles from './mapa.module.css'
import {
  DETAIL_TOWNS, GAINED, LAKE_LINES, LAKES, LAND, LETTER_SPACING, NEIGHBOURS, RIVER_LINES, RIVERS, SEA, SHEET, TOWNS,
} from './map1941'
import {
  BANAT_LINES, NDH_LABELS, NDH_LINES, PERIODS, ZONE_LABELS, ZONES, type Period, type Zone,
} from './partition1941'
import {
  DASH, MONTHS, MONTHS_IN, WHOLE, arrowsOf, day, fade, monthEnd, monthIndex, monthName, monthStart, pathOf, toSheet, yearOf,
  type Pt, type View, type Year,
} from './geometry'
import { KilledLink } from './KilledLink'
import { useMap, type Unit } from './state'
import { EVENT_R, killedPath } from './units'
import { BATTLES, type Battle } from './battles'
import { LIBERATED, type Liberated } from './liberated1941'
import { project } from './projection'

const { width: W, height: H } = SHEET
const FRAME = 10                                    // the frame's outer line, in from the sheet's edge
const INNER = 14                                    // its inner line
const RIVER_LINES_FROM = 1.3                        // enlarged past this, rivers are drawn as plain lines
const MINOR_FROM = 1.8                              // and the smaller rivers join them
const RANK2_FROM = 1.35, RANK3_FROM = 2.0           // when the towns of rank 2 and 3 come in

const num = (n: number) => formatNumber('sr', n)
const borci = (n: number) => `${num(n)} ${plural('sr', n, { one: 'borac', few: 'borca', other: 'boraca' })}`

type Box = [number, number, number, number]

// How far the reader may enlarge the map, and a frame kept on the sheet: no further out than the whole country
const ZOOM_MOST = 12
function held(v: View): View {
  if (v.z <= 1.001) return WHOLE
  const hw = W / (2 * v.z), hh = H / (2 * v.z)
  return { z: v.z, cx: Math.min(W - hw, Math.max(hw, v.cx)), cy: Math.min(H - hh, Math.max(hh, v.cy)) }
}
const overlaps = (a: Box, b: Box) => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3]

// ---------- the country, drawn once and moved and enlarged as a whole ----------

// Each occupier's zone gets its own pen hatching, as one-colour plates tell them apart; the spacing is held on the
// sheet as the map is enlarged
function Hatches({ z }: { z: number }) {
  const s = `scale(${(1 / z).toFixed(4)})`
  return (
    <g className={styles.hatch}>
      <pattern id="hatch-nemacka" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform={`${s} rotate(45)`}><line x1="0.4" y1="0" x2="0.4" y2="3.4" /></pattern>
      <pattern id="hatch-italija" width="3.6" height="3.6" patternUnits="userSpaceOnUse" patternTransform={s}><line x1="0" y1="0.4" x2="3.6" y2="0.4" /></pattern>
      <pattern id="hatch-madjarska" width="3.6" height="3.6" patternUnits="userSpaceOnUse" patternTransform={s}><line x1="0.4" y1="0" x2="0.4" y2="3.6" /></pattern>
      <pattern id="hatch-bugarska" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform={`${s} rotate(45)`}><line x1="0.4" y1="0" x2="0.4" y2="5" /><line x1="0" y1="0.4" x2="5" y2="0.4" /></pattern>
      <pattern id="hatch-albanija" width="3.8" height="3.8" patternUnits="userSpaceOnUse" patternTransform={s}><circle cx="1.9" cy="1.9" r="0.6" /></pattern>
      <pattern id="hatch-crnagora" width="6.5" height="6.5" patternUnits="userSpaceOnUse" patternTransform={`${s} rotate(-45)`}><line x1="0.4" y1="0" x2="0.4" y2="6.5" /></pattern>
    </g>
  )
}
// a zone's colour: its power's tint (set on the plate, lighter in the dark theme), the ink where none is named
const tint = (power: string | null) => (power ? `var(--tint-${power}, var(--ink))` : 'var(--ink)')

// The country divided as it stood in a month (partition1941.ts): the period that month falls in
const ZONE_BY_KEY = new Map(ZONES.map(z => [z.key, z]))
const zonesIn = (period: Period): Zone[] => period.zones.map(k => ZONE_BY_KEY.get(k)).filter((z): z is Zone => Boolean(z))
export const periodAt = (ym: string): Period => PERIODS.find(p => p.from <= ym && ym <= p.to) ?? PERIODS[0]
// the liberated territory as the VII's history maps it (liberated1941.ts), in the months each of its maps covers
export const freeAt = (ym: string): Liberated | null => LIBERATED.find(l => l.from <= ym && ym <= l.to) ?? null
// on the war path, the year chosen is shown as it stood in its middle; the whole war as it was divided in 1941
const YEAR_MONTH: Record<string, string> = { '1941–42': '1942-06', '1943': '1943-06', '1944': '1944-06', '1945': '1945-02' }
// a war-path year's first and last day, in the days `day` counts ('1941–42' is both years)
const yearStart = (y: Year) => Date.UTC(y === '1941–42' ? 1941 : +y, 0, 1) / 864e5
const yearEnd = (y: Year) => Date.UTC(y === '1941–42' ? 1942 : +y, 11, 31) / 864e5

// Each zone the grey of who held it (German darker, Italian lighter, a zone inside a state a shade over its state's),
// its hatching on top where it was annexed; the NDH, a state in name, keeps the paper's white
const Country = memo(function Country({ period, free, lines, minor, scale }: {
  period: Period | null; free: Liberated | null; lines: boolean; minor: boolean; scale: number
}) {
  const zones = period ? zonesIn(period) : []
  return (
    <>
      {period && (
        <>
          {zones.filter(z => z.tone > 0).map(z => (
            <path key={z.key} d={z.d} className={styles.tone} style={{ fill: tint(z.power), fillOpacity: Math.min(1, z.tone * scale) }} />
          ))}
          <g className={styles.zones}>
            {zones.filter(z => z.hatch).map(z => <path key={z.key} d={z.d} fill={`url(#hatch-${z.hatch})`} />)}
          </g>
        </>
      )}
      {/* the liberated territory, a wash of the Partisan red over the occupiers' greys; the semi-liberated hatched */}
      {free && (
        <>
          <path d={free.semi} className={styles.semiFree} fill="url(#hatch-free)" />
          <path d={free.liberated} className={styles.free} />
        </>
      )}
      {lines ? (
        <g className={styles.riverLines}>
          {RIVER_LINES.filter(r => minor || r.kind !== 'minor').map((r, i) => <path key={i} d={r.d} className={styles[r.kind]} />)}
        </g>
      ) : (
        <g className={styles.rivers}>{RIVERS.map((r, i) => <path key={i} d={r.d} />)}</g>
      )}
      <g className={styles.lakes}>{LAKES.map((d, i) => <path key={i} d={d} />)}</g>
      <g className={styles.lakeLines}>{LAKE_LINES.map((d, i) => <path key={i} d={d} />)}</g>
      {/* the land Yugoslavia gained after the war, Italy's then: only a faint outline, its border with Italy dashed */}
      <g className={styles.gained}>
        {GAINED.coast.map((d, i) => <path key={`c${i}`} d={d} />)}
        {GAINED.border.map((d, i) => <path key={`b${i}`} d={d} className={styles.gainedBorder} />)}
      </g>
      <g className={styles.land}>{LAND.map((d, i) => <path key={i} d={d} />)}</g>
      {period && (
        <>
          {period.banat && <g className={styles.banatLines}>{BANAT_LINES.map((d, i) => <path key={i} d={d} />)}</g>}
          <g className={styles.zoneLines}>{period.lines.map((d, i) => <path key={i} d={d} />)}</g>
          {period.ndh && (
            <>
              {NDH_LINES.zone_variant.map((d, i) => <path key={`v${i}`} d={d} className={styles.variantLine} />)}
              {NDH_LINES.zone_ii_iii.map((d, i) => <path key={`z${i}`} d={d} className={styles.zoneIILine} />)}
              {NDH_LINES.demarcation.map((d, i) => (
                <g key={`d${i}`}>
                  <path d={d} className={styles.demarcationTicks} />
                  <path d={d} className={styles.demarcationLine} />
                </g>
              ))}
            </>
          )}
        </>
      )}
    </>
  )
})

// Lettering that belongs to the ground (the sea, the neighbours, the new states), set inside the enlarged group at a
// size divided by the zoom, so it reads the same at every scale
function GroundLettering({ z, period }: { z: number; period: Period | null }) {
  return (
    <g className={styles.lettering}>
      <text className={styles.sea} fontSize={12.5 / z} letterSpacing={`${LETTER_SPACING.sea}em`}>
        <textPath href="#map-sea" startOffset="50%" textAnchor="middle">{SEA.name}</textPath>
      </text>
      {NEIGHBOURS.map(n => (
        <text key={n.name} className={styles.neighbour} fontSize={11 / z} textAnchor="middle" letterSpacing={`${LETTER_SPACING.neighbour}em`}
          transform={`translate(${n.x} ${n.y}) rotate(${n.rotate})`}>{n.name}</text>
      ))}
      {period?.ndh && NDH_LABELS.map(l => (
        <text key={l.name} className={styles.ndhZoneName} fontSize={8.5 / z} textAnchor="middle" letterSpacing="0.25em"
          transform={`translate(${l.x} ${l.y}) rotate(${l.rotate})`}>{l.name}</text>
      ))}
      {period && ZONE_LABELS.filter(l => l.zones.some(k => period.zones.includes(k))).map(l => (
        <g key={l.name} transform={`translate(${l.x} ${l.y}) rotate(${l.rotate})`}>
          <text className={styles.zoneName} fontSize={l.size / z} textAnchor="middle" letterSpacing="0.35em">{l.name}</text>
          {/* what the name was then, smaller under it */}
          {l.under && <text className={styles.zoneUnder} y={(l.size * 1.05) / z} fontSize={(l.size * 0.62) / z} textAnchor="middle"
            letterSpacing="0.08em">{l.under}</text>}
        </g>
      ))}
    </g>
  )
}

// ---------- towns, on the sheet ----------

// The ten towns of the overview always, then as the map closes in the rank-2 and rank-3 towns, each named only
// where its name finds room (a book's detail sheet names more places than its overview, not bigger ones)
// The towns and their names, culled where they would collide; with the boxes their names took, which the battle
// labels keep off
// the overview's towns on the sheet, drawn whatever else is there, each with the box its name takes
function mainTowns(view: View) {
  const T = toSheet(view)
  return TOWNS.map(t => ({ t, p: T(t) }))
    .filter(({ p }) => p.x >= INNER && p.x <= W - INNER && p.y >= INNER && p.y <= H - INNER)
    .map(({ t, p }) => {
      const x1 = t.underline[0] - t.x + p.x, x2 = t.underline[1] - t.x + p.x, dy = t.ly - t.y
      return { t, p, x1, x2, box: [x1 - 1, p.y + dy - t.size, x2 + 1, p.y + dy + 3] as Box }
    })
}

function placeTowns(view: View, keepClear: Box[]): { nodes: ReactNode[]; boxes: Box[]; names: Set<string> } {
  const T = toSheet(view)
  const placed: Box[] = [...keepClear]
  const out: ReactNode[] = []
  const names = new Set<string>()
  for (const { t, p, x1, x2, box } of mainTowns(view)) {
    const dx = t.lx - t.x, dy = t.ly - t.y
    placed.push(box)
    names.add(t.name.toLowerCase())
    out.push(
      <g key={t.name}>
        {t.rank === 0 ? (
          <>
            <rect x={p.x - 4} y={p.y - 4} width={8} height={8} className={styles.markOpen} />
            <rect x={p.x - 2} y={p.y - 2} width={4} height={4} className={styles.markFull} />
          </>
        ) : <rect x={p.x - 2.3} y={p.y - 2.3} width={4.6} height={4.6} className={styles.markFull} />}
        <text x={p.x + dx} y={p.y + dy} fontSize={t.size} textAnchor={t.anchor} className={styles.halo}>{t.name.toUpperCase()}</text>
        <text x={p.x + dx} y={p.y + dy} fontSize={t.size} textAnchor={t.anchor}>{t.name.toUpperCase()}</text>
        <line x1={x1} x2={x2} y1={p.y + dy + 2.4} y2={p.y + dy + 2.4} className={styles.underline} />
      </g>,
    )
  }
  for (const t of DETAIL_TOWNS) {
    if ((t.rank === 2 && view.z < RANK2_FROM) || (t.rank === 3 && view.z < RANK3_FROM)) continue
    const p = T(t)
    if (p.x < INNER + 6 || p.x > W - INNER - 6 || p.y < INNER + 10 || p.y > H - INNER - 6) continue
    // a size up from the generator's, to be read on a screen
    const size = t.size + 1.5, tw = (t.w * size) / t.size
    const h = size * 0.75
    const east: Box = [p.x + 3.5, p.y - h / 2 - 1, p.x + 4.5 + tw, p.y + h / 2 + 1]
    const west: Box = [p.x - 4.5 - tw, p.y - h / 2 - 1, p.x - 3.5, p.y + h / 2 + 1]
    const mark: Box = [p.x - 2.6, p.y - 2.6, p.x + 2.6, p.y + 2.6]
    if (placed.some(b => overlaps(b, mark))) continue
    const side = !placed.some(b => overlaps(b, east)) ? 'e' : !placed.some(b => overlaps(b, west)) ? 'w' : null
    if (!side) continue
    placed.push(mark, side === 'e' ? east : west)
    names.add(t.name.toLowerCase())
    const x = side === 'e' ? p.x + 4 : p.x - 4
    out.push(
      <g key={t.name} className={styles.detailTown}>
        <circle cx={p.x} cy={p.y} r={2} className={styles.markOpen} />
        <circle cx={p.x} cy={p.y} r={0.7} className={styles.markFull} />
        <text x={x} y={p.y + h / 2} fontSize={size} textAnchor={side === 'e' ? 'start' : 'end'} className={styles.halo}>{t.name}</text>
        <text x={x} y={p.y + h / 2} fontSize={size} textAnchor={side === 'e' ? 'start' : 'end'}>{t.name}</text>
      </g>,
    )
  }
  return { nodes: out, boxes: placed.slice(keepClear.length), names }
}

// ---------- the unit, in red over the black plate ----------

function Arrows({ pts }: { pts: Pt[] }) {
  return (
    <g className={styles.routeArrow}>
      {arrowsOf(pts).map((a, i) => (
        <path key={i} d="M3 0L-5 -3.4L-3.4 0L-5 3.4Z" transform={`translate(${a.x.toFixed(1)} ${a.y.toFixed(1)}) rotate(${a.a.toFixed(0)})`} />
      ))}
    </g>
  )
}

function EventNumbers({ upTo, year }: { upTo?: number; year?: Year | null }) {
  const { unit, numbers, open, setOpen, view, month, variant } = useMap()
  const T = toSheet(view)
  return (
    <>
      {unit.labelled.map((w, i) => {
        if (upTo !== undefined && day(w.date) > upTo) return null
        const p = numbers[i], at = T(w)
        const moved = Math.hypot(p.x - at.x, p.y - at.y) > 3
        const toggle = () => setOpen(open === i ? null : i)
        // events of other years, or long past on the timeline, step back but stay clickable
        let opacity = 1
        if (year && yearOf(day(w.date)) !== year) opacity = 0.3
        if (variant === 'vreme') opacity = Math.max(0.3, fade(month - monthIndex(day(w.date))))
        if (open === i) opacity = 1
        return (
          <g key={i} role="button" tabIndex={0} aria-label={`${i + 1}. ${w.label}`} aria-expanded={open === i}
            className={styles.eventHit} onClick={toggle} style={{ opacity }}
            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle() } }}>
            {moved && <line x1={at.x} y1={at.y} x2={p.x} y2={p.y} className={styles.leader} />}
            <circle cx={p.x} cy={p.y} r={EVENT_R} className={open === i ? styles.eventMarkOn : styles.eventMark} />
            <text x={p.x} y={p.y + 4} className={open === i ? styles.eventNumberOn : styles.eventNumber}>{i + 1}</text>
          </g>
        )
      })}
    </>
  )
}

// Crossed sabres, the maps' sign for a battle, centred on 0,0
function Sabres() {
  return (
    <>
      <path d="M-6.5 6.5L6 -6M-5.4 2.9L-2.9 5.4M6.5 6.5L-6 -6M2.9 5.4L5.4 2.9" />
      <circle cx={-6.6} cy={6.6} r={0.9} />
      <circle cx={6.6} cy={6.6} r={0.9} />
    </>
  )
}

// The war's great battles the unit fought in (battles.ts): the sabres at the place the battle is named for, in ink
// (the red is the brigade's own). Its name and dates stand off to one side, with a fine leader back to the sabres.
// On the timeline they are the month's; on the war path all of them, another year's stepping back to its sabres
// alone. The labels are set before the villages: a village's name gives way to a battle's, the overview's towns
// (always drawn) and the title block do not
type ShownBattle = Battle & { dim?: boolean }
type BattleLabel = {
  b: ShownBattle; p: Pt; stepped: boolean
  lx: number; ly: number; w: number; h: number; ex: number; ey: number; ux: number; uy: number
  covered: boolean; sx: number; sy: number; box: Box | null
}

// The battles a sheet shows, and what their labels keep off: the brigade's line (on the timeline as walked so far,
// on the war path the year's or all of it) and its event numbers
function battlesFor(unit: Unit, variant: 'put' | 'vreme', month: number, year: Year | null, view: View, numbers: Pt[]) {
  const T = toSheet(view)
  if (variant === 'vreme') {
    const ym = MONTHS[month], now = monthEnd(ym)
    return {
      list: bigBattlesOn(unit, month) as ShownBattle[],
      busy: [...unit.samples.filter(s => s.t <= now).map(T), ...numbers],
    }
  }
  return {
    list: BATTLES.filter(b => unit.battles.includes(b.key))
      .map(b => ({ ...b, dim: !!year && yearOf(day(b.from)) !== year && yearOf(day(b.to)) !== year })),
    busy: [...unit.samples.filter(s => !year || yearOf(s.t) === year).map(T), ...numbers],
  }
}

// Where each battle's label goes: of the places on either side of the sabres, and straight above and below, the
// emptiest. The brigade's line and the killed count by the room they take (8-unit cells, so a war path that crosses
// a place many times over weighs as the area it covers, not as its thousands of points); an event number far more,
// and a town's name (of the overview's, which are always drawn) above all; a place further off pays a little
function placeBattles(list: ShownBattle[], open: string | null, view: View, numbers: Pt[], busy: Pt[], avoid: Box[]): BattleLabel[] {
  const T = toSheet(view)
  const placed: Box[] = []                          // labels already set, which the next keeps off
  return list.map(b => {
    const [x, y] = project(b.lon, b.lat)
    const p = T({ x, y })
    const stepped = !!b.dim && open !== b.key
    const name = b.name.toUpperCase()
    const w = Math.max(name.length * 14.5 * 0.62 * 1.16, b.dates.length * 10 * 0.5)
    const h = 32
    if (stepped) return { b, p, stepped, lx: p.x, ly: p.y, w, h, ex: p.x, ey: p.y, ux: 0, uy: 0, covered: false, sx: p.x, sy: p.y, box: null }
    const near = [-44, 30, -h / 2], far = [-78, 62], farther = [-112, 96]
    const spots = [...near.map(dy => ({ dy, far: 0 })), ...far.map(dy => ({ dy, far: 1 })), ...farther.map(dy => ({ dy, far: 2 }))]
      .flatMap(({ dy, far: f }) => [{ dx: 34, dy, f }, { dx: -34 - w, dy, f }, { dx: 94, dy, f: f + 1 }, { dx: -94 - w, dy, f: f + 1 }])
      .concat([[-h - 22, 0.5], [24, 0.5], [-h - 56, 1.5], [58, 1.5]].map(([dy, f]) => ({ dx: -w / 2, dy, f })))
      .map(o => {
        const box: Box = [p.x + o.dx - 4, p.y + o.dy - 4, p.x + o.dx + w + 4, p.y + o.dy + h + 4]
        const inside = box[0] > INNER && box[2] < W - INNER && box[1] > INNER && box[3] < H - INNER
        const within = (q: Pt) => q.x > box[0] && q.x < box[2] && q.y > box[1] && q.y < box[3]
        const crowd = new Set(busy.filter(within).map(q => `${Math.floor(q.x / 8)} ${Math.floor(q.y / 8)}`)).size
        const covered = numbers.filter(q => q.x > box[0] - EVENT_R && q.x < box[2] + EVENT_R && q.y > box[1] - EVENT_R && q.y < box[3] + EVENT_R).length
        const names = avoid.filter(q => overlaps(q, box)).length
        return {
          ...o, box,
          score: crowd + 40 * covered + 60 * names + 1.5 * o.f + (inside ? 0 : 1000) + (placed.some(q => overlaps(q, box)) ? 500 : 0),
        }
      })
    const at = spots.reduce((a, o) => (o.score < a.score ? o : a), spots[0])
    placed.push(at.box)
    const lx = p.x + at.dx, ly = p.y + at.dy
    // the leader runs from the place to the label's nearest point; where an event number covers the place, the
    // sabres move along it, out from under the number
    const ex = Math.min(Math.max(p.x, lx - 3), lx + w + 3), ey = Math.min(Math.max(p.y, ly), ly + h)
    const len = Math.hypot(ex - p.x, ey - p.y) || 1, ux = (ex - p.x) / len, uy = (ey - p.y) / len
    const covered = numbers.some(q => Math.hypot(q.x - p.x, q.y - p.y) < EVENT_R + BIG_RING)
    const sx = covered ? p.x + ux * (EVENT_R + BIG_RING + 4) : p.x, sy = covered ? p.y + uy * (EVENT_R + BIG_RING + 4) : p.y
    return { b, p, stepped, lx, ly, w, h, ex, ey, ux, uy, covered, sx, sy, box: at.box }
  })
}

function Battles({ labels }: { labels: BattleLabel[] }) {
  const { battle, setBattle } = useMap()
  if (!labels.length) return null
  const toggleOf = (b: Battle) => () => setBattle(battle === b.key ? null : b.key)
  const onKey = (toggle: () => void) => (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle() }
  }
  return (
    <g className={styles.lettering}>
      {labels.filter(l => l.stepped).map(({ b, p }) => {
        const toggle = toggleOf(b)
        return (
          <g key={b.key} role="button" tabIndex={0} aria-label={`${b.name}, ${b.dates}`} aria-expanded={false}
            className={styles.battle} onClick={toggle} onKeyDown={onKey(toggle)} style={{ opacity: 0.3 }}>
            <title>{`${b.name}, ${b.dates}`}</title>
            <g transform={`translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) scale(0.75)`}>
              <circle r={BIG_RING + 3} className={styles.battleHit} />
              <circle r={BIG_RING} className={styles.battleRingHalo} />
              <circle r={BIG_RING} className={styles.battleRing} />
              <g transform="scale(1.25)" className={styles.battleMarkBig}><Sabres /></g>
            </g>
          </g>
        )
      })}
      {labels.filter(l => !l.stepped).map(({ b, p, lx, ly, w, h, ex, ey, ux, uy, covered, sx, sy }) => {
        const name = b.name.toUpperCase()
        const toggle = toggleOf(b)
        return (
          <g key={b.key} role="button" tabIndex={0} aria-label={`${b.name}, ${b.dates}`} aria-expanded={battle === b.key}
            className={battle === b.key ? styles.battleOn : styles.battle} onClick={toggle} onKeyDown={onKey(toggle)}>
            <title>{`${b.name}, ${b.dates}`}</title>
            <rect x={lx - 4} y={ly - 2} width={w + 8} height={h + 4} className={styles.battleHit} />
            <line x1={p.x + ux * (covered ? EVENT_R : BIG_RING)} y1={p.y + uy * (covered ? EVENT_R : BIG_RING)} x2={ex} y2={ey} className={styles.battleLeader} />
            <g transform={`translate(${sx.toFixed(1)} ${sy.toFixed(1)})`}>
              <circle r={BIG_RING} className={styles.battleRingHalo} />
              <circle r={BIG_RING} className={styles.battleRing} />
              <g transform="scale(1.25)" className={styles.battleMarkBig}><Sabres /></g>
            </g>
            <text x={lx} y={ly + 14} fontSize={14.5} letterSpacing="0.16em" className={styles.halo}>{name}</text>
            <text x={lx} y={ly + 14} fontSize={14.5} letterSpacing="0.16em" className={styles.battleName}>{name}</text>
            <text x={lx} y={ly + 29} fontSize={10} className={styles.halo}>{b.dates}</text>
            <text x={lx} y={ly + 29} fontSize={10} className={styles.battleDates}>{b.dates}</text>
          </g>
        )
      })}
    </g>
  )
}

const BIG_RING = 13

// The battles big enough to be drawn on their own this month (for the unit), as points on the sheet
function bigBattlesOn(unit: Unit, month: number) {
  const ym = MONTHS[month]
  return BATTLES.filter(b => unit.battles.includes(b.key) && b.from <= ym && ym <= b.to)
    .map(b => { const [x, y] = project(b.lon, b.lat); return { ...b, x, y } })
}

// The brigade's own fights in a stretch of days (the timeline's month, the war path's chosen year): each place its
// route marks as a battle, with small sabres and the place's name, so a village the map doesn't otherwise name shows
// where the fighting was. Where the map names the town already, only the sabres are added; where a great battle of
// the stretch stands, it alone is drawn; a name that would run into another is left to the sabres' tooltip.
function Fights({ unit, from, to, big, view, numbers, townNames, townBoxes }: {
  unit: Unit; from: number; to: number; big: Pt[]; view: View; numbers: Pt[]; townNames: Set<string>; townBoxes: Box[]
}) {
  const { setOpen, fight, setFight } = useMap()
  const T = toSheet(view)
  const fights = unit.ROUTE.filter(w => w.kind === 'battle' && day(w.date) >= from && day(w.date) <= to)
    .filter(w => !big.some(b => Math.hypot(b.x - w.x, b.y - w.y) < 8))      // the same place, ~7 km
    .filter((w, i, list) => list.findIndex(o => o.place === w.place) === i)
  const placed: Box[] = [...townBoxes]
  return (
    <g className={styles.lettering}>
      {fights.map(w => {
        const p = T(w)
        if (p.x < INNER || p.x > W - INNER || p.y < INNER || p.y > H - INNER) return null
        // clear of an event number on the place
        const under = numbers.some(q => Math.hypot(q.x - p.x, q.y - p.y) < EVENT_R + 4)
        const named = townNames.has(w.place.toLowerCase())
        const sx = p.x + (under ? EVENT_R + 9 : 8), sy = p.y - (named ? 9 : 0)
        const nameBox: Box = [sx + 6, sy - 4.5, sx + 8 + w.place.length * 10.5 * 0.52, sy + 5.5]
        const lettered = !named && !placed.some(b => overlaps(b, nameBox))
        if (lettered) placed.push(nameBox)
        // a fight the map numbers opens its event's card, any other its own
        const event = unit.labelled.indexOf(w)
        const at = unit.ROUTE.indexOf(w)
        const open = () => (event >= 0 ? setOpen(event) : setFight(fight === at ? null : at))
        return (
          <g key={`${w.date}${w.place}`} role="button" tabIndex={0} aria-label={w.label ?? `${w.place}, borba brigade`}
            className={fight === at ? styles.fightOn : styles.fight} onClick={open}
            onKeyDown={(e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open() } }}>
            <title>{`${w.label ?? w.place}`}</title>
            {!under && <circle cx={p.x} cy={p.y} r={1.6} className={styles.markFull} />}
            <g transform={`translate(${sx.toFixed(1)} ${sy.toFixed(1)}) scale(0.62)`}>
              <g className={styles.battleHalo}><Sabres /></g>
              <g className={styles.battleMark}><Sabres /></g>
            </g>
            {lettered && (
              <>
                <text x={sx + 7} y={sy + 3.8} fontSize={10.5} className={styles.halo}>{w.place}</text>
                <text x={sx + 7} y={sy + 3.8} fontSize={10.5} className={styles.fightName}>{w.place}</text>
              </>
            )}
          </g>
        )
      })}
    </g>
  )
}

function Route({ townBoxes, townNames, battles }: { townBoxes: Box[]; townNames: Set<string>; battles: BattleLabel[] }) {
  const { unit, variant, year, month, view, marker, numbers } = useMap()
  const T = toSheet(view)
  const first = T(unit.ROUTE[0]), last = T(unit.ROUTE[unit.ROUTE.length - 1])
  const ends = (
    <>
      <circle cx={first.x} cy={first.y} r={4.4} className={styles.here} />
      <circle cx={last.x} cy={last.y} r={5.2} className={styles.endRing} />
      <circle cx={last.x} cy={last.y} r={2.4} className={styles.here} />
    </>
  )
  let body: ReactNode
  if (variant === 'put') {
    // the whole way, a year to a pattern; a chosen year stands out and the others step back
    // a move away from the fighting (to rest, by train) is a thin line of its own, without arrows
    const runs: { year: Year; move: boolean; pts: Pt[] }[] = []
    for (const s of unit.samples) {
      const y = yearOf(s.t), move = !!s.move, p = T(s)
      const run = runs[runs.length - 1]
      if (run && run.year === y && run.move === move) run.pts.push(p)
      else runs.push({ year: y, move, pts: run ? [run.pts[run.pts.length - 1], p] : [p] })
    }
    body = (
      <>
        <g>
          {runs.map((r, i) => (
            <g key={i} className={year && year !== r.year ? styles.faded : undefined}>
              {r.move
                ? <path d={pathOf(r.pts)} className={styles.routeMove} />
                : <path d={pathOf(r.pts)} className={r.year === '1945' ? styles.routeDotted : styles.route} strokeDasharray={DASH[r.year]} />}
              {!r.move && (!year || year === r.year) && <Arrows pts={r.pts} />}
            </g>
          ))}
          {ends}
        </g>
        {year && (
          <Fights unit={unit} from={yearStart(year)} to={yearEnd(year)} big={battles.filter(l => !l.b.dim).map(l => { const [x, y] = project(l.b.lon, l.b.lat); return { x, y } })}
            view={view} numbers={numbers} townNames={townNames} townBoxes={townBoxes} />
        )}
        <Battles labels={battles} />
        <EventNumbers year={year} />
      </>
    )
  } else {
    const ym = MONTHS[month]
    const now = monthEnd(ym)
    const past = unit.samples.filter(s => s.t <= now)
    const at = T(past[past.length - 1] ?? unit.samples[0])
    // the way already behind the unit, a month at a time, each fainter the longer ago it was walked
    const runs: { age: number; move: boolean; pts: Pt[] }[] = []
    for (const s of past) {
      const age = month - monthIndex(s.t), move = !!s.move, p = T(s)
      const run = runs[runs.length - 1]
      if (run && run.age === age && run.move === move) run.pts.push(p)
      else runs.push({ age, move, pts: run ? [run.pts[run.pts.length - 1], p] : [p] })
    }
    // arrows on the last months' marching, not on the moves between
    // arrows on the month's marching and the month before's, as faint as their line, none on the moves between
    const arrowRuns = runs.filter(r => r.age <= 1 && !r.move && r.pts.length > 1)
    body = (
      <>
        {runs.map((r, i) => r.pts.length > 1 && (
          <path key={`r${i}`} d={pathOf(r.pts)} className={r.move ? styles.routeMove : styles.route} style={{ opacity: fade(r.age) }} />
        ))}
        {arrowRuns.map((r, i) => <g key={`a${i}`} style={{ opacity: fade(r.age) }}><Arrows pts={r.pts} /></g>)}
        <Fights unit={unit} from={monthStart(ym)} to={now} big={bigBattlesOn(unit, month)} view={view} numbers={numbers}
          townNames={townNames} townBoxes={townBoxes} />
        <Battles labels={battles} />
        <circle cx={at.x} cy={at.y} r={8.5} className={styles.hereRing} />
        <circle cx={at.x} cy={at.y} r={4.2} className={styles.here} />
        <EventNumbers upTo={now} />
      </>
    )
  }
  const m = marker && T(marker)
  return (
    <g role="group" aria-label={`Ratni put: ${unit.name}`}>
      {body}
      {m && (
        <g className={styles.lettering}>
          <circle cx={m.x} cy={m.y} r={9} className={styles.markerRing} />
          <circle cx={m.x} cy={m.y} r={3} className={styles.here} />
          {marker!.label && (
            <>
              <text x={m.x + 13} y={m.y + 3.5} fontSize={9.5} className={styles.halo}>{marker!.label}</text>
              <text x={m.x + 13} y={m.y + 3.5} fontSize={9.5} className={styles.markerLabel}>{marker!.label}</text>
            </>
          )}
        </g>
      )}
    </g>
  )
}

// ---------- the sheet's furniture: title block, scale, the country in small ----------

const TITLE_RIGHT = W - INNER - 14
const TITLE_TOP = INNER + 12

function titleLines(unit: Unit, variant: 'put' | 'vreme', year: Year | null, month: number) {
  const [name, honour] = unit.name.split(' „')
  const y0 = unit.ROUTE[0].date.slice(0, 4), y1 = unit.ROUTE[unit.ROUTE.length - 1].date.slice(0, 4)
  const sub = variant === 'vreme' ? monthName(MONTHS[month]) : year ? `ratni put, ${year}.` : `ratni put ${y0}–${y1}.`
  return {
    name: name.toUpperCase(),
    honour: honour ? `„${honour.toUpperCase()}` : null,
    sub,
  }
}

// "Tumač znakova", as the book maps print it, in the sheet's lower left corner (over the Adriatic when the whole
// country shows): the brigade's marks, a rule, then the country as it was divided after the April war. It stays
// folded to a small tab with its name until it is opened, so it covers nothing of a close-up
const KEY_W = 214, KEY_ROW = 13
function keyRows(variant: 'put' | 'vreme', transfers: boolean, battles: boolean, year: Year | null): [ReactNode, string][] {
  return [
    [<line key="r" x1={0} x2={20} y1={0} y2={0} className={styles.route} />, 'put brigade'],
    ...(transfers ? [[<line key="m" x1={0} x2={20} y1={0} y2={0} className={styles.routeMove} />, 'premeštanje van borbe'] as [ReactNode, string]] : []),
    ...(variant === 'vreme' ? [[<g key="h"><circle cx={10} cy={0} r={5.2} className={styles.hereRing} /><circle cx={10} cy={0} r={2.6} className={styles.here} /></g>, 'brigada u tom mesecu'] as [ReactNode, string]] : []),
    [<g key="e"><circle cx={10} cy={0} r={5.8} className={styles.eventMark} /><text x={10} y={2.9} className={styles.eventNumber} style={{ fontSize: 8 }}>1</text></g>, 'događaj (klik: opis)'],
    ...(battles ? [[<g key="b" transform="translate(10 0) scale(0.5)"><circle r={BIG_RING} className={styles.battleRing} /><g transform="scale(1.25)" className={styles.battleMarkBig}><Sabres /></g></g>, variant === 'vreme' ? 'velika bitka, dok traje' : 'velika bitka'] as [ReactNode, string]] : []),
    ...(variant === 'vreme' || year ? [[<g key="s" transform="translate(10 0) scale(0.62)" className={styles.battleMark}><Sabres /></g>, variant === 'vreme' ? 'borba brigade u tom mesecu' : 'borba brigade te godine'] as [ReactNode, string]] : []),
    [<g key="t"><circle cx={10} cy={0} r={2} className={styles.markOpen} /><circle cx={10} cy={0} r={0.7} className={styles.markFull} /></g>, 'naselje'],
  ]
}

// the lines a period draws, for the key
function partitionLines(period: Period): [string, string][] {
  return [
    ...(period.lines.length ? [[styles.zoneLine, 'granica'] as [string, string]] : []),
    ...(period.ndh ? [
      [styles.demarcationLine, 'nemačko-italijanska linija u NDH'],
      [styles.zoneIILine, 'granica II i III italijanske zone'],
      [styles.variantLine, 'varijanta te granice'],
    ] as [string, string][] : []),
  ]
}

const TAB_W = 112, TAB_H = 22
const KEY_STORE = 'mapa-tumac-otvoren'

function MapKey({ rows, period, free, open, onToggle, scale }: {
  rows: [ReactNode, string][]; period: Period | null; free: Liberated | null; open: boolean; onToggle: () => void; scale: number
}) {
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle() }
  }
  // the heading opens and folds it: a chevron pointing where the box goes
  const heading = (w: number, up: boolean) => (
    <g role="button" tabIndex={0} aria-expanded={open} aria-label={open ? 'Sklopi tumač znakova' : 'Otvori tumač znakova'}
      className={styles.keyTab} onClick={onToggle} onKeyDown={onKey}>
      <rect width={w} height={TAB_H} className={styles.keyTabHit} />
      <text x={10} y={14.5} fontSize={7.5} letterSpacing="0.35em">TUMAČ ZNAKOVA</text>
      <path d={up ? `M${w - 16} 13.5l4 -4 4 4` : `M${w - 16} 9.5l4 4 4 -4`} className={styles.keyChevron} />
    </g>
  )
  if (!open) {
    return (
      <g transform={`translate(${INNER + 8} ${H - INNER - 8 - TAB_H})`} className={styles.lettering}>
        <rect width={TAB_W} height={TAB_H} className={styles.legendFrame} />
        {heading(TAB_W, true)}
      </g>
    )
  }
  // the period's zones, each legend once (the NDH of 1941 and of 1943 say the same)
  const zones = period ? zonesIn(period).filter((z, i, list) => list.findIndex(o => o.legend === z.legend) === i) : []
  const lineRows = period ? partitionLines(period) : []
  const freeRows = free ? (free.semi ? 2 : 1) : 0
  const zoneRows = freeRows + zones.length + lineRows.length
  const ruleAt = 28 + rows.length * KEY_ROW - 4
  const h = ruleAt + (zoneRows ? 12 + zoneRows * KEY_ROW : 0) + 4
  const row = (i: number) => (i < rows.length ? 28 + i * KEY_ROW : ruleAt + 16 + (i - rows.length) * KEY_ROW)
  return (
    <g transform={`translate(${INNER + 8} ${H - INNER - 8 - h})`} className={styles.lettering}>
      <rect width={KEY_W} height={h} className={styles.legendFrame} />
      {heading(KEY_W, false)}
      {rows.map(([mark, text], i) => (
        <g key={text} transform={`translate(10 ${row(i)})`}>
          {mark}
          <text x={28} y={2.8} fontSize={7.8}>{text}</text>
        </g>
      ))}
      {zoneRows > 0 && (
        <>
          <line x1={10} x2={KEY_W - 10} y1={ruleAt + 4} y2={ruleAt + 4} className={styles.keyRule} />
          {free && (
            <>
              <g transform={`translate(10 ${row(rows.length)})`}>
                <rect x={1} y={-4} width={18} height={8} className={styles.free} />
                <text x={28} y={2.8} fontSize={7.8}>{`slobodna teritorija, ${free.label}`}</text>
              </g>
              {free.semi && <g transform={`translate(10 ${row(rows.length + 1)})`}>
                <rect x={1} y={-4} width={18} height={8} fill="url(#hatch-free)" className={styles.semiFree} />
                <rect x={1} y={-4} width={18} height={8} fill="none" className={styles.swatch} />
                <text x={28} y={2.8} fontSize={7.8}>poluoslobođena teritorija</text>
              </g>}
            </>
          )}
          {zones.map((z, i) => (
            <g key={z.key} transform={`translate(10 ${row(rows.length + freeRows + i)})`}>
              {z.tone > 0 && <rect x={1} y={-4} width={18} height={8} className={styles.tone}
                style={{ fill: tint(z.power), fillOpacity: Math.min(1, z.tone * scale * (z.key === 'banat' ? 3.2 : 1)) }} />}
              {z.hatch && <rect x={1} y={-4} width={18} height={8} fill={`url(#hatch-${z.hatch})`} />}
              <rect x={1} y={-4} width={18} height={8} fill="none" className={styles.swatch} />
              <text x={28} y={2.8} fontSize={7.8}>{z.legend}</text>
            </g>
          ))}
          {lineRows.map(([cls, text], i) => (
            <g key={text} transform={`translate(10 ${row(rows.length + freeRows + zones.length + i)})`}>
              {cls === styles.demarcationLine && <line x1={0} x2={20} y1={0} y2={0} className={styles.demarcationTicks} />}
              <line x1={0} x2={20} y1={0} y2={0} className={cls} />
              <text x={28} y={2.8} fontSize={7.8}>{text}</text>
            </g>
          ))}
        </>
      )}
    </g>
  )
}

// a scale bar as the sketches draw it, of a length that suits the zoom: blocks black and white in turn
function ScaleBar({ x, y, z }: { x: number; y: number; z: number }) {
  const u = SHEET.unitsPerKm * z
  const km = [25, 50, 100, 200].find(k => k * u >= 70) ?? 200
  const step = km / 4
  return (
    <g className={styles.scale}>
      {[0, 1, 2, 3].map(i => (
        <rect key={i} x={x - km * u + i * step * u} y={y} width={step * u} height={3} className={i % 2 === 0 ? styles.markFull : styles.markOpen} />
      ))}
      {[0, km / 2, km].map(k => (
        <text key={k} x={x - km * u + k * u} y={y + 11} textAnchor="middle" fontSize={7}>{k}</text>
      ))}
      <text x={x + 5} y={y + 11} fontSize={7}>km</text>
    </g>
  )
}

const LOC_W = 132, LOC_S = LOC_W / W, LOC_H = H * LOC_S
// The country in small, with the part the sheet shows marked, in whichever corner the unit leaves free
function Locator({ view, corner }: { view: View; corner: Pt }) {
  const vx = (view.cx - W / (2 * view.z)) * LOC_S, vy = (view.cy - H / (2 * view.z)) * LOC_S
  return (
    <g transform={`translate(${corner.x} ${corner.y})`} className={styles.locator}>
      <rect width={LOC_W} height={LOC_H} className={styles.locatorPaper} />
      <g transform={`scale(${LOC_S})`}><path d={LAND[0]} className={styles.locatorLand} /></g>
      <rect x={vx} y={vy} width={(W / view.z) * LOC_S} height={(H / view.z) * LOC_S} className={styles.locatorView} />
    </g>
  )
}


// ---------- the card for a numbered event ----------

function EventCard() {
  const { unit, open, setOpen, numbers, variant, month } = useMap()
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { ref.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) }, [open])
  if (open === null || open >= unit.labelled.length) return null
  const w = unit.labelled[open]
  if (variant === 'vreme' && day(w.date) > monthEnd(MONTHS[month])) return null
  const p = numbers[open]
  const [head, what = ''] = (w.label ?? w.place).split(': ')
  const ym = w.date.slice(0, 7)
  const n = unit.FALLEN_BY_MONTH[ym] ?? 0
  // the count opens the list of those soldiers in a new tab
  const killed = n ? (
    <>
      U {MONTHS_IN[Number(ym.slice(5)) - 1]} {ym.slice(0, 4)}. {plural('sr', n, { one: 'poginuo je', few: 'poginula su', other: 'poginulo je' })}{' '}
      <KilledLink href={killedPath(unit.key, { month: ym })}>{borci(n)} brigade</KilledLink>.
    </>
  ) : null
  const left = p.x / W, top = p.y / H
  const dx = left > 0.6 ? 'calc(-100% - 14px)' : '14px'
  const dy = top < 0.2 ? '-12%' : top > 0.75 ? '-88%' : '-50%'
  return (
    <div ref={ref} className={styles.card} role="dialog" aria-label={w.label ?? w.place}
      style={{ left: `${left * 100}%`, top: `${top * 100}%`, transform: `translate(${dx}, ${dy})` }}>
      <div className={styles.cardHead}>
        <span className={styles.legendNumber}>{open + 1}</span>
        <p className={styles.cardTitle}>{head}</p>
        <button type="button" className={styles.cardClose} onClick={() => setOpen(null)} aria-label="Zatvori"><CloseIcon size={16} /></button>
      </div>
      {what && <p className={styles.cardWhat}>{what.charAt(0).toUpperCase() + what.slice(1)}</p>}
      {w.about && <p className={styles.cardText}>{w.about}</p>}
      {killed && <p className={styles.cardText}>{killed}</p>}
      <p className={styles.cardSource}>Prema: {unit.SOURCE}</p>
    </div>
  )
}

// ---------- the card for a great battle ----------

// What the battle was, in a few lines, and the brigade's own numbered events in it so far (a click opens one)
function BattleCard() {
  const { unit, battle, setBattle, setOpen, variant, month, view } = useMap()
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { ref.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) }, [battle])
  if (!battle) return null
  // on the timeline the month's battles, on the war path all the unit's
  const list = variant === 'vreme' ? bigBattlesOn(unit, month)
    : BATTLES.filter(x => unit.battles.includes(x.key)).map(x => { const [bx, by] = project(x.lon, x.lat); return { ...x, x: bx, y: by } })
  const b = list.find(x => x.key === battle)
  if (!b) return null
  const p = toSheet(view)(b)
  const now = variant === 'vreme' ? monthEnd(MONTHS[month]) : Infinity
  const events = unit.labelled.map((w, i) => ({ w, i }))
    // within its days, and not a move away from the fighting (Prva lička's rest in Beograd during the Srem front)
    .filter(({ w }) => day(w.date) >= day(b.start) && day(w.date) <= day(b.end) && day(w.date) <= now && w.kind !== 'transfer')
  const left = Math.min(Math.max(p.x / W, 0), 1), top = Math.min(Math.max(p.y / H, 0), 1)
  const dx = left > 0.6 ? 'calc(-100% - 18px)' : '18px'
  const dy = top < 0.2 ? '-12%' : top > 0.75 ? '-88%' : '-50%'
  return (
    <div ref={ref} className={styles.card} role="dialog" aria-label={b.name}
      style={{ left: `${left * 100}%`, top: `${top * 100}%`, transform: `translate(${dx}, ${dy})` }}>
      <div className={styles.cardHead}>
        <svg width="22" height="22" viewBox="-14 -14 28 28" aria-hidden="true" className={styles.cardSabres}>
          <circle r={BIG_RING} className={styles.battleRing} />
          <g transform="scale(1.25)" className={styles.battleMarkBig}><Sabres /></g>
        </svg>
        <p className={styles.cardTitle}>{b.name}</p>
        <button type="button" className={styles.cardClose} onClick={() => setBattle(null)} aria-label="Zatvori"><CloseIcon size={16} /></button>
      </div>
      <p className={styles.cardWhat}>{b.dates}</p>
      <p className={styles.cardText}>{b.about}</p>
      {events.length > 0 && (
        <>
          <p className={styles.cardSub}>Brigada u ovoj bici</p>
          <ul className={styles.cardEvents}>
            {events.map(({ w, i }) => (
              <li key={i}>
                <button type="button" className={styles.legendItem} onClick={() => setOpen(i)}>
                  <span className={styles.legendNumber}>{i + 1}</span>{w.label}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

// ---------- the card for one of the brigade's fights ----------

// A fight the book's route names without an event of its own: the place, the month, the brigade's killed there that
// month (their list a click away), and the book
function FightCard() {
  const { unit, fight, setFight, variant, month, year, view } = useMap()
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { ref.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) }, [fight])
  if (fight === null) return null
  const w = unit.ROUTE[fight]
  if (!w) return null
  // the fight's own month (on the war path, of the year chosen)
  const ym = w.date.slice(0, 7)
  if (variant === 'vreme' ? ym !== MONTHS[month] : !year || yearOf(day(w.date)) !== year) return null
  const p = toSheet(view)(w)
  // the killed of the month at the place: the spot of that name, else the nearest one close by
  const near = unit.FALLEN.map((f, i) => ({ f, i, d: Math.hypot(f.x - w.x, f.y - w.y) }))
    .filter(({ f, d }) => f.months[ym] && (f.place === w.place || d < 12))
    .sort((a, b) => Number(b.f.place === w.place) - Number(a.f.place === w.place) || a.d - b.d)[0]
  const n = near ? near.f.months[ym] : 0
  const left = Math.min(Math.max(p.x / W, 0), 1), top = Math.min(Math.max(p.y / H, 0), 1)
  const dx = left > 0.6 ? 'calc(-100% - 16px)' : '16px'
  const dy = top < 0.2 ? '-12%' : top > 0.75 ? '-88%' : '-50%'
  return (
    <div ref={ref} className={styles.card} role="dialog" aria-label={w.place}
      style={{ left: `${left * 100}%`, top: `${top * 100}%`, transform: `translate(${dx}, ${dy})` }}>
      <div className={styles.cardHead}>
        <svg width="18" height="18" viewBox="-9 -9 18 18" aria-hidden="true" className={styles.cardSabres}>
          <g className={styles.battleMark}><Sabres /></g>
        </svg>
        <p className={styles.cardTitle}>{w.place}</p>
        <button type="button" className={styles.cardClose} onClick={() => setFight(null)} aria-label="Zatvori"><CloseIcon size={16} /></button>
      </div>
      <p className={styles.cardWhat}>Borba brigade, {monthName(ym)}</p>
      {n > 0 && (
        <p className={styles.cardText}>
          {plural('sr', n, { one: 'Tu je poginuo', few: 'Tu su poginula', other: 'Tu je poginulo' })}{' '}
          <KilledLink href={killedPath(unit.key, { spot: near!.i, month: ym })}>{borci(n)} brigade</KilledLink>.
        </p>
      )}
      <p className={styles.cardSource}>Prema: {unit.SOURCE}</p>
    </div>
  )
}

// ---------- the sheet ----------

export default function MapSheet({ below, aside }: { below?: ReactNode; aside?: ReactNode }) {
  const { unit, variant, year, month, partition, view, manual, setManual, colors, toneScale, numbers, battle } = useMap()
  const shownMonth = variant === 'vreme' ? MONTHS[month] : YEAR_MONTH[year ?? ''] ?? '1942-06'
  const period = partition ? periodAt(shownMonth) : null
  // the liberated territory only on the timeline, in the months a map of it covers
  const free = variant === 'vreme' ? freeAt(shownMonth) : null
  const T = toSheet(view)
  const lines = view.z >= RIVER_LINES_FROM, minor = view.z >= MINOR_FROM
  const title = titleLines(unit, variant, year, month)
  // On the timeline the month stands large in the title block, the sheet's corner: the reader looks there as the
  // months step by. The war path keeps its small line
  const big = variant === 'vreme'
  const subSize = big ? 27 : 10.5
  const subY = TITLE_TOP + (title.honour ? 25 : 12) + (big ? 31 : 16)
  const scaleY = subY + (big ? 10 : 9)
  // a month the free territory's map only stands in for says so, small, under the scale
  const standIn = free?.standIn.includes(shownMonth) ? [`slobodna teritorija sa karte za ${free.label}`, '(za ovaj mesec karte nema)'] : null
  const titleW = Math.max(title.name.length * 13 * 0.64, (title.honour?.length ?? 0) * 9 * 0.64, title.sub.length * subSize * 0.56, 150,
    (standIn?.[0].length ?? 0) * 8.5 * 0.5)
  const titleH = scaleY - TITLE_TOP + 12 + (standIn ? 25 : 0)
  const rows = keyRows(variant, unit.ROUTE.some(w => w.kind === 'transfer'), unit.battles.length > 0, variant === 'put' ? year : null)
  const titleBox: Box = [TITLE_RIGHT - titleW - 10, TITLE_TOP - 6, TITLE_RIGHT + 6, TITLE_TOP + titleH + 20]
  // the key stays as the reader left it, in this browser (it opens folded where storage is not to be had)
  const [keyOpen, setKeyOpen] = useState(false)
  useEffect(() => {
    try { setKeyOpen(window.localStorage.getItem(KEY_STORE) === '1') } catch { /* folded */ }
  }, [])
  const toggleKey = () => setKeyOpen(o => {
    try { window.localStorage.setItem(KEY_STORE, o ? '0' : '1') } catch { /* not kept */ }
    return !o
  })

  // the locator goes to the corner the route leaves emptiest (never over the partition's legend)
  const zoomed = view.z > 1.15
  const corner = useMemo(() => {
    const pts = unit.samples.map(T)
    const corners: Pt[] = [
      { x: INNER + 10, y: H - INNER - 10 - LOC_H },
      { x: W - INNER - 10 - LOC_W, y: H - INNER - 10 - LOC_H },
      { x: INNER + 10, y: INNER + 50 },              // under the zoom buttons
    ].filter((_, i) => !(partition && i === 0))
    const count = (c: Pt) => pts.filter(p => p.x > c.x - 8 && p.x < c.x + LOC_W + 8 && p.y > c.y - 8 && p.y < c.y + LOC_H + 8).length
    return corners.reduce((best, c) => (count(c) < count(best) ? c : best), corners[0])
  }, [unit, view, partition])                         // eslint-disable-line react-hooks/exhaustive-deps
  const keepClear: Box[] = [titleBox, ...(zoomed ? [[corner.x - 4, corner.y - 4, corner.x + LOC_W + 4, corner.y + LOC_H + 4] as Box] : [])]
  // the great battles' labels before the villages: a village's name makes way for a battle's, which keeps off the
  // overview's towns and the title block
  const shown = battlesFor(unit, variant, month, year, view, numbers)
  const battleLabels = placeBattles(shown.list, battle, view, numbers, shown.busy, [...keepClear, ...mainTowns(view).map(m => m.box)])
  const labelBoxes = battleLabels.flatMap(l => (l.box ? [l.box] : []))
  const towns = placeTowns(view, [...keepClear, ...labelBoxes])

  // Shift and the wheel enlarge the map at the pointer, a drag with the mouse moves it; the frame is then the
  // reader's until "Vrati okvir"
  const wrap = useRef<HTMLDivElement>(null)
  const live = useRef({ view, setManual })
  live.current = { view, setManual }
  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const at = (e: { clientX: number; clientY: number }) => {
      const r = el.getBoundingClientRect()
      return { x: ((e.clientX - r.left) / r.width) * W, y: ((e.clientY - r.top) / r.height) * H }
    }
    const onWheel = (e: WheelEvent) => {
      if (!e.shiftKey) return
      const d = e.deltaY || e.deltaX                  // with Shift held, some browsers turn the wheel sideways
      if (!d) return
      e.preventDefault()
      const { view: v, setManual: set } = live.current
      const p = at(e)
      const z = Math.min(ZOOM_MOST, Math.max(1, v.z * Math.exp(-d * (e.deltaMode === 1 ? 0.08 : 0.002))))
      // the place under the pointer stays under it
      const wx = (p.x - W / 2) / v.z + v.cx, wy = (p.y - H / 2) / v.z + v.cy
      set(held({ z, cx: wx - (p.x - W / 2) / z, cy: wy - (p.y - H / 2) / z }))
    }
    let drag: { x: number; y: number; v: View; moved: boolean } | null = null
    const onDown = (e: PointerEvent) => {
      if (e.pointerType !== 'mouse' || e.button !== 0 || live.current.view.z <= 1.001) return
      const p = at(e)
      drag = { x: p.x, y: p.y, v: live.current.view, moved: false }
    }
    const onMove = (e: PointerEvent) => {
      if (!drag) return
      const p = at(e)
      if (!drag.moved && Math.hypot(p.x - drag.x, p.y - drag.y) < 4) return
      drag.moved = true
      el.classList.add(styles.dragging)
      const { v } = drag
      live.current.setManual(held({ z: v.z, cx: v.cx - (p.x - drag.x) / v.z, cy: v.cy - (p.y - drag.y) / v.z }))
    }
    const onUp = () => {
      el.classList.remove(styles.dragging)
      if (drag?.moved) {
        // a drag is no click on what it started on
        const stop = (ev: Event) => { ev.stopPropagation(); ev.preventDefault() }
        el.addEventListener('click', stop, { capture: true, once: true })
        setTimeout(() => el.removeEventListener('click', stop, { capture: true }), 0)
      }
      drag = null
    }
    // the browser's own drag (a link, the sheet as an image) would take the gesture from the map
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

  // on a phone the sheet is wider than the screen: start it at the middle, where the unit is
  const scroller = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const s = scroller.current
    if (s && s.scrollWidth > s.clientWidth) s.scrollLeft = (s.scrollWidth - s.clientWidth) / 2
  }, [unit.key, variant])

  const ground = `translate(${(W / 2 - view.cx * view.z).toFixed(2)} ${(H / 2 - view.cy * view.z).toFixed(2)}) scale(${view.z.toFixed(4)})`
  return (
    <figure className={styles.plate} style={Object.fromEntries(Object.entries(colors).map(([k, c]) => [`--zone-${k}`, c])) as React.CSSProperties}>
      <div className={variant === 'vreme' && aside ? styles.plateRow : undefined}>
      {variant === 'vreme' && aside}
      <div className={styles.scroller} ref={scroller}>
        <div className={styles.sheetWrap} ref={wrap}>
          <svg viewBox={`0 0 ${W} ${H}`} className={styles.sheet} role="img" aria-label={`${unit.name}, ${title.sub}`}>
            <defs>
              {/* the ink's edge: a fine grain pushes every line a hair off true, as ink on paper does */}
              <filter id="map-ink" x="-1%" y="-1%" width="102%" height="102%">
                <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="1" seed="7" result="grain" />
                <feDisplacementMap in="SourceGraphic" in2="grain" scale="0.8" xChannelSelector="R" yChannelSelector="G" />
              </filter>
              <clipPath id="map-inside"><rect x={INNER} y={INNER} width={W - 2 * INNER} height={H - 2 * INNER} /></clipPath>
              <path id="map-sea" d={SEA.d} />
              {partition && <Hatches z={view.z} />}
              <pattern id="hatch-free" width="3.2" height="3.2" patternUnits="userSpaceOnUse"
                patternTransform={`scale(${(1 / view.z).toFixed(4)}) rotate(-45)`} className={styles.freeHatch}>
                <line x1="0.4" y1="0" x2="0.4" y2="3.2" />
              </pattern>
            </defs>

            <rect width={W} height={H} className={styles.paper} />
            <g clipPath="url(#map-inside)">
              <g filter="url(#map-ink)">
                <g transform={ground}><Country period={period} free={free} lines={lines} minor={minor} scale={toneScale} /></g>
              </g>
              <g transform={ground}><GroundLettering z={view.z} period={period} /></g>
              <g className={styles.lettering}>{towns.nodes}</g>
              <g filter="url(#map-ink)"><Route townBoxes={[...towns.boxes, ...labelBoxes]} townNames={towns.names} battles={battleLabels} /></g>
              <MapKey rows={rows} period={period} free={free} open={keyOpen} onToggle={toggleKey} scale={toneScale} />
              {zoomed && <Locator view={view} corner={corner} />}
              <g className={styles.lettering}>
                <rect x={titleBox[0]} y={titleBox[1]} width={titleBox[2] - titleBox[0]} height={titleBox[3] - titleBox[1]} className={styles.titlePaper} />
                <text x={TITLE_RIGHT} y={TITLE_TOP + 12} textAnchor="end" fontSize={13} letterSpacing="0.06em">{title.name}</text>
                {title.honour && <text x={TITLE_RIGHT} y={TITLE_TOP + 25} textAnchor="end" fontSize={9.5} letterSpacing="0.06em">{title.honour}</text>}
                <text x={TITLE_RIGHT} y={subY} textAnchor="end" fontSize={subSize} letterSpacing={big ? '0.03em' : undefined}
                  className={big ? styles.titleMonth : undefined}>{title.sub}</text>
                <ScaleBar x={TITLE_RIGHT - 12} y={scaleY} z={view.z} />
                {standIn && standIn.map((line, i) => (
                  <text key={i} x={TITLE_RIGHT} y={scaleY + 25 + i * 10.5} textAnchor="end" fontSize={8.5} className={styles.titleNote}>{line}</text>
                ))}
              </g>
            </g>
            <rect x={FRAME} y={FRAME} width={W - 2 * FRAME} height={H - 2 * FRAME} className={styles.frameOuter} />
            <rect x={INNER} y={INNER} width={W - 2 * INNER} height={H - 2 * INNER} className={styles.frameInner} />
          </svg>
          <EventCard />
          <BattleCard />
          <FightCard />
          <div className={styles.zoomTools}>
            <button type="button" className={styles.zoomButton} aria-label="Uvećaj kartu" title="Uvećaj (Shift i točkić)"
              onClick={() => setManual(held({ ...view, z: Math.min(ZOOM_MOST, view.z * 1.5) }))}>+</button>
            <button type="button" className={styles.zoomButton} aria-label="Umanji kartu" title="Umanji (Shift i točkić)"
              onClick={() => setManual(held({ ...view, z: Math.max(1, view.z / 1.5) }))}>−</button>
            {manual && <button type="button" className={styles.resetView} onClick={() => setManual(null)}>Vrati okvir</button>}
          </div>
        </div>
      </div>
      </div>
      <figcaption className={styles.caption}>
        {variant === 'vreme'
          ? `${unit.name}, ${monthName(MONTHS[month])}`
          : `Ratni put ${unit.genitive}, ${year ? `${year}.` : `${unit.ROUTE[0].date.slice(0, 4)}–${unit.ROUTE[unit.ROUTE.length - 1].date.slice(0, 4)}.`}`}
        {' '}Prema: {unit.SOURCE}.
        {free?.source && <> Slobodna teritorija prema: {free.source}.</>}
      </figcaption>
      {below}
    </figure>
  )
}
