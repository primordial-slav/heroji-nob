'use client'

import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import type { Soldier, SoldierSource } from '@/app/lib/types'
import { SoldierName } from './SoldierResults'
import { ChevronLeftIcon, ChevronRightIcon, CloseIcon } from './Icons'
import { sqQuotes } from '@/app/lib/typography'
import { entriesOf, hasPage, recordDetails, sourceTitle, unitByName } from '@/app/lib/records'
import { units } from '@/app/data/units'
import { photoPosition } from '@/app/data/photoFocus'
import RecordActions from './RecordActions'
import { SoldierMedals, honoursLine } from './Medal'
import { wasDelivered } from '@/app/lib/formsubmit'
import KnowSoldierForm from './KnowSoldierForm'
import FamilyStory from './FamilyStory'
import { contributionsFor } from '@/app/data/family'
import RelationsTree from './RelationsTree'

// Lazy-load PdfViewer so PDF.js (~500KB) is not in the initial bundle
const PdfViewer = lazy(() => import('./PdfViewer'))

/** A short name for the book switch: "spisak poginulih" from "Brodska brigada — spisak poginulih" */
function shortTitle(entry: SoldierSource): string {
  const title = sourceTitle(entry)
  const part = title.includes(' — ') ? title.split(' — ').pop()! : title
  return part.charAt(0).toUpperCase() + part.slice(1)
}

interface SoldierModalProps {
  soldier: Soldier
  unitName?: string
  // The soldier's unit list, for the comrades tree; a name there opens in this dialog through onOpen
  unitSoldiers?: Soldier[]
  onOpen?: (soldier: Soldier) => void
  onClose: () => void
}

