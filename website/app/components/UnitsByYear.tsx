'use client'

import Link from 'next/link'
import type { Unit } from '@/app/data/units'
import { formation, formationKey } from '@/app/data/formation'
import { useLang, useLocalePath, useT } from '@/app/i18n/LangContext'
import { unitDescription, unitName } from '@/app/i18n/units'
import { unitImageProps } from '@/app/lib/unitImage'

// How wide a card's photo is drawn (.unit-grid in .container, globals.css): one column up to 711px
// (the page's side padding is 16px a side up to 640px, 24px above), two columns of at least 20rem
// with a 24px gap from 712px, three from 1056px, and the 72rem page caps them at 352px from 1152px.
const CARD_SIZES =
  '(max-width: 640px) calc(100vw - 32px), (max-width: 711px) calc(100vw - 48px), ' +
  '(max-width: 1055px) calc(50vw - 36px), (max-width: 1151px) calc(33.34vw - 32px), 352px'

interface YearGroup {
  year: string | null // null: units whose formation date isn't recorded yet
  units: Unit[]
}

function groupByYear(units: Unit[]): YearGroup[] {
  const dated = units
    .filter((u) => formation[u.id])
    .sort((a, b) => formationKey(formation[a.id].date) - formationKey(formation[b.id].date))
  const groups: YearGroup[] = []
  for (const unit of dated) {
    const year = formation[unit.id].date.slice(0, 4)
    const last = groups[groups.length - 1]
    if (last && last.year === year) last.units.push(unit)
    else groups.push({ year, units: [unit] })
  }
  const undated = units.filter((u) => !formation[u.id])
  if (undated.length) groups.push({ year: null, units: undated })
  return groups
}

// The units under the year they were formed, oldest first
export default function UnitsByYear({ units }: { units: Unit[] }) {
  const t = useT()
  const lang = useLang()
  const to = useLocalePath()
  return (
    <div className="unit-years">
      {groupByYear(units).map(({ year, units: group }) => (
        <section key={year ?? 'ostale'} className="unit-year" aria-labelledby={`godina-${year ?? 'ostale'}`}>
          <h3 className={year ? 'unit-year-head' : 'unit-year-head is-undated'} id={`godina-${year ?? 'ostale'}`}>
            {year ? <span className="unit-year-number">{year}</span> : t.home.otherUnits}
          </h3>
          <ul className="unit-grid">
            {group.map((unit) => (
              <li key={unit.id}>
                <Link href={to(`/units/${unit.id}`)} className="unit-card">
                  <div className="unit-card-photo">
                    <img loading="lazy" {...unitImageProps(unit.image, CARD_SIZES)} alt="" />
                  </div>
                  <div className="unit-card-body">
                    <h4 className="unit-name">{unitName(unit, lang)}</h4>
                    <p className="unit-desc">{unitDescription(unit, lang)}</p>
                    <p className="unit-count">{t.borci(unit.soldierCount)}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
