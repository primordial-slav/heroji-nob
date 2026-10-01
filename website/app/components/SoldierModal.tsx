'use client'

import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import type { Soldier, SoldierSource } from '@/app/lib/types'
import { SoldierName } from './SoldierResults'
import { ChevronLeftIcon, ChevronRightIcon, CloseIcon } from './Icons'
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
import SoldierPortrait from './SoldierPortrait'
import { portraitFor } from '@/app/data/portraits'
import { useLang, useLocalePath, useT } from '@/app/i18n/LangContext'
import { LANG_NAMES, type Lang } from '@/app/i18n/config'
import { quoteMarks } from '@/app/i18n/format'
import { titlePart } from '@/app/i18n/sources'
import { unitName as localUnitName } from '@/app/i18n/units'
import RichText from '@/app/i18n/RichText'
import { unitImageProps } from '@/app/lib/unitImage'

// The unit photo spans the dialog: the whole screen up to 640px, the 40rem dialog above
const RECORD_PHOTO_SIZES = '(max-width: 640px) 100vw, 640px'

// Lazy-load PdfViewer so PDF.js (~500KB) is not in the initial bundle
const PdfViewer = lazy(() => import('./PdfViewer'))

/** A short name for the book switch: "Spisak poginulih" from "Brodska brigada — spisak poginulih", in English "The fallen" */
function shortTitle(entry: SoldierSource, lang: Lang): string {
  const part = titlePart(sourceTitle(entry), lang)
  return part.charAt(0).toUpperCase() + part.slice(1)
}

