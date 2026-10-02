'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { recordPath } from '@/app/lib/records'
import {
  dayParts, deathDay, lifeSpan, loadPlaces, subunitPath, unitIndex, type Level, type Place, type PlaceMember,
} from '@/app/lib/relations'
import { useLang, useT } from '@/app/i18n/LangContext'
import type { Messages } from '@/app/i18n'
import { unitShortName } from '@/app/i18n/units'
import { ChevronDownIcon } from './Icons'

const SHOWN = 8

/** "1. bataljon" in the page's language; a sub-unit the book names ("3. kordunaški bataljon") as printed */
export function levelLabel(level: Level, t: Messages['kin']): string {
  switch (level.kind) {
    case 'staff': return t.staff
    case 'none': return t.noBattalion
    case undefined: return level.label
    default: return t[level.kind](level.n!)
  }
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
  kicker?: string   // what the label is, before it: "Mesto rođenja" (the village tree groups by birthplace)
  note?: string
  size: number
  leaves: Leaf[]
}

export type KinPart = 'comrades' | 'neighbours'

/** What the record's facts link to: the soldier's own sub-unit, those who fell the same day, his village */
export interface KinCounts {
  unit?: { size: number }      // the deepest sub-unit he is listed in, himself included
  sameDay?: number             // others of the unit who fell the same day
  place?: { others: number }   // others of all units born in his village
}

/** A fact asks a fold to open on one of its groups ("1.516 boraca" opens the sub-unit); nonce: a new request */
export interface KinRequest {
  part: KinPart
  group: 'unit' | 'day' | 'place'
  nonce: number
}

interface Props {
  soldier: Soldier
  unit: Unit
  unitSoldiers?: Soldier[]
  onOpen?: (soldier: Soldier) => void
  part: KinPart                                 // its comrades in the unit, or the people of its village
  request?: KinRequest | null
  onCounts?: (part: KinPart, counts: KinCounts) => void
}

