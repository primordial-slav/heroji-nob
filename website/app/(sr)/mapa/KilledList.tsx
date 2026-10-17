'use client'

import { useEffect, useRef, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import { units, type Unit } from '@/app/data/units'
import { unitByName } from '@/app/lib/records'
import { fullRecord, loadUnitList, loadedUnitList } from '@/app/lib/searchIndex'
import { deathDay } from '@/app/lib/relations'
import SoldierResults from '@/app/components/SoldierResults'
import SoldierModal from '@/app/components/SoldierModal'
import styles from './mapa.module.css'
import { YEARS, day, monthName, yearOf } from './geometry'
import { UNIT_ROUTES, type UnitRoute } from './units'

type Ready = {
  status: 'ready'
  route: UnitRoute
  unit: Unit
  title: string          // the month, the year, or the place
  period: string | null  // for a place: when ("januar 1945.", "1944.", "u celom ratu")
  members: Soldier[]
}
type State = { status: 'loading' } | { status: 'missing' } | { status: 'failed' } | Ready

/**
 * The soldiers behind a count of the killed on the map, opened from it in a new tab:
 * /mapa/spisak?jedinica=<route key>&mesec=1945-01, or a place (an index into the unit's FALLEN) in a month, a year
 * or the whole war: &mesto=12[&mesec=..|&godina=1944]. The ids are the ones the map counted
 * (scripts/make_unit_route.py), so the list is as long as the count.
 */
export default function KilledList() {
  const [state, setState] = useState<State>({ status: 'loading' })
  const [selected, setSelected] = useState<Soldier | null>(null)
  const opening = useRef<Soldier | null>(null)

  useEffect(() => {
    let live = true
    const q = new URLSearchParams(window.location.search)
    const route = UNIT_ROUTES.find(u => u.key === q.get('jedinica'))
    const month = q.get('mesec')
    const year = (YEARS as readonly string[]).includes(q.get('godina') ?? '') ? q.get('godina') : null
    const spotParam = q.get('mesto')
    const spot = spotParam === null ? null : Number(spotParam)
    if (!route || (spot !== null && !route.FALLEN[spot])) {
      setState({ status: 'missing' })
      return
    }
    const inPeriod = (m: string) => (month ? m === month : year ? yearOf(day(m)) === year : true)

    const load = async (): Promise<State> => {
      const killed = await route.killed()
      const unit = units.find(u => u.dataFile === killed.DATA_FILE)
      if (!unit) return { status: 'missing' }
      const byMonth = spot === null ? killed.KILLED_BY_MONTH : killed.KILLED_AT[spot]
      const ids = Object.entries(byMonth).filter(([m]) => inPeriod(m)).flatMap(([, list]) => list)
      const list = await loadUnitList(unit)
      const byId = new Map(list.map(s => [s.soldier_id, s]))
      const collator = new Intl.Collator('sr-Latn')
      // in the order they fell, a day's dead by name; those the record gives only a month for after the days
      const members = ids.map(id => byId.get(id)).filter((s): s is Soldier => Boolean(s))
        .map(s => ({ s, d: deathDay(s) ?? '9' }))
        .sort((a, b) => a.d.localeCompare(b.d) || collator.compare(a.s.full_name, b.s.full_name))
        .map(x => x.s)
      const when = month ? monthName(month) : year ? `${year}.` : null
      return spot === null
        ? { status: 'ready', route, unit, title: when ?? 'Ceo rat', period: null, members }
        : { status: 'ready', route, unit, title: route.FALLEN[spot].place, period: when ?? 'u celom ratu', members }
    }

    load()
      .then(next => live && setState(next))
      .catch(() => live && setState({ status: 'failed' }))
    return () => { live = false }
  }, [])

  // the list has what search shows; the dialog gets the soldier's full record
  const openSoldier = async (soldier: Soldier) => {
    opening.current = soldier
    const record = await fullRecord(soldier).catch(() => soldier)
    if (opening.current === soldier) setSelected(record)
  }

  if (state.status === 'loading') {
    return (
      <ul className="loading-rows" aria-label="Učitava se spisak">
        {Array.from({ length: 8 }, (_, i) => <li key={i} />)}
      </ul>
    )
  }
  if (state.status !== 'ready') {
    return (
      <div className="empty">
        <h2>{state.status === 'missing' ? 'Ovaj spisak ne postoji' : 'Spisak se nije učitao'}</h2>
        <p>{state.status === 'missing'
          ? 'Link je možda nepotpun. Otvorite kartu i kliknite broj poginulih.'
          : 'Proverite vezu sa internetom i osvežite stranicu.'}</p>
      </div>
    )
  }

  const { route, unit, title, period, members } = state
  const selectedUnit = selected ? unitByName(selected.unit) : undefined
  return (
    <>
      <header className={styles.listHead}>
        <p className={styles.listKicker}>Poginuli</p>
        <h1 className="page-title">{title}</h1>
        <p className={styles.listContext}>{[route.name, period].filter(Boolean).join(', ')}</p>
        <p className={styles.listNote}>
          Kako ih broji karta: borci brigade za koje spisak daje mesto i mesec pogibije. Nestali, umrli i oni bez
          datuma nisu u spisku.
        </p>
      </header>
      <div id="results">
        <SoldierResults results={members} onSelect={openSoldier} scrollTargetId="results" />
      </div>
      {selected && (
        <SoldierModal
          key={selected.soldier_id}
          soldier={selected}
          unitName={selected.unit ?? unit.name}
          unitSoldiers={selectedUnit ? loadedUnitList(selectedUnit) : undefined}
          onOpen={openSoldier}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  )
}
