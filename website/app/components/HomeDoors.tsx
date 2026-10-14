'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { units } from '@/app/data/units'
import { sources } from '@/app/data/sources'
import index from '@/app/data/portrait-index.json'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import { isNoUnit } from '@/app/components/UnitsByYear'
import { photoOf } from '@/app/components/PortraitRails'
import { unitImageProps } from '@/app/lib/unitImage'
import { useLocalePath, useT } from '@/app/i18n/LangContext'

// The home page's ways into the archive, after "Na današnji dan": the units (their own page, /jedinice), the
// photographs (Galerija) and the books (Izvori). Each door shows a few of what it leads to, in a new choice on
// every visit, as the margins do.

const UNITS = units.filter((u) => !isNoUnit(u))
const UNIT_PHOTOS = UNITS.filter((u) => !u.image.includes('pdf-thumbs'))
const FACES = WARTIME_PORTRAITS.filter((id) => photoOf(id))
const PHOTO_COUNT = Object.values(index as Record<string, { same?: string }>).filter((p) => !p.same).length
const BOOKS = sources.filter((s) => s.thumbnail)

// A door's picture is a quarter of a card's (.unit-grid: one column on phones, at most 352px from 1152px)
const PIC_SIZES = '(max-width: 640px) 25vw, 180px'

// `n` of a list: the first ones while the page is drawn on the server, a random choice once it is in the browser
function pick<T>(list: T[], n: number, shuffled: boolean): T[] {
  if (!shuffled) return list.slice(0, n)
  const copy = [...list]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy.slice(0, n)
}

export default function HomeDoors() {
  const t = useT().home.doors
  const to = useLocalePath()
  const [choice, setChoice] = useState(() => ({
    units: pick(UNIT_PHOTOS, 4, false), faces: pick(FACES, 6, false), books: pick(BOOKS, 3, false),
  }))
  useEffect(() => setChoice({ units: pick(UNIT_PHOTOS, 4, true), faces: pick(FACES, 6, true), books: pick(BOOKS, 3, true) }), [])

  return (
    <section className="doors" aria-labelledby="doors-title">
      <h2 className="unit-year-head is-undated" id="doors-title">{t.title}</h2>
      <ul className="unit-grid doors-grid">
        <li>
          <Link href={to('/jedinice')} className="unit-card door">
            <div className="unit-card-photo door-pics door-units" aria-hidden="true">
              {choice.units.map((unit) => (
                <img key={unit.id} loading="lazy" {...unitImageProps(unit.image, PIC_SIZES)} alt="" />
              ))}
            </div>
            <div className="unit-card-body">
              <h3 className="unit-name">{t.units}</h3>
              <p className="unit-desc">{t.unitsText}</p>
              <p className="unit-count">{t.unitsCount(UNITS.length)}</p>
            </div>
          </Link>
        </li>
        <li>
          <Link href={to('/galerija')} className="unit-card door">
            <div className="unit-card-photo door-pics door-faces" aria-hidden="true">
              {choice.faces.map((id) => {
                const face = photoOf(id)!
                return <img key={id} loading="lazy" src={face.src} alt="" style={{ objectPosition: `50% ${face.focus}%` }} />
              })}
            </div>
            <div className="unit-card-body">
              <h3 className="unit-name">{t.photos}</h3>
              <p className="unit-desc">{t.photosText}</p>
              <p className="unit-count">{t.photosCount(PHOTO_COUNT)}</p>
            </div>
          </Link>
        </li>
        <li>
          <Link href={to('/izvori')} className="unit-card door">
            <div className="unit-card-photo door-pics door-books" aria-hidden="true">
              {choice.books.map((book) => <img key={book.id} loading="lazy" src={book.thumbnail} alt="" />)}
            </div>
            <div className="unit-card-body">
              <h3 className="unit-name">{t.books}</h3>
              <p className="unit-desc">{t.booksText}</p>
              <p className="unit-count">{t.booksCount(sources.length)}</p>
            </div>
          </Link>
        </li>
      </ul>
    </section>
  )
}
