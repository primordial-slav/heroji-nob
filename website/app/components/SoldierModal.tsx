'use client'

import { lazy, Suspense } from 'react'
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
              />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  )
}
