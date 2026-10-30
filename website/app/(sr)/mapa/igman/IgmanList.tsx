'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import { units } from '@/app/data/units'
import { fullRecord, loadRows } from '@/app/lib/searchIndex'
import SoldierResults from '@/app/components/SoldierResults'
import SoldierModal from '@/app/components/LazySoldierModal'
import styles from '../mapa.module.css'
import igman from './igman.json'

type Group = { key: string; title: string; ids: string[] }
type Fate = 'rat' | 'posle' | 'ziv'
type Filter = 'svi' | 'marš' | 'umrli' | Fate
const DATA = igman as { groups: Group[]; marks: Record<string, string[]>; fates: Record<string, Fate> }
const UNIT = units.find((u) => u.id === 'prva-proleterska-brigada')

// a filter's test of one man (scripts/make_igman_list.py gives the marks and what became of each)
const FILTERS: { key: Filter; label: string; test: (id: string) => boolean }[] = [
  { key: 'svi', label: 'Svi', test: () => true },
  { key: 'marš', label: 'Zapis pominje marš', test: (id) => DATA.marks[id]?.includes('igman') ?? false },
  { key: 'umrli', label: 'Umrli posle marša', test: (id) => DATA.marks[id]?.includes('foca') ?? false },
  { key: 'rat', label: 'Poginuli ili umrli kasnije u ratu', test: (id) => DATA.fates[id] === 'rat' },
  { key: 'ziv', label: 'Preživeli rat', test: (id) => DATA.fates[id] !== 'rat' },
]

type State = { status: 'loading' } | { status: 'failed' } | { status: 'ready'; byId: Map<string, Soldier> }

/**
 * The Prva proleterska's men in the column that crossed Igman on the night of 27-28 January 1942, as the brigade's
 * line-up at Rudo and its monograph give them (scripts/make_igman_list.py, igman.json): by battalion, with filters for
 * what the entries say of the march and what became of each.
 */
export default function IgmanList() {
  const [state, setState] = useState<State>({ status: 'loading' })
  const [filter, setFilter] = useState<Filter>('svi')
  const [selected, setSelected] = useState<Soldier | null>(null)
  const opening = useRef<Soldier | null>(null)

  useEffect(() => {
    let live = true
    if (!UNIT) {
      setState({ status: 'failed' })
      return
    }
    loadRows(UNIT, DATA.groups.flatMap((g) => g.ids))
      .then((rows) => live && setState({ status: 'ready', byId: new Map(rows.map((s) => [s.soldier_id, s])) }))
      .catch(() => live && setState({ status: 'failed' }))
    return () => { live = false }
  }, [])

  const all = useMemo(() => DATA.groups.flatMap((g) => g.ids), [])
  const counts = useMemo(() => Object.fromEntries(FILTERS.map((f) => [f.key, all.filter(f.test).length])), [all])

  const openSoldier = async (soldier: Soldier) => {
    opening.current = soldier
    const record = await fullRecord(soldier).catch(() => soldier)
    if (opening.current === soldier) setSelected(record)
  }

  const test = FILTERS.find((f) => f.key === filter)!.test
  const collator = new Intl.Collator('sr-Latn')

  return (
    <>
      <header className={styles.listHead}>
        <p className={styles.listKicker}>Prva proleterska brigada</p>
        <h1 className="page-title">Igmanski marš</h1>
        <p className={styles.listContext}>
          U noći 27. na 28. januara 1942. brigada je od Grabljive Njive prešla Sarajevsko polje, prugu i most na Bosni
          kod Reljeva i Igman do Presjenice: 19 časova hoda, na mrazu od oko 30 stepeni ispod nule. U koloni su bili
          1. bataljon u prethodnici, 2. bataljon, 5. bataljon i sanitet, a 3. bataljon u zaštitnici, sa štabom
          brigade. Mraz je iz stroja izbacio 158 boraca; šest promrzlih umrlo je posle marša, najviše od tetanusa u
          bolnici u Foči.
        </p>
        <p className={styles.listNote}>
          Kako je spisak sastavljen: borci koji su 21. decembra 1941. stajali u stroju u Rudom u tim bataljonima, bez
          3. čete 2. bataljona i Užičke čete 5. bataljona (bile su s Vrhovnim štabom na Jahorini, kao i 4. i
          6. bataljon), i bez onih koji su poginuli pre marša, na Pjenovcu i Bijelim Vodama. Posavska četa
          6. bataljona bila je sa 5. bataljonom na Pjenovcu; knjiga je ne pominje u koloni, ali je njen borac Avram
          Pijade umro u Foči posle marša, pa su njeni borci posebno.
          Ko je u brigadu došao posle Ruda, ili je do marša bio ranjen ili upućen drugde, stroj ne kaže, zato je spisak
          približan; od kasnijih su tu samo oni čiji zapis pominje marš. Izvor: Miloš Vuksanović, Prva proleterska
          brigada (1981), poglavlja „Igmanski marš“ i „Liječenje promrzlih Igmanaca“, i spisak boraca brigade.
        </p>
      </header>

      <div className="units-years" role="group" aria-label="Prikaži" style={{ marginBottom: 'var(--space-6)' }}>
        {FILTERS.map((f) => (
          <button key={f.key} type="button" aria-pressed={filter === f.key} onClick={() => setFilter(f.key)}>
            {f.label} <span className="units-year-count">{counts[f.key]}</span>
          </button>
        ))}
      </div>

      {state.status === 'loading' && (
        <ul className="loading-rows" aria-label="Učitava se spisak">
          {Array.from({ length: 8 }, (_, i) => <li key={i} />)}
        </ul>
      )}
      {state.status === 'failed' && (
        <div className="empty">
          <h2>Spisak se nije učitao</h2>
          <p>Proverite vezu sa internetom i osvežite stranicu.</p>
        </div>
      )}
      {state.status === 'ready' && DATA.groups.map((g) => {
        const members = g.ids.filter(test).map((id) => state.byId.get(id)).filter((s): s is Soldier => !!s)
          .sort((a, b) => collator.compare(a.full_name, b.full_name))
        if (!members.length) return null
        const id = `grupa-${g.key}`
        return (
          <section key={g.key} id={id} style={{ marginBottom: 'var(--space-8)' }}>
            <h2 className={styles.listKicker} style={{ fontSize: 'var(--step-1)', marginBottom: 'var(--space-3)' }}>
              {g.title}
            </h2>
            <SoldierResults results={members} onSelect={openSoldier} scrollTargetId={id} />
          </section>
        )
      })}
      {selected && UNIT && (
        <SoldierModal
          key={selected.soldier_id}
          soldier={selected}
          unitName={selected.unit ?? UNIT.name}
          onOpen={openSoldier}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  )
}