export default function SoldierModal({ soldier, unitName, unitSoldiers, onOpen, onClose }: SoldierModalProps) {
  // The soldier's own entry, then the same soldier's entries in the unit's other books
  const entries: SoldierSource[] = entriesOf(soldier)
  const pages = entries.filter(hasPage)
  const [shownPage, setShownPage] = useState(0)
  const page = pages[Math.min(shownPage, pages.length - 1)]
  const pageLabels = pages.map(shortTitle)
  const switchLabels = pages.map((e, i) =>
    pageLabels.indexOf(pageLabels[i]) !== pageLabels.lastIndexOf(pageLabels[i]) ? `${pageLabels[i]}, str. ${e.pdf_page}` : pageLabels[i])
  const sourceHref = page?.pdf_file ? `/izvori#${page.pdf_file.replace('.pdf', '')}` : undefined
  const unit = unitName || soldier.unit
  const unitRecord = unitByName(unit)
  // the units of the soldier's entries from other units' books (a link): he is listed in each of them
  const unitOf = (e: SoldierSource) => units.find((u) => u.dataFile === `/${e.unit_file}`)?.name
  const allUnits = [unit, ...entries.map((e) => (e.unit_file ? unitOf(e) : undefined))]
    .filter((u, i, list): u is string => Boolean(u) && list.indexOf(u) === i)

  const [showReportForm, setShowReportForm] = useState(false)
  const [reportText, setReportText] = useState('')
  const [reportStatus, setReportStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const dialogRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  // The entries before and after this one in the unit's list, which is in the order of the books
  const at = unitSoldiers ? unitSoldiers.findIndex((s) => s.soldier_id === soldier.soldier_id) : -1
  const previous = onOpen && at > 0 ? unitSoldiers![at - 1] : undefined
  const next = onOpen && at >= 0 ? unitSoldiers![at + 1] : undefined
  const stepRef = useRef({ previous, next, onOpen })
  stepRef.current = { previous, next, onOpen }

  // Close on Escape, step through the list with the arrow keys, keep the page behind from scrolling,
  // and move focus into the dialog
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseRef.current()
      if ((e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return
      const target = e.target
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest('input, textarea, select'))) return
      const { previous, next, onOpen } = stepRef.current
      const to = e.key === 'ArrowLeft' ? previous : next
      if (to && onOpen) {
        e.preventDefault()
        onOpen(to)
      }
    }
    document.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialogRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      previousFocus?.focus()
    }
  }, [])

  const handleReport = async () => {
    if (!reportText.trim()) return
    setReportStatus('sending')
    try {
      const res = await fetch(`https://formsubmit.co/ajax/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          _subject: `Prijava greške: ${soldier.full_name} (${soldier.soldier_id})`,
          Borac: soldier.full_name,
          ID: soldier.soldier_id,
          Jedinica: unit || '',
          'Opis greške': reportText,
        }),
      })
      setReportStatus((await wasDelivered(res)) ? 'sent' : 'error')
    } catch {
      setReportStatus('error')
    }
  }

  const filled = recordDetails(soldier)
  const honours = honoursLine(soldier)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={dialogRef}
        className="modal-content"
        role="dialog"
        aria-modal="true"
        aria-labelledby="soldier-name"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label="Zatvori">
          <CloseIcon size={22} />
        </button>

        {unitRecord && !unitRecord.image.includes('/pdf-thumbs/') && (
          <div className="record-photo">
            <img src={unitRecord.image} alt="" style={{ objectPosition: photoPosition(unitRecord.id) }} />
          </div>
        )}
        <SoldierMedals soldier={soldier} look="foto" className="modal-medals" />
        <h2 className="modal-title" id="soldier-name"><SoldierName soldier={soldier} /></h2>
        {allUnits.length > 0 && <p className="modal-unit">{allUnits.map(sqQuotes).join(' · ')}</p>}
        {honours && <p className="modal-honours">{honours}</p>}
        <RecordActions soldier={soldier} unit={unitRecord} />
        <FamilyStory items={contributionsFor(soldier.soldier_id, (soldier.other_sources ?? []).map((o) => o.soldier_id))} />

        {entries.length === 1 && soldier.additional_info && (
          <p className="modal-entry">{soldier.additional_info}</p>
        )}

        {entries.length > 1 && (
          <ol className="modal-sources" aria-label="Zapisi u knjigama">
            {entries.map((e, i) => (
              <li key={i} className="modal-source-entry">
                <p className="modal-source-label">
                  {e.unit_file && unitOf(e) && <>{sqQuotes(unitOf(e)!)}: </>}
                  {sourceTitle(e)}
                  {e.pdf_page != null && `, str. ${e.pdf_page}`}
                  {e.name && e.name !== soldier.full_name && <>. Ime u knjizi: {e.name}</>}
                </p>
                {e.additional_info && <p className="modal-entry">{e.additional_info}</p>}
              </li>
            ))}
          </ol>
        )}

        {filled.length > 0 && (
          <dl className="modal-details">
            {filled.map(([label, value]) => (
              <div key={label} style={{ display: 'contents' }}>
                <dt className="modal-label">{label}</dt>
                <dd className="modal-value">{value}</dd>
              </div>
            ))}
          </dl>
        )}

        {unitRecord && (
          <RelationsTree soldier={soldier} unit={unitRecord} unitSoldiers={unitSoldiers} onOpen={onOpen} />
        )}

        {page && (
          <>
            <div className="modal-source-head">
              <h3>Reference</h3>
              {pages.length > 1 && (
                <div className="modal-source-switch" role="group" aria-label="Knjiga">
                  {pages.map((e, i) => (
                    <button
                      key={i}
                      type="button"
                      aria-pressed={e === page}
                      onClick={() => setShownPage(i)}
                    >
                      {switchLabels[i]}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <Suspense fallback={<div className="pdf-viewer-loading">Učitavanje strane…</div>}>
              <PdfViewer
                key={`${page.pdf_file}#${page.pdf_page}#${page.pdf_y}`}
                pdfFile={`/pdfs/${page.pdf_file}`}
                pageNumber={page.pdf_page!}
                yPosition={page.pdf_y ?? 0}
                yPositionEnd={page.pdf_y_end}
                xPosition={page.pdf_x ?? 0}
                xPositionLeft={page.pdf_x_left}
                xPositionEnd={page.pdf_x_end}
                rects={page.pdf_rects}
                sourceHref={sourceHref}
              />
            </Suspense>
          </>
        )}

        {!page && soldier.source_url && (
          <>
            <div className="modal-source-head">
              <h3>Izvor</h3>
            </div>
            <p className="modal-source-note">
              Za ovaj spisak nema skenirane knjige: objavljen je kao tekst na{' '}
              <a href={soldier.source_url} target="_blank" rel="noopener noreferrer">znaci.org</a>.
            </p>
          </>
        )}

        <KnowSoldierForm soldier={soldier} unit={unitRecord} />

        {!showReportForm && reportStatus === 'idle' && (
          <button className="report-error-link" onClick={() => setShowReportForm(true)}>
            Vidite grešku u ovom zapisu? Prijavite je
          </button>
        )}

        {showReportForm && reportStatus === 'idle' && (
          <div className="report-form">
            <label htmlFor="report-text">Šta nije tačno?</label>
            <textarea
              id="report-text"
              className="report-textarea"
              placeholder="Na primer: prezime je u knjizi Adžić, a ovde piše Adzić."
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              rows={3}
              maxLength={2000}
            />
            <div className="report-actions">
              <button className="btn btn-primary" onClick={handleReport} disabled={!reportText.trim()}>
                Pošalji prijavu
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => { setShowReportForm(false); setReportText('') }}
              >
                Otkaži
              </button>
            </div>
          </div>
        )}

        {reportStatus === 'sending' && <p className="report-status">Slanje…</p>}
        {reportStatus === 'sent' && (
          <p className="report-status report-success">Hvala, prijava je poslata. Proverićemo zapis u knjizi.</p>
        )}
        {reportStatus === 'error' && (
          <p className="report-status report-error-msg">
            Prijava nije poslata. Proverite internet vezu i{' '}
            <button className="report-error-link" style={{ marginTop: 0 }} onClick={() => setReportStatus('idle')}>
              pokušajte ponovo
            </button>.
          </p>
        )}

        {(previous || next) && (
          <nav className="record-steps" aria-label="Susedni zapisi u spisku">
            {previous ? (
              <button type="button" className="record-step" onClick={() => onOpen!(previous)}>
                <span className="record-step-label"><ChevronLeftIcon size={16} /> Prethodni</span>
                <span className="record-step-name">{previous.full_name}</span>
              </button>
            ) : <span />}
            {next && (
              <button type="button" className="record-step record-step-next" onClick={() => onOpen!(next)}>
                <span className="record-step-label">Sledeći <ChevronRightIcon size={16} /></span>
                <span className="record-step-name">{next.full_name}</span>
              </button>
            )}
          </nav>
        )}
      </div>
    </div>
  )
}
