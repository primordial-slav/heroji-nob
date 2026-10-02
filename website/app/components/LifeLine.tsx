'use client'

import type { LifeEvent, Soldier, SoldierSource } from '@/app/lib/types'
import { units } from '@/app/data/units'
import { isWoman } from '@/app/lib/standIn'
import { useLang, useT } from '@/app/i18n/LangContext'
import type { Messages } from '@/app/i18n'
import { unitShortName } from '@/app/i18n/units'
import { CandleIcon } from './Icons'

/** A unit as its name says it is: "brigade", "division", "detachment" (odred), or "unit" */
export function unitKind(name?: string): string {
  if (!name) return 'unit'
  if (/divizij/i.test(name)) return 'division'
  if (/odred/i.test(name)) return 'detachment'
  if (/brigad/i.test(name)) return 'brigade'
  return 'unit'
}

const parts = (d: string) => d.split('-').map((p) => parseInt(p, 10))

/** Under a step's year: its day ("11. 7.") or month ("decembar"), or a period ("januar – mart", "do 1943") */
function under(e: LifeEvent, t: Messages['life']): string {
  const at = ([, m, d]: number[]) => (d ? t.day(d, m) : m ? t.month(m) : '')
  const start = parts(e.d)
  if (!e.e) return at(start)
  const end = parts(e.e)
  const to = `${at(end)}${end[0] !== start[0] ? ` ${end[0]}` : ''}`.trim()
  return `${at(start)} – ${to}`.trim()
}

const capital = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

interface Props {
  soldier: Soldier
  entries: SoldierSource[]          // entriesOf(soldier): a step's s is its index here
  unitName?: string
  pageOf: (entry: number) => number | undefined
  onShow: (entry: number) => void   // show the entry a step was read from, on its page
}

// "Životni put": the dated steps of a soldier's life, down a line, each one pointing at the entry it was read from
export default function LifeLine({ soldier, entries, unitName, pageOf, onShow }: Props) {
  const lang = useLang()
  const messages = useT()
  const t = messages.life
  const steps = soldier.life_events ?? []
  if (steps.length === 0) return null
  const woman = isWoman(soldier)
  // the entries the steps were read from: one gets a note under the line, several a page on each step
  const read = Array.from(new Set(steps.map((e) => e.s ?? 0)))
  const oneSource = read.length === 1

  // The step's words: the site's own for what every book says alike, the book's own for a duty or a transfer
  const words = (e: LifeEvent): [string, string?] => {
    switch (e.k) {
      case 'born': return [t.born(woman)]
      case 'death': return [t.fate(soldier.death_type, woman)]
      case 'skoj': return [t.skoj]
      case 'kpj': return [t.kpj]
      case 'nob': return [t.nob, e.x]
      case 'unit': {
        // from another unit's book: that unit
        const file = entries[e.s ?? 0]?.unit_file
        const other = file ? units.find((u) => u.dataFile === `/${file}`) : undefined
        return other ? [t.unit(unitKind(other.name)), unitShortName(other, lang)] : [t.unit(unitKind(unitName)), e.x]
      }
      case 'wounded': return [t.wounded(woman), e.x]
      case 'captured': return [t.captured(woman), e.x]
      case 'exchanged': return [t.exchanged(woman), e.x]
      default: return e.x && t.printedLabels ? [capital(e.x)] : [t[e.k], e.x]   // duty, moved, ill, left
    }
  }

  let lastYear = ''
  return (
    <section className="life-line" aria-labelledby="life-title">
      <h3 id="life-title" className="life-title">{t.title}</h3>
      <ol className="life-steps">
        {steps.map((e, i) => {
          const year = e.d.slice(0, 4)
          const repeat = year === lastYear
          lastYear = year
          const [label, detail] = words(e)
          const sub = under(e, t)
          const page = pageOf(e.s ?? 0)
          return (
            <li key={i} className={`life-step${e.k === 'death' ? ' is-end' : ''}`}>
              <span className="life-when">
                <span className={`life-year${repeat ? ' is-repeat' : ''}`}>{year}</span>
                {sub && <span className="life-sub">{sub}</span>}
              </span>
              <button type="button" className="life-what" title={t.show} onClick={() => onShow(e.s ?? 0)}>
                {e.k === 'death' && <span className="life-candle"><CandleIcon size={16} /></span>}
                <span className="life-label">{label}</span>
                {detail && <span className="life-detail">{detail}</span>}
                {!oneSource && page != null && <span className="life-ref">{messages.record.page(page)}</span>}
              </button>
            </li>
          )
        })}
      </ol>
      {oneSource && pageOf(read[0]) != null && (
        <button type="button" className="life-source" onClick={() => onShow(read[0])}>{t.source(pageOf(read[0])!)}</button>
      )}
    </section>
  )
}
