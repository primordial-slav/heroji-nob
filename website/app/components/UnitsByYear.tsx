'use client'

import Link from 'next/link'
import type { Unit } from '@/app/data/units'
import { formation, formationKey } from '@/app/data/formation'
import type { Lang } from '@/app/i18n/config'
import { formatNumber } from '@/app/i18n/format'
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
  noUnit?: boolean // the soldiers of the books across units who have no unit on the site
  census?: Unit[] // with them, the 1964 census's parts: listed by region beside the card, not as cards of their own
}

// Not units: Ostali borci (the books across units) and its parts for the 1964 census, one a republic or province;
// they stand last, under a heading of their own
const NO_UNIT = 'ostali-borci'
export const isNoUnit = (u: Unit) => u.id === NO_UNIT || u.id.startsWith(`${NO_UNIT}-`)

/** A census part's region, its name after " – " in the page's language: "Ostali borci – Slovenija" -> "Slovenija" */
function regionOf(unit: Unit, lang: Lang): string {
  const name = unitName(unit, lang)
  const cut = name.indexOf(' – ')
  return cut < 0 ? name : name.slice(cut + 3)
}

function groupByYear(all: Unit[]): YearGroup[] {
  const units = all.filter((u) => !isNoUnit(u))
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
  const noUnit = all.filter((u) => u.id === NO_UNIT)
  const census = all.filter((u) => isNoUnit(u) && u.id !== NO_UNIT)
  if (noUnit.length || census.length) groups.push({ year: null, units: noUnit, census, noUnit: true })
  return groups
}

// The units under the year they were formed, oldest first
export default function UnitsByYear({ units }: { units: Unit[] }) {
  const t = useT()
  const lang = useLang()
  const to = useLocalePath()
  return (
    <div className="unit-years">
      {groupByYear(units).map(({ year, units: group, noUnit, census }) => {
        const key = year ?? (noUnit ? 'bez-jedinice' : 'ostale')
        return (
        <section key={key} className="unit-year" aria-labelledby={`godina-${key}`}>
          <h3 className={year ? 'unit-year-head' : 'unit-year-head is-undated'} id={`godina-${key}`}>
            {year ? <span className="unit-year-number">{year}</span> : noUnit ? t.home.noUnit : t.home.otherUnits}
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
            {census && census.length > 0 && (
              // one panel for the census: its eight parts would be eight cards of the same scanned page
              <li className="census-index">
                <div>
                  <h4 className="unit-name">{t.home.census}</h4>
                  <p className="unit-desc">{t.home.censusLead}</p>
                  <ul className="census-parts">
                    {census.map((unit) => (
                      <li key={unit.id}>
                        <Link href={to(`/units/${unit.id}`)} aria-label={`${regionOf(unit, lang)}, ${t.borci(unit.soldierCount)}`}>
                          <span className="census-part-name">{regionOf(unit, lang)}</span>
                          <span className="census-part-count">{formatNumber(lang, unit.soldierCount)}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                  <p className="unit-count">{t.borci(census.reduce((sum, unit) => sum + unit.soldierCount, 0))}</p>
                </div>
              </li>
            )}
          </ul>
        </section>
        )
      })}
    </div>
  )
}