// Where the soldier stood in the unit and who fell with him (comrades), or who came from his village (neighbours):
// a fold at the end of the record that says what is in it, with a small tree per question inside
export default function RelationsTree({ soldier, unit, unitSoldiers, onOpen, part, request, onCounts }: Props) {
  const lang = useLang()
  const messages = useT()
  const t = messages.kin
  const [place, setPlace] = useState<Place | null>(null)
  const [open, setOpen] = useState<string | null>(null)
  const [full, setFull] = useState(false)
  const [folded, setFolded] = useState(true)
  const [flashed, setFlashed] = useState<string | null>(null)
  const sectionRef = useRef<HTMLElement>(null)

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
        if (villageIds.has(s.soldier_id)) tags.push(t.samePlaceTag)
        if (myDay && index?.days.get(s) === myDay) tags.push(t.sameDayTag)
        return { id: s.soldier_id, name: s.full_name, years: lifeSpan(s), soldier: s, tags }
      })
      .sort((a, b) => b.tags.length - a.tags.length || collator.compare(a.name, b.name))
  }

  const unitGroups: Group[] = levels.map((list, depth) => ({
    key: `u:${path[depth].key}`,
    label: levelLabel(path[depth], t),
    size: list.length,
    leaves: toLeaves(list),
  }))

  const dayGroup: Group | null = myDay && sameDay.length > 1 ? {
    key: 'day',
    label: t.sameDay,
    note: [t.day(...dayParts(myDay)), soldier.death_place].filter(Boolean).join(' · '),
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
          label: memberUnit ? unitShortName(memberUnit, lang) : file,
          size: members.length,
          leaves: members
            .filter((m) => m.id !== soldier.soldier_id)
            .map((m) => ({
              id: m.id, name: m.name, years: m.years, soldier: local?.get(m.id), unit: memberUnit,
              tags: deepest && local?.get(m.id) && deepest.includes(local.get(m.id)!) ? [levelLabel(path[path.length - 1], t)] : [],
            }))
            .sort((a, b) => b.tags.length - a.tags.length || collator.compare(a.name, b.name)),
        }
      })
  }, [place, neighbours, unit, unitSoldiers, soldier.soldier_id, collator, path, levels, lang, t])

  const showUnitTree = part === 'comrades' && (unitGroups.length > 0 || dayGroup !== null)
  const showPlaceTree = part === 'neighbours' && place !== null && placeGroups.length > 0
  const deepest = unitGroups[unitGroups.length - 1]
  const others = Math.max(0, neighbours.length - 1)

  // What the record's facts link to, for the counts they show
  const unitSize = deepest?.size ?? 0
  const dayOthers = dayGroup ? dayGroup.size - 1 : 0
  useEffect(() => {
    if (!onCounts) return
    if (part === 'comrades') onCounts(part, { unit: unitSize ? { size: unitSize } : undefined, sameDay: dayOthers || undefined })
    else onCounts(part, { place: showPlaceTree && others ? { others } : undefined })
  }, [onCounts, part, unitSize, dayOthers, showPlaceTree, others])

  // A fact asked this fold to open on a group: open it, scroll to it and flash its row
  const placeKey = placeGroups.length === 1 ? 'place' : null
  useEffect(() => {
    if (!request || request.part !== part) return
    const key = request.group === 'unit' ? deepest?.key : request.group === 'day' ? 'day' : placeKey
    setFolded(false)
    setFull(false)
    if (key) setOpen(key)
    setFlashed(key ?? 'fold')
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    requestAnimationFrame(() => sectionRef.current?.scrollIntoView({ block: 'start', behavior: reduce ? 'auto' : 'smooth' }))
    // only a new request opens the fold; the groups it names are read when it comes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [request?.nonce])

  if (!showUnitTree && !showPlaceTree) return null

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
              <Link href={recordPath(leaf.unit, leaf.id, lang)}><LeafBody leaf={leaf} /></Link>
            ) : (
              <span><LeafBody leaf={leaf} /></span>
            )}
          </li>
        ))}
        {!full && group.leaves.length > SHOWN && (
          <li className="kin-leaf kin-more">
            <button type="button" onClick={() => setFull(true)}>{t.more(group.leaves.length - SHOWN)}</button>
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
        <button type="button" className={`kin-row${flashed === group.key ? ' is-flash' : ''}`} aria-expanded={canOpen ? isOpen : undefined}
          disabled={!canOpen} onClick={() => toggle(group.key)} onAnimationEnd={() => setFlashed(null)}>
          {group.kicker && <span className="kin-kicker">{group.kicker}</span>}
          <span className="kin-label">{group.label}</span>
          {group.note && <span className="kin-note">{group.note}</span>}
          <span className="kin-count">{t.count(group.size)}</span>
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
          {soldier.full_name}</span><span className="kin-note">{t.thisRecord}</span></span></li></ul>
      )
    }
    return <ul>{renderGroup(unitGroups[depth], true, nestPath(depth + 1))}</ul>
  }

  // What the fold holds, before it is opened: "4. bataljon, 1.516 · istog dana 2", "Užička Požega, 5"
  const summary = part === 'comrades'
    ? [deepest ? `${deepest.label}, ${t.count(deepest.size)}` : unitShortName(unit, lang),
      dayGroup ? `${messages.life.sameDayShort} ${t.count(dayGroup.size)}` : null].filter(Boolean).join(' · ')
    : place ? `${placeName(place)}, ${t.count(neighbours.length)}` : ''

  return (
    <section ref={sectionRef} className={`kin record-fold${folded ? '' : ' is-open'}`}
      aria-label={part === 'comrades' ? t.comrades : t.neighbours}>
      <button type="button" className={`record-fold-row${flashed === 'fold' ? ' is-flash' : ''}`} aria-expanded={!folded}
        onClick={() => setFolded((f) => !f)} onAnimationEnd={() => setFlashed(null)}>
        <span className="record-fold-text">
          <span className="record-fold-title">{part === 'comrades' ? t.comrades : t.neighbours}</span>
          <span className="record-fold-summary">{summary}</span>
        </span>
        <ChevronDownIcon size={18} />
      </button>

      {!folded && showUnitTree && (
        <ul className="kin-tree">
          <li className="kin-node kin-root is-path">
            <span className="kin-row">
              <span className="kin-kicker">{t.unit}</span>
              <span className="kin-label">{unitShortName(unit, lang)}</span>
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

      {!folded && showPlaceTree && place && (
        <ul className="kin-tree">
          {placeGroups.length === 1 ? (
            renderGroup({ ...placeGroups[0], key: 'place', label: placeName(place), kicker: t.birthplace, note: undefined }, false)
          ) : (
            <li className="kin-node kin-root">
              <span className="kin-row">
                <span className="kin-kicker">{t.birthplace}</span>
                <span className="kin-label">{placeName(place)}</span>
                <span className="kin-count">{t.count(neighbours.length)}</span>
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
