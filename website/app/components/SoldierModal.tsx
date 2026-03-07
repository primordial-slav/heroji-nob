'use client'

import { lazy, Suspense, useState } from 'react'
import type { Soldier } from '@/app/lib/types'

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

  const [showReportForm, setShowReportForm] = useState(false)
  const [reportText, setReportText] = useState('')
  const [reportStatus, setReportStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')

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
          Jedinica: unitName || soldier.unit || '',
          'Opis greške': reportText,
        }),
      })
      if (res.ok) {
        setReportStatus('sent')
      } else {
        setReportStatus('error')
      }
    } catch {
      setReportStatus('error')
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`modal-content ${hasPdfData ? 'has-pdf' : ''}`}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose}>&times;</button>
        <h2 className="modal-title">{soldier.full_name}</h2>
        <div className="modal-details">
          {soldier.fathers_name && (
            <div className="modal-detail-row">
              <span className="modal-label">Ime oca:</span>
              <span className="modal-value">{soldier.fathers_name}</span>
            </div>
          )}
          {soldier.birth_year && (
            <div className="modal-detail-row">
              <span className="modal-label">Godina rođenja:</span>
              <span className="modal-value">{soldier.birth_year}</span>
            </div>
          )}
          {(unitName || soldier.unit) && (
            <div className="modal-detail-row">
              <span className="modal-label">Jedinica:</span>
              <span className="modal-value">{unitName || soldier.unit}</span>
            </div>
          )}
          {soldier.additional_info && (
            <div className="modal-detail-row">
              <span className="modal-label">Dodatne informacije:</span>
              <span className="modal-value">{soldier.additional_info}</span>
            </div>
          )}
        </div>

        {/* Report Error */}
        {!showReportForm && reportStatus !== 'sent' && (
          <button
            className="report-error-link"
            onClick={() => setShowReportForm(true)}
          >
            Prijavi grešku
          </button>
        )}

        {showReportForm && reportStatus === 'idle' && (
          <div className="report-form">
            <textarea
              className="report-textarea"
              placeholder="Opišite grešku..."
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              rows={3}
            />
            <div className="report-actions">
              <button
                className="report-submit"
                onClick={handleReport}
                disabled={!reportText.trim()}
              >
                Pošalji
              </button>
              <button
                className="report-cancel"
                onClick={() => { setShowReportForm(false); setReportText('') }}
              >
                Otkaži
              </button>
            </div>
          </div>
        )}

        {reportStatus === 'sending' && (
          <p className="report-status">Slanje...</p>
        )}
        {reportStatus === 'sent' && (
          <p className="report-status report-success">Hvala na prijavi!</p>
        )}
        {reportStatus === 'error' && (
          <p className="report-status report-error-msg">Greška pri slanju. Pokušajte ponovo.</p>
        )}

        {/* PDF Viewer Section */}
        {hasPdfData && (
          <div style={{ marginTop: '1.25rem' }}>
            <Suspense fallback={
              <div className="pdf-viewer-loading" style={{ padding: '2rem', textAlign: 'center' }}>
                Učitavanje pregledača...
              </div>
            }>
              <PdfViewer
                pdfFile={`/pdfs/${soldier.pdf_file}`}
                pageNumber={soldier.pdf_page!}
                yPosition={soldier.pdf_y ?? 0}
                xPosition={soldier.pdf_x ?? 0}
                sourceHref={sourceHref}
              />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  )
}
