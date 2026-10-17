'use client'

import { useEffect, useRef } from 'react'
import { formatNumber, plural } from '@/app/i18n/format'
import styles from './mapa.module.css'
import { DASH, MONTHS, MONTH_NAMES, YEARS, day, monthEnd, monthName } from './geometry'
import { DEFAULT_COLORS, POWERS, useMap, type Variant } from './state'
import { KilledLink } from './KilledLink'
import { killedPath } from './units'

const num = (n: number) => formatNumber('sr', n)
const borci = (n: number) => `${num(n)} ${plural('sr', n, { one: 'borac', few: 'borca', other: 'boraca' })}`

const VIEWS: { id: Variant; label: string }[] = [
  { id: 'vreme', label: 'Kroz vreme' },
  { id: 'put', label: 'Ratni put' },
]

// Above the map: which unit, which of the two views, and that view's own controls, in one place
export function Toolbar() {
  const { unit, variant, setVariant } = useMap()
  // one unit a page: the unit page's "Ratni put" opens the map at its unit (?jedinica=), with no switch to another
  // (the user, 2026-10-17)
  return (
    <div className={styles.toolbar}>
      <div className={styles.toolbarRow}>
        <p className={styles.unitPick}>
          <span>Jedinica</span> <b>{unit.name}</b>
        </p>
        <div className={styles.tabs} role="tablist" aria-label="Prikaz">
          {VIEWS.map(v => (
            <button key={v.id} type="button" role="tab" aria-selected={variant === v.id}
              className={variant === v.id ? styles.tabOn : styles.tab} onClick={() => setVariant(v.id)}>
              {v.label}
            </button>
          ))}
        </div>
      </div>
      <div className={styles.toolbarSub}>
        <div className={styles.toolbarView}>{variant === 'put' ? <RouteControls /> : <TimeControls />}</div>
        <SheetSwitches />
      </div>
    </div>
  )
}

// The sheet's own switch, under the tabs: how much of the country
function SheetSwitches() {
  const { whole, setWhole } = useMap()
  return (
    <div className={styles.sheetOptions}>
      <div className={styles.choice} role="group" aria-label="Prikaz karte">
        Karta:
        <button type="button" aria-pressed={!whole} className={styles.choiceButton} onClick={() => setWhole(false)}>oblast jedinice</button>
        <button type="button" aria-pressed={whole} className={styles.choiceButton} onClick={() => setWhole(true)}>cela zemlja</button>
      </div>
    </div>
  )
}

// Ratni put: the whole way or one year of it
function RouteControls() {
  const { year, setYear } = useMap()
  return (
    <div className={styles.viewControls}>
      <div className={styles.years} role="group" aria-label="Godina">
        <button type="button" aria-pressed={year === null} className={year === null ? styles.yearOn : styles.year} onClick={() => setYear(null)}>Sve</button>
        {YEARS.map(y => (
          <button key={y} type="button" aria-pressed={year === y} className={year === y ? styles.yearOn : styles.year}
            onClick={() => setYear(year === y ? null : y)}>
            <svg width="30" height="8" viewBox="0 0 30 8" aria-hidden="true">
              <line x1="1" y1="4" x2="29" y2="4" className={y === '1945' ? styles.routeDotted : styles.route} strokeDasharray={DASH[y]} />
            </svg>
            {y}
          </button>
        ))}
      </div>
    </div>
  )
}

// Kroz vreme: what happened in the month and how many were killed, directly over the map; the month itself stands
// large in the sheet's title block, the months and the play mark beside the map
function TimeControls() {
  const { unit, month } = useMap()
  const ym = MONTHS[month]
  const now = monthEnd(ym)
  const events = unit.ROUTE.filter(w => day(w.date) <= now && day(w.date) > monthEnd(MONTHS[month - 1] ?? '1941-11'))
  const killed = unit.FALLEN_BY_MONTH[ym] ?? 0
  return (
    <div className={styles.timelineTop}>
      <div className={styles.timelineHead}>
        <p className={styles.timelineNote}>
          {events.length ? `${events.map(w => w.label ?? w.place).join(' · ')}.` : 'Bez novog mesta na putu.'}
          {killed > 0 && <> Poginulo: <KilledLink href={killedPath(unit.key, { month: ym })}>{borci(killed)}</KilledLink>.</>}
        </p>
      </div>
    </div>
  )
}

