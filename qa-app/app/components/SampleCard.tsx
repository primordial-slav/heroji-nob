'use client'

import { Suspense, lazy, useState } from 'react'
import type { SoldierSample } from '../lib/types'
import { FLAG_LABELS } from '../lib/types'
import ReviewForm from './ReviewForm'

const PdfViewer = lazy(() => import('./PdfViewer'))

interface SampleCardProps {
  sample: SoldierSample
  detection: 'suspicious' | 'random'
  onRemove: (soldierId: string) => void
  onStatsChanged: () => void
}

export default function SampleCard({ sample, detection, onRemove, onStatsChanged }: SampleCardProps) {
  const { soldier, brigadeName, brigadeCode, flags } = sample
  const [showPdf, setShowPdf] = useState(false)
  const hasPdf = soldier.pdf_page && soldier.pdf_file && soldier.pdf_y

  const handleDismiss = async () => {
    await fetch('/api/reviews', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        soldier_id: soldier.soldier_id,
        brigade_code: brigadeCode,
        status: 'dismissed',
        detection,
        flags_detail: JSON.stringify(flags),
        soldier_data: JSON.stringify(soldier),
      }),
    })
    onRemove(soldier.soldier_id)
    onStatsChanged()
  }

  const handleReviewed = () => {
    onRemove(soldier.soldier_id)
    onStatsChanged()
  }

  return (
    <div className="sample-card">
      <div className="card-header">
        <div className="card-name">{soldier.full_name || `${soldier.last_name} ${soldier.first_name}`}</div>
        <button className="btn-dismiss" onClick={handleDismiss} title="Dismiss">&#10005;</button>
      </div>

      <div className="card-meta">
        <span className="meta-id">{soldier.soldier_id}</span>
        <span className="meta-brigade">{brigadeName}</span>
      </div>

      <div className="card-fields">
        {soldier.fathers_name && (
          <div className="field-row">
            <span className="field-label">Father:</span>
            <span className="field-value">{soldier.fathers_name}</span>
          </div>
        )}
        {soldier.birth_year && (
          <div className="field-row">
            <span className="field-label">Birth:</span>
            <span className="field-value">{soldier.birth_year}</span>
          </div>
        )}
        {soldier.middle_name && (
          <div className="field-row">
            <span className="field-label">Middle:</span>
            <span className="field-value">{soldier.middle_name}</span>
          </div>
        )}
        {soldier.additional_info && (
          <div className="field-row field-row-info">
            <span className="field-label">Info:</span>
            <span className="field-value">{soldier.additional_info}</span>
          </div>
        )}
      </div>

      {flags.length > 0 && (
        <div className="card-flags">
          {flags.map(f => (
            <span key={f} className="flag-badge">{FLAG_LABELS[f] || f}</span>
          ))}
        </div>
      )}

      {hasPdf && (
        <div className="card-pdf-section">
          {!showPdf ? (
            <button className="btn-show-pdf" onClick={() => setShowPdf(true)}>
              Show PDF source
            </button>
          ) : (
            <Suspense fallback={<div className="pdf-loading">Loading PDF viewer...</div>}>
              <PdfViewer
                pdfFile={soldier.pdf_file!}
                pageNumber={soldier.pdf_page!}
                yPosition={soldier.pdf_y!}
                xPosition={soldier.pdf_x || 72}
              />
            </Suspense>
          )}
        </div>
      )}

      <ReviewForm
        soldierId={soldier.soldier_id}
        brigadeCode={brigadeCode}
        soldierData={JSON.stringify(soldier)}
        detection={detection}
        flagsDetail={JSON.stringify(flags)}
        onSaved={handleReviewed}
      />
    </div>
  )
}
