'use client'

import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import type { SoldierSource } from '@/app/lib/types'
import { cropBox } from '@/app/lib/entryBox'
import { useT } from '@/app/i18n/LangContext'
import { ChevronLeftIcon, ChevronRightIcon, CloseIcon } from './Icons'
import { useLightboxKeys } from './PhotoLightbox'

// Only when it shows: it brings PDF.js
const EntryCrop = lazy(() => import('./EntryCrop'))

// A column's print and a page's are the same size to the eye: pixels to a PDF point, where the strip is wide enough
const PIXELS_PER_POINT = 1.5
// No cut-out shows taller than this; a longer entry opens whole over the page
const TALLEST = 160

// The whole entry over the page: Escape, the X or a click beside it closes it, and only it. A long one scrolls.
function EntryPopup({ src, width, label, onClose }: { src: string; width: number; label: string; onClose: () => void }) {
  const t = useT().record
  const closeRef = useLightboxKeys(onClose)
  return (
    <div className="lightbox lightbox-entry" role="dialog" aria-modal="true" aria-label={label} onClick={onClose}>
      <button ref={closeRef} type="button" className="lightbox-close" onClick={onClose} aria-label={t.close}>
        <CloseIcon size={22} />
      </button>
      <figure className="lightbox-figure" onClick={(e) => e.stopPropagation()}>
        <img src={src} alt="" style={{ width: `min(100%, ${Math.round(width)}px)` }} />
        <figcaption><span className="lightbox-credit">{label}</span></figcaption>
      </figure>
    </div>
  )
}

// The printed line cut from the scan, under the record's facts; a man printed in several books has one to a book, swiped
// through, or stepped through with the arrows on either side of it. Only the books whose scan is on the site are here
// (`entries`: hasPage): one that isn't is named further down, as it always was. Nothing is cut until the strip comes on
// screen, so a record read only for its facts, or stepped past, opens no book, and then only the line shown and the next,
// so a man in six books doesn't load six PDFs at once. Each stands in the middle, in a window as tall as it is, up to
// TALLEST, worked out from the entries' boxes before any is cut; a longer one opens whole with "Ceo zapis" or a click on it.
export default function EntryStrip({ entries, label, onWholePage }: {
  entries: SoldierSource[]
  label: (entry: SoldierSource) => string
  onWholePage: (entry: SoldierSource) => void
}) {
  const t = useT()
  const strip = useRef<HTMLDivElement>(null)
  const [at, setAt] = useState(0)
  const [width, setWidth] = useState(0)
  // The lines cut so far stay cut, so going back shows them at once
  const [cut, setCut] = useState<Set<number>>(() => new Set())
  const [seen, setSeen] = useState(false)
  const [images, setImages] = useState<Record<number, string>>({})
  const [popup, setPopup] = useState<number | null>(null)
  const many = entries.length > 1
  const shown = Math.min(at, entries.length - 1)

  useEffect(() => {
    if (!seen) return
    setCut((done) => (done.has(at + 1) && done.has(at) ? done : new Set([...done, at, at + 1])))
  }, [at, seen])

  useEffect(() => {
    const el = strip.current
    if (!el) return
    const watch = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return
      setSeen(true)
      watch.disconnect()
    })
    watch.observe(el)
    return () => watch.disconnect()
  }, [])

  useEffect(() => {
    const el = strip.current
    if (!el) return
    const measure = () => setWidth(el.clientWidth)
    measure()
    const watch = new ResizeObserver(measure)
    watch.observe(el)
    return () => watch.disconnect()
  }, [])

  const sizes = entries.map((entry) => {
    const box = cropBox(entry)
    const across = Math.min(width, box.width * PIXELS_PER_POINT)
    // and the image's border
    return { width: across, height: Math.ceil((across * box.height) / box.width) + 2, whole: box.width * 2 }
  })

  const goTo = (i: number) => {
    const el = strip.current
    if (!el) return
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    el.scrollTo({ left: i * el.clientWidth, behavior: reduce ? 'auto' : 'smooth' })
  }

  return (
    <section className="record-lead">
      <div className="record-lead-head">
        <h3>{t.record.references}</h3>
        {many && <span className="record-lead-count">{t.record.stepOf(shown + 1, entries.length)}</span>}
      </div>
      <div className="record-lead-foot">
        <span>{label(entries[shown])}</span>
        <span className="record-lead-links">
          {sizes[shown].height > TALLEST && (
            <button type="button" className="record-fact-link" disabled={!images[shown]} onClick={() => setPopup(shown)}>
              {t.record.wholeEntry}<ChevronRightIcon size={14} />
            </button>
          )}
          <button type="button" className="record-fact-link" onClick={() => onWholePage(entries[shown])}>
            {t.record.wholePage}<ChevronRightIcon size={14} />
          </button>
        </span>
      </div>
      <div className={`record-lead-stage${many ? ' has-steps' : ''}`}>
        {many && (
          <button type="button" className="record-lead-step" aria-label={t.record.previous} disabled={shown === 0} onClick={() => goTo(shown - 1)}>
            <ChevronLeftIcon size={16} />
          </button>
        )}
        <div
          ref={strip}
          className="record-lead-strip"
          style={{ height: Math.min(TALLEST, sizes[shown].height) }}
          onScroll={(e) => {
            const el = e.currentTarget
            if (el.clientWidth) setAt(Math.round(el.scrollLeft / el.clientWidth))
          }}
        >
          {entries.map((entry, i) => (
            <div key={`${entry.pdf_file}#${entry.pdf_page}#${entry.pdf_y}`} className="record-lead-slide">
              <div
                className={`record-lead-crop${sizes[i].height > TALLEST ? ' is-longer' : ''}`}
                style={{ width: sizes[i].width, height: Math.min(TALLEST, sizes[i].height) }}
                onClick={() => { if (images[i]) setPopup(i) }}
              >
                {cut.has(i) ? (
                  <Suspense fallback={<div className="entry-crop-loading" />}>
                    <EntryCrop entry={entry} onImage={(src) => setImages((old) => ({ ...old, [i]: src }))} />
                  </Suspense>
                ) : <div className="entry-crop-loading" />}
              </div>
            </div>
          ))}
        </div>
        {many && (
          <button type="button" className="record-lead-step" aria-label={t.record.next} disabled={shown === entries.length - 1} onClick={() => goTo(shown + 1)}>
            <ChevronRightIcon size={16} />
          </button>
        )}
      </div>
      {popup !== null && images[popup] && (
        <EntryPopup src={images[popup]} width={sizes[popup].whole} label={label(entries[popup])} onClose={() => setPopup(null)} />
      )}
    </section>
  )
}
