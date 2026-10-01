'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { recordPath } from '@/app/lib/records'
import {
  count, deathDay, formatDay, lifeSpan, loadPlaces, subunitPath, unitIndex, type Place, type PlaceMember,
} from '@/app/lib/relations'

const SHOWN = 8
// The village tree groups soldiers by where they were born (the record's "Mesto rođenja"), not where they fell
const BIRTHPLACE = 'Mesto rođenja'
const UNIT = 'Jedinica'

/** 'Prva lička proleterska brigada "Marko Orešković"' -> 'Prva lička proleterska brigada' */
export function shortUnitName(name: string): string {
  return name.split(/\s+["„]/)[0]
}

interface Leaf {
  id: string
  name: string
  years: string
  soldier?: Soldier          // in the open unit: opens in this dialog
  unit?: Unit                // elsewhere: a link to the record
  tags: string[]
}

interface Group {
  key: string
  label: string
  kicker?: string   // what the label is, before it: "Mesto rođenja"
  note?: string
  size: number
  leaves: Leaf[]
}

interface Props {
  soldier: Soldier
  unit: Unit
  unitSoldiers?: Soldier[]
  onOpen?: (soldier: Soldier) => void
}

// Where the soldier stood in the unit, who fell with him, and who came from his village: a small tree per question
export default function RelationsTree({ soldier, unit, unitSoldiers, onOpen }: Props) {
  const [place, setPlace] = useState<Place | null>(null)
  const [open, setOpen] = useState<string | null>(null)
  const [full, setFull] = useState(false)

  useEffect(() => {
    let live = true
    loadPlaces().then((index) => { if (live) setPlace(index.byId.get(soldier.soldier_id) ?? null) }).catch(() => {})
    return () => { live = false }
  }, [soldier.soldier_id])

  // The soldier's own records in other units' books (a link): him, not a neighbour
  const linkedSelf = useMemo(
    () => new Set((soldier.other_sources ?? []).filter((o) => o.unit_file && o.soldier_id).map((o) => o.soldier_id!)),
    [soldier])
  const neighbours = useMemo(() => place?.members.filter((m) => !linkedSelf.has(m.id)) ?? [], [place, linkedSelf])
  const villageIds = useMemo(() => new Set(neighbours.map((m) => m.id)), [neighbours])
  const collator = useMemo(() => new Intl.Collator('sr-Latn'), [])

  const { path, levels, sameDay, day } = useMemo(() => {
    const path = subunitPath(soldier.unit_detail)
    const day = deathDay(soldier)
    if (!unitSoldiers) return { path, levels: [] as Soldier[][], sameDay: [] as Soldier[], day }
    const index = unitIndex(unitSoldiers)
    const levels = path.map((_, depth) => unitSoldiers.filter((s) => {
      const p = index.paths.get(s)!
      return p.length > depth && p.slice(0, depth + 1).every((l, i) => l.key === path[i].key)
    }))
    const sameDay = day ? unitSoldiers.filter((s) => index.days.get(s) === day) : []
    return { path, levels, sameDay, day }
  }, [soldier, unitSoldiers])

  const myDay = day
  const toLeaves = (list: Soldier[]): Leaf[] => {
    const index = unitSoldiers ? unitIndex(unitSoldiers) : null
    return list
      .filter((s) => s.soldier_id !== soldier.soldier_id)
      .map((s) => {
        const tags: string[] = []
        if (villageIds.has(s.soldier_id)) tags.push('isto mesto')
        if (myDay && index?.days.get(s) === myDay) tags.push('isti dan')
        return { id: s.soldier_id, name: s.full_name, years: lifeSpan(s), soldier: s, tags }
      })
      .sort((a, b) => b.tags.length - a.tags.length || collator.compare(a.name, b.name))
  }

  const unitGroups: Group[] = levels.map((list, depth) => ({
    key: `u:${path[depth].key}`,
    label: path[depth].label,
    size: list.length,
    leaves: toLeaves(list),
  }))

  const dayGroup: Group | null = myDay && sameDay.length > 1 ? {
    key: 'day',
    label: 'Stradali istog dana',
    note: [formatDay(myDay), soldier.death_place].filter(Boolean).join(' · '),
    size: sameDay.length,
    leaves: toLeaves(sameDay),
  } : null

  // Neighbours: the soldier's own unit first, then the other units by size
  const placeGroups: Group[] = useMemo(() => {
    if (!place) return []
    const byFile = new Map<string, PlaceMember[]>()
    for (const m of neighbours) byFile.set(m.file, [...(byFile.get(m.file) ?? []), m])
    const own = unit.dataFile.replace(/^\//, '')
    return Array.from(byFile.entries())
      .sort(([a, x], [b, y]) => Number(b === own) - Number(a === own) || y.length - x.length)
      .map(([file, members]) => {
        const memberUnit = units.find((u) => u.dataFile === `/${file}`)
        const local = file === own && unitSoldiers ? new Map(unitSoldiers.map((s) => [s.soldier_id, s])) : null
        const deepest = levels[levels.length - 1]
        return {
          key: `p:${file}`,
          label: memberUnit ? shortUnitName(memberUnit.name) : file,
          size: members.length,
          leaves: members
            .filter((m) => m.id !== soldier.soldier_id)
            .map((m) => ({
              id: m.id, name: m.name, years: m.years, soldier: local?.get(m.id), unit: memberUnit,
              tags: deepest && local?.get(m.id) && deepest.includes(local.get(m.id)!) ? [path[path.length - 1].label] : [],
            }))
            .sort((a, b) => b.tags.length - a.tags.length || collator.compare(a.name, b.name)),
        }
      })
  }, [place, neighbours, unit, unitSoldiers, soldier.soldier_id, collator, path, levels])

  const showUnitTree = unitGroups.length > 0 || dayGroup !== null
  if (!showUnitTree && placeGroups.length === 0) return null

  const toggle = (key: string) => {
    setOpen((k) => (k === key ? null : key))
    setFull(false)
  }

  const renderLeaves = (group: Group) => {
    const shown = full ? group.leaves : group.leaves.slice(0, SHOWN)
    return (
      <ul className={`kin-leaves${full && group.leaves.length > SHOWN ? ' is-full' : ''}`}>
        {shown.map((leaf) => (
          <li key={leaf.id} className="kin-leaf">
            {leaf.soldier && onOpen ? (
              <button type="button" onClick={() => onOpen(leaf.soldier!)}>
                <LeafBody leaf={leaf} />
              </button>
            ) : leaf.unit ? (
              <Link href={recordPath(leaf.unit, leaf.id)}><LeafBody leaf={leaf} /></Link>
            ) : (
              <span><LeafBody leaf={leaf} /></span>
            )}
          </li>
        ))}
        {!full && group.leaves.length > SHOWN && (
          <li className="kin-leaf kin-more">
            <button type="button" onClick={() => setFull(true)}>još {count(group.leaves.length - SHOWN)}</button>
          </li>
        )}
      </ul>
    )
  }

  const renderGroup = (group: Group, onPath: boolean, children?: React.ReactNode) => {
    const isOpen = open === group.key
    const canOpen = group.leaves.length > 0
    return (
      <li className={`kin-node${onPath ? ' is-path' : ''}${isOpen ? ' is-open' : ''}`} key={group.key}>
        <button type="button" className="kin-row" aria-expanded={canOpen ? isOpen : undefined}
          disabled={!canOpen} onClick={() => toggle(group.key)}>
          {group.kicker && <span className="kin-kicker">{group.kicker}</span>}
          <span className="kin-label">{group.label}</span>
          {group.note && <span className="kin-note">{group.note}</span>}
          <span className="kin-count">{count(group.size)}</span>
        </button>
        {children}
        {isOpen && renderLeaves(group)}
      </li>
    )
  }

  // the unit path, nested: brigade > battalion > company > the soldier
  const nestPath = (depth: number): React.ReactNode => {
    if (depth === unitGroups.length) {
      return (
        <ul><li className="kin-node is-path is-self"><span className="kin-row"><span className="kin-label">
          {soldier.full_name}</span><span className="kin-note">ovaj zapis</span></span></li></ul>
      )
    }
    return <ul>{renderGroup(unitGroups[depth], true, nestPath(depth + 1))}</ul>
  }

  return (
    <section className="kin" aria-label="Saborci i zemljaci">
      {showUnitTree && <div className="modal-source-head"><h3>Saborci</h3></div>}
      {showUnitTree && (
        <ul className="kin-tree">
          <li className="kin-node kin-root is-path">
            <span className="kin-row">
              <span className="kin-kicker">{UNIT}</span>
              <span className="kin-label">{shortUnitName(unit.name)}</span>
            </span>
            {unitGroups.length > 0 || dayGroup ? (
              <ul>
                {unitGroups.length > 0 && renderGroup(unitGroups[0], true, nestPath(1))}
                {dayGroup && renderGroup(dayGroup, false)}
              </ul>
            ) : null}
          </li>
        </ul>
      )}

      {place && placeGroups.length > 0 && <div className="modal-source-head"><h3>Zemljaci</h3></div>}
      {place && placeGroups.length > 0 && (
        <ul className="kin-tree">
          {placeGroups.length === 1 ? (
            renderGroup({ ...placeGroups[0], key: 'place', label: placeName(place), kicker: BIRTHPLACE, note: undefined }, false)
          ) : (
            <li className="kin-node kin-root">
              <span className="kin-row">
                <span className="kin-kicker">{BIRTHPLACE}</span>
                <span className="kin-label">{placeName(place)}</span>
                <span className="kin-count">{count(neighbours.length)}</span>
              </span>
              <ul>{placeGroups.map((g) => renderGroup(g, false))}</ul>
            </li>
          )}
        </ul>
      )}
    </section>
  )
}

function placeName(place: Place): string {
  return place.municipality ? `${place.village}, ${place.municipality}` : place.village
}

function LeafBody({ leaf }: { leaf: Leaf }) {
  return (
    <>
      <span className="kin-leaf-name">{leaf.name}</span>
      {leaf.years && <span className="kin-leaf-years">{leaf.years}</span>}
      {leaf.tags.map((t) => <span key={t} className="kin-tag">{t}</span>)}
    </>
  )
}
