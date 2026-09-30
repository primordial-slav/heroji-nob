'use client'

import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import { SoldierName } from './SoldierResults'
import { CloseIcon } from './Icons'
import { sqQuotes } from '@/app/lib/typography'
import { units } from '@/app/data/units'

// Lazy-load PdfViewer so PDF.js (~500KB) is not in the initial bundle
const PdfViewer = lazy(() => import('./PdfViewer'))

interface SoldierModalProps {
  soldier: Soldier
  unitName?: string
  onClose: () => void
}

export default function SoldierModal({ soldier, unitName, onClose }: SoldierModalProps) {
  const hasPdfData = soldier.pdf_page != null && soldier.pdf_file != null
  const sourceHref = soldier.pdf_file
    ? `/izvori#${soldier.pdf_file.replace('.pdf', '')}`
    : undefined
  const unit = unitName || soldier.unit
  const died = soldier.death_type === 'umro'
  const unitRecord = units.find((u) => u.name === unit)

  const [showReportForm, setShowReportForm] = useState(false)
  const [reportText, setReportText] = useState('')
  const [reportStatus, setReportStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const dialogRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  // Close on Escape, keep the page behind from scrolling, and move focus into the dialog
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onCloseRef.current() }
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
      setReportStatus(res.ok ? 'sent' : 'error')
    } catch {
      setReportStatus('error')
    }
  }

  const details: [string, string | undefined][] = [
    ['Ime oca', soldier.fathers_name],
    ['Godina rođenja', soldier.birth_year],
    ['Mesto rođenja', soldier.birth_place],
    ['Narodnost', soldier.ethnicity],
    ['Zanimanje', soldier.occupation],
    ['Dužnost', soldier.rank],
    ['Podjedinica', soldier.unit_detail],
    [died ? 'Datum smrti' : 'Datum pogibije', soldier.death_date],
    [died ? 'Mesto smrti' : 'Mesto pogibije', soldier.death_place],
  ]
  const filled = details.filter(([, value]) => value)

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
            <img src={unitRecord.image} alt="" />
          </div>
        )}
        <h2 className="modal-title" id="soldier-name"><SoldierName soldier={soldier} /></h2>
        {unit && <p className="modal-unit">{sqQuotes(unit)}</p>}

        {soldier.additional_info && (
          <p className="modal-entry">{soldier.additional_info}</p>
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

        {hasPdfData && (
          <>
            <div className="modal-source-head">
              <h3>Strana u knjizi</h3>
            </div>
            <Suspense fallback={<div className="pdf-viewer-loading">Učitavanje strane…</div>}>
              <PdfViewer
                pdfFile={`/pdfs/${soldier.pdf_file}`}
                pageNumber={soldier.pdf_page!}
                yPosition={soldier.pdf_y ?? 0}
                yPositionEnd={soldier.pdf_y_end}
                xPosition={soldier.pdf_x ?? 0}
                xPositionLeft={soldier.pdf_x_left}
                xPositionEnd={soldier.pdf_x_end}
                sourceHref={sourceHref}
              />
            </Suspense>
          </>
        )}

        {!hasPdfData && soldier.source_url && (
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
      </div>
    </div>
  )
}