/** A unit's name (as the records give it, in Serbo-Croatian) in the page's language */
function shownUnitName(name: string, lang: Lang): string {
  const unit = unitByName(name)
  return unit ? localUnitName(unit, lang) : quoteMarks(lang, name)
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
  const lang = useLang()
  const t = useT()
  const to = useLocalePath()
  // The soldier's own entry, then the same soldier's entries in the unit's other books
  const entries: SoldierSource[] = entriesOf(soldier)
  const pages = entries.filter(hasPage)
  const [shownPage, setShownPage] = useState(0)
  const page = pages[Math.min(shownPage, pages.length - 1)]
  const pageLabels = pages.map((e) => shortTitle(e, lang))
  const switchLabels = pages.map((e, i) =>
    pageLabels.indexOf(pageLabels[i]) !== pageLabels.lastIndexOf(pageLabels[i]) ? `${pageLabels[i]}, ${t.record.page(e.pdf_page!)}` : pageLabels[i])
  const sourceHref = page?.pdf_file ? to(`/izvori#${page.pdf_file.replace('.pdf', '')}`) : undefined
  const unit = unitName || soldier.unit
  const unitRecord = unitByName(unit)
  const portrait = portraitFor(soldier)
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
          Jezik: LANG_NAMES[lang].name,
          'Opis greške': reportText,
        }),
      })
      setReportStatus((await wasDelivered(res)) ? 'sent' : 'error')
    } catch {
      setReportStatus('error')
    }
  }

  const filled = recordDetails(soldier, t)
  const honours = honoursLine(soldier, t)

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
        <button className="modal-close" onClick={onClose} aria-label={t.record.close}>
          <CloseIcon size={22} />
        </button>

        {unitRecord && !unitRecord.image.includes('/pdf-thumbs/') && (
          <div className="record-photo">
            <img {...unitImageProps(unitRecord.image, RECORD_PHOTO_SIZES)} alt="" style={{ objectPosition: photoPosition(unitRecord.id) }} />
          </div>
        )}
        <SoldierMedals soldier={soldier} look="foto" className="modal-medals" />
        <div className="modal-head">
          <SoldierPortrait soldier={soldier} unitId={unitRecord?.id} portrait={portrait} className="modal-portrait" />
          <div>
            <h2 className="modal-title" id="soldier-name"><SoldierName soldier={soldier} /></h2>
            {allUnits.length > 0 && <p className="modal-unit">{allUnits.map((u) => shownUnitName(u, lang)).join(' · ')}</p>}
            {honours && <p className="modal-honours">{honours}</p>}
            {portrait && (
              <p className="modal-portrait-credit">
                {t.record.photo} {portrait.href
                  ? <a href={portrait.href} target="_blank" rel="noopener noreferrer">{t.record.photoCredit(portrait.credit)}</a>
                  : t.record.photoCredit(portrait.credit)}
              </p>
            )}
          </div>
        </div>
        <RecordActions soldier={soldier} unit={unitRecord} />
        <FamilyStory items={contributionsFor(soldier.soldier_id, (soldier.other_sources ?? []).map((o) => o.soldier_id))} />

        {entries.length === 1 && soldier.additional_info && (
          <p className="modal-entry">{soldier.additional_info}</p>
        )}

        {entries.length > 1 && (
          <ol className="modal-sources" aria-label={t.record.entries}>
            {entries.map((e, i) => (
              <li key={i} className="modal-source-entry">
                <p className="modal-source-label">
                  {e.unit_file && unitOf(e) && <>{shownUnitName(unitOf(e)!, lang)}: </>}
                  {sourceTitle(e)}
                  {e.pdf_page != null && `, ${t.record.page(e.pdf_page)}`}
                  {e.name && e.name !== soldier.full_name && <>. {t.record.nameInBook} {e.name}</>}
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
              <h3>{t.record.references}</h3>
              {pages.length > 1 && (
                <div className="modal-source-switch" role="group" aria-label={t.record.book}>
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
            <Suspense fallback={<div className="pdf-viewer-loading">{t.record.loadingPage}</div>}>
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
              <h3>{t.record.source}</h3>
            </div>
            <p className="modal-source-note">
              <RichText
                text={t.record.noScan}
                render={(part) => <a href={soldier.source_url} target="_blank" rel="noopener noreferrer">{part}</a>}
              />
            </p>
          </>
        )}

        <KnowSoldierForm soldier={soldier} unit={unitRecord} />

        {!showReportForm && reportStatus === 'idle' && (
          <button className="report-error-link" onClick={() => setShowReportForm(true)}>
            {t.report.open}
          </button>
        )}

        {showReportForm && reportStatus === 'idle' && (
          <div className="report-form">
            <label htmlFor="report-text">{t.report.label}</label>
            <textarea
              id="report-text"
              className="report-textarea"
              placeholder={t.report.hint}
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              rows={3}
              maxLength={2000}
            />
            <div className="report-actions">
              <button className="btn btn-primary" onClick={handleReport} disabled={!reportText.trim()}>
                {t.report.send}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => { setShowReportForm(false); setReportText('') }}
              >
                {t.report.cancel}
              </button>
            </div>
          </div>
        )}

        {reportStatus === 'sending' && <p className="report-status">{t.report.sending}</p>}
        {reportStatus === 'sent' && (
          <p className="report-status report-success">{t.report.sent}</p>
        )}
        {reportStatus === 'error' && (
          <p className="report-status report-error-msg">
            <RichText
              text={t.report.failed}
              render={(part) => (
                <button className="report-error-link" style={{ marginTop: 0 }} onClick={() => setReportStatus('idle')}>
                  {part}
                </button>
              )}
            />
          </p>
        )}

        {(previous || next) && (
          <nav className="record-steps" aria-label={t.record.steps}>
            {previous ? (
              <button type="button" className="record-step" onClick={() => onOpen!(previous)}>
                <span className="record-step-label"><ChevronLeftIcon size={16} /> {t.record.previous}</span>
                <span className="record-step-name">{previous.full_name}</span>
              </button>
            ) : <span />}
            {next && (
              <button type="button" className="record-step record-step-next" onClick={() => onOpen!(next)}>
                <span className="record-step-label">{t.record.next} <ChevronRightIcon size={16} /></span>
                <span className="record-step-name">{next.full_name}</span>
              </button>
            )}
          </nav>
        )}
      </div>
    </div>
  )
}