// Beside the map in Kroz vreme: the war as a ruler along the sheet's edge. A tick for each month, a longer one with
// its year at each January, a grey bar back from the line for how many were killed (on a square-root scale, so a
// quiet month still shows beside the Sutjeska), a red dot on the line where the map numbers an event; the month
// shown has a red tick,
// a red mark on the line and its name, and a pointer over a tick shows that month's name. A click picks the month,
// the wheel over the ruler and the arrow keys (state.tsx) step through them, the play mark at its head runs them.
// On a phone the months run across, above the map.
export function MonthRail() {
  const { unit, variant, month, setMonth, playing, setPlaying } = useMap()
  const box = useRef<HTMLDivElement>(null)
  const strip = useRef<HTMLDivElement>(null)

  // on a phone the chosen month stays in sight in the strip, without moving the page
  useEffect(() => {
    const b = strip.current, item = b?.querySelector<HTMLElement>('[aria-current="date"]')
    if (!b || !item || b.scrollWidth <= b.clientWidth) return
    const pad = 36
    if (item.offsetLeft < b.scrollLeft + pad) b.scrollLeft = item.offsetLeft - pad
    else if (item.offsetLeft + item.offsetWidth > b.scrollLeft + b.clientWidth - pad) b.scrollLeft = item.offsetLeft + item.offsetWidth - b.clientWidth + pad
  }, [month, unit.key, variant])

  // the wheel over the ruler steps the months, a notch a month
  const bounds = useRef({ first: unit.first, last: unit.last })
  bounds.current = { first: unit.first, last: unit.last }
  useEffect(() => {
    const el = box.current
    if (!el) return
    let acc = 0
    const onWheel = (e: WheelEvent) => {
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return
      e.preventDefault()
      acc += e.deltaMode === 1 ? e.deltaY * 40 : e.deltaY
      const steps = Math.trunc(acc / 80)
      if (!steps) return
      acc -= steps * 80
      setPlaying(false)
      setMonth(m => Math.min(bounds.current.last, Math.max(bounds.current.first, m + steps)))
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [variant, setMonth, setPlaying])

  if (variant !== 'vreme') return null
  // a month's events by their number on the map
  const numbers = new Map<string, number[]>()
  unit.labelled.forEach((w, n) => numbers.set(w.date.slice(0, 7), [...(numbers.get(w.date.slice(0, 7)) ?? []), n + 1]))
  const months = MONTHS.map((ym, i) => ({ ym, i })).filter(m => m.i >= unit.first && m.i <= unit.last).map(({ ym, i }) => ({
    ym, i,
    year: ym.slice(0, 4),
    name: MONTH_NAMES[Number(ym.slice(5)) - 1],
    killed: unit.FALLEN_BY_MONTH[ym] ?? 0,
    nums: numbers.get(ym),
  }))
  const most = Math.sqrt(Math.max(1, ...months.map(m => m.killed)))
  const pick = (i: number) => { setPlaying(false); setMonth(i) }
  const title = (m: (typeof months)[number]) =>
    `${monthName(m.ym)}${m.nums ? ` · događaj ${m.nums.join(', ')}` : ''}${m.killed ? ` · poginulo ${borci(m.killed)}` : ''}`
  const cur = (i: number) => (i === month ? 'date' as const : undefined)

  const play = (
    <button type="button" className={styles.play} aria-label={playing ? 'Zaustavi' : 'Pusti kroz mesece'} title={playing ? 'Zaustavi' : 'Pusti kroz mesece'}
      onClick={() => {
        if (!playing && month >= unit.last) setMonth(unit.first)
        setPlaying(!playing)
      }}>
      <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
        {playing ? <><rect x="2" y="1.5" width="2.6" height="9" /><rect x="7.4" y="1.5" width="2.6" height="9" /></> : <path d="M3 1.2 10.6 6 3 10.8Z" />}
      </svg>
    </button>
  )

  return (
    <nav className={styles.rail} aria-label="Meseci">
      <div className={styles.railColumn} ref={box}>
        <div className={styles.railHead}>{play}</div>
        <ol className={styles.ruler}>
          {months.map(m => {
            const january = m.ym.endsWith('-01') || m.i === unit.first
            return (
              <li key={m.ym}>
                <button type="button" aria-current={cur(m.i)} className={m.i === month ? styles.rulerRowOn : styles.rulerRow}
                  title={title(m)} aria-label={title(m)} onClick={() => pick(m.i)}>
                  {m.killed > 0 && (
                    <span className={styles.rulerBar} style={{ width: `calc((100% - 0.75rem) * ${(Math.sqrt(m.killed) / most).toFixed(3)})` }} />
                  )}
                  <span className={styles.rulerLabel}>
                    {january && <span className={styles.rulerYear}>{m.year}.</span>}
                    <span className={styles.rulerMonth}>{m.name}</span>
                  </span>
                  <span className={styles.rulerAxis}>
                    <span className={january ? styles.rulerTickYear : styles.rulerTick} />
                    {m.nums && <i className={styles.rulerEvent} />}
                    {m.i === month && <i className={styles.rulerNow} />}
                  </span>
                </button>
              </li>
            )
          })}
        </ol>
      </div>
      {/* on a phone: the months across, above the map */}
      <div className={styles.railStrip} ref={strip}>
        {play}
        {months.map(m => (
          <button key={m.ym} type="button" aria-current={cur(m.i)} className={m.i === month ? styles.stripMonthOn : styles.stripMonth}
            title={title(m)} onClick={() => pick(m.i)}>
            {m.ym.endsWith('-01') || m.i === unit.first ? <b>{m.year}.</b> : null}
            {m.name}
            {m.nums && <span className={styles.railEvents}>{m.nums.join(', ')}</span>}
          </button>
        ))}
      </div>
    </nav>
  )
}

// For trying the occupiers' colours on the map (kept in this browser): a colour for each power, how strong the tones
// are, and the values to hand on once they are right
function ZoneColors() {
  const { colors, setColor, toneScale, setToneScale, resetColors } = useMap()
  const values = JSON.stringify({ colors, scale: toneScale })
  return (
    <details className={styles.colorPanel}>
      <summary>Boje okupatora (proba)</summary>
      <div className={styles.colorRows}>
        {POWERS.map(p => (
          <label key={p.key} className={styles.colorRow}>
            <input type="color" value={colors[p.key]} onChange={e => setColor(p.key, e.target.value)} />
            <span>{p.name}</span>
            <code>{colors[p.key]}</code>
            {colors[p.key] !== DEFAULT_COLORS[p.key] && <span className={styles.colorChanged}>promenjeno</span>}
          </label>
        ))}
        <label className={styles.colorRow}>
          <input type="range" min={0.5} max={2.5} step={0.1} value={toneScale} onChange={e => setToneScale(Number(e.target.value))} />
          <span>Jačina tonova: ×{toneScale.toFixed(1)}</span>
        </label>
      </div>
      <div className={styles.colorFoot}>
        <button type="button" className={styles.choiceButton} onClick={resetColors}>Vrati početne</button>
        <code className={styles.colorValues}>{values}</code>
      </div>
    </details>
  )
}

// Under the map: how the keys work, and the occupiers' colours to try
export function BelowSheet() {
  const { variant } = useMap()
  return (
    <div className={styles.below}>
      <p className={styles.keysHint}>
        {variant === 'vreme' ? 'Mesec pomeraju strelice i točkić nad lenjirom. ' : ''}Shift i točkić uvećavaju kartu, a
        prevlačenje mišem je pomera.
      </p>
      <ZoneColors />
    </div>
  )
}
