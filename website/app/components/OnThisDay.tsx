'use client'

import { useEffect, useMemo, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import { MONTHS_GENITIVE, ageAtDeath, parseDeathDay, type DeathDay } from '@/app/lib/deathDay'
import { sqQuotes } from '@/app/lib/typography'
import { SoldierName } from './SoldierResults'
import { SoldierMedals } from './Medal'
import { CandleIcon } from './Icons'

// Dates of capture or wounding are not deaths
const NOT_DEATHS = new Set(['zarobljen', 'ranjen'])
const SHOWN = 6

interface Fallen {
  soldier: Soldier
  year: number
  death: DeathDay
}

// The missing say so, in the word their entry uses: the year is when they went missing
function missingWord(soldier: Soldier): string | null {
  if (!soldier.death_type?.startsWith('nesta')) return null
  return /\bnestala\b/i.test(soldier.additional_info) ? 'Nestala' : 'Nestao'
}

// A candle, then the year and place of death, and how old the soldier was
function DeathLine({ soldier, year, death }: Fallen) {
  const missing = missingWord(soldier)
  const age = ageAtDeath(soldier.birth_year, soldier.additional_info, death)
  return (
    <span className="on-this-day-meta">
      <span className="death-mark" title={missing ? 'Godina i mesto nestanka' : 'Godina i mesto smrti'}>
        <CandleIcon size={14} />
        {!missing && <span className="visually-hidden">Smrt:</span>}
      </span>
      {missing && `${missing} `}
      {year}{soldier.death_place && `, ${soldier.death_place}`}
      {age && (
        <>
          {' · '}
          <b>{age}</b>
        </>
      )}
    </span>
  )
}

// A small seeded shuffle, so the same people are shown all day and others tomorrow
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

interface OnThisDayProps {
  soldiers: Soldier[]
  loading: boolean
  onSelect: (soldier: Soldier) => void
}

// "Na današnji dan": soldiers who fell, died or went missing on today's date during the war
export default function OnThisDay({ soldiers, loading, onSelect }: OnThisDayProps) {
  // Today in the visitor's own calendar, known only in the browser
  const [today, setToday] = useState<{ day: number; month: number; key: string } | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    const now = new Date()
    setToday({ day: now.getDate(), month: now.getMonth() + 1, key: now.toDateString() })
  }, [])

  const fallen = useMemo<Fallen[]>(() => {
    if (!today) return []
    const list: Fallen[] = []
    for (const soldier of soldiers) {
      if (!soldier.death_date || NOT_DEATHS.has(soldier.death_type ?? '')) continue
      const d = parseDeathDay(soldier.death_date)
      if (d && d.day === today.day && d.month === today.month && d.year >= 1941 && d.year <= 1945) {
        list.push({ soldier, year: d.year, death: d })
      }
    }
    return list
  }, [soldiers, today])

  const featured = useMemo(() => {
    if (!today) return []
    // Prefer entries that also say where; the rest only when there aren't enough
    const withPlace = fallen.filter((f) => f.soldier.death_place)
    const pool = withPlace.length >= SHOWN ? withPlace : fallen
    return shuffled(pool, today.key).slice(0, SHOWN)
  }, [fallen, today])

  const everyone = useMemo(
    () => [...fallen].sort((a, b) => a.year - b.year || a.soldier.last_name.localeCompare(b.soldier.last_name, 'sr')),
    [fallen],
  )

  if (!today) return null
  const loaded = !loading && soldiers.length > 0
  if (loaded && fallen.length === 0) return null

  const date = `${today.day}. ${MONTHS_GENITIVE[today.month - 1]}`
  const shown = showAll ? everyone : featured

  return (
    <section className="on-this-day" aria-labelledby="on-this-day-title">
      <div className="section-head">
        <h2 id="on-this-day-title">Na današnji dan</h2>
        <p className="section-note">Borci koji su {date} poginuli, umrli ili nestali u ratu</p>
      </div>

      {!loaded ? (
        <ul className="on-this-day-list is-loading" aria-label="Učitavanje">
          {Array.from({ length: SHOWN }, (_, i) => <li key={i} />)}
        </ul>
      ) : (
        <>
          <ul className={showAll ? 'on-this-day-list is-all' : 'on-this-day-list'}>
            {shown.map((fallen) => { const { soldier } = fallen; return (
              <li key={soldier.soldier_id}>
                <button type="button" className="on-this-day-item" onClick={() => onSelect(soldier)}>
                  <span className="on-this-day-text">
                    <span className="on-this-day-name"><SoldierName soldier={soldier} /></span>
                    <DeathLine {...fallen} />
                    {soldier.unit && <span className="on-this-day-unit">{sqQuotes(soldier.unit)}</span>}
                  </span>
                  <SoldierMedals soldier={soldier} look="gravira" />
                </button>
              </li>
            ) })}
          </ul>
          {fallen.length > SHOWN && (
            <button type="button" className="on-this-day-more" onClick={() => setShowAll((v) => !v)}>
              {showAll ? 'Prikaži manje' : `Prikaži sve za ovaj dan (${fallen.length})`}
            </button>
          )}
        </>
      )}
    </section>
  )
}
