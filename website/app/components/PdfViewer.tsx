'use client'

import { useState, useRef, useCallback, useLayoutEffect } from 'react'
import Link from 'next/link'
import { ChevronLeftIcon, ChevronRightIcon, MinusIcon, PlusIcon, TargetIcon } from './Icons'
import { highlightBox } from '@/app/lib/entryBox'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// Self-hosted PDF.js worker (avoids CDN dependency)
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'

// Never let PDF.js compile font code with eval (also blocked by the CSP). Load only the parts of the book the
// shown page needs, by range requests, rather than the whole file (up to 18 MB): without streaming and prefetch
const pdfOptions = { isEvalSupported: false, disableStream: true, disableAutoFetch: true }

interface PdfViewerProps {
  pdfFile: string          // URL path like "/pdfs/prva-proleterska-1.pdf"
  pageNumber: number       // 1-indexed page to show
  yPosition: number        // Y of the entry's first line, in PDF points from the page top
  yPositionEnd?: number    // Bottom of the entry's last line on the page
  xPosition: number        // X of the entry's first line, in PDF points from the left edge
  xPositionLeft?: number   // Left edge of the entry when it isn't xPosition
  xPositionEnd?: number    // Right edge of the entry's text
  sourceHref?: string      // Link to the Sources page anchor for "View full document"
}

export default function PdfViewer({
  pdfFile, pageNumber, yPosition, yPositionEnd, xPosition, xPositionLeft, xPositionEnd, sourceHref,
}: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(pageNumber)
  const [scale, setScale] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const fitScale = useRef(2)

  // Start at the zoom where the whole highlighted entry fits the viewer's width (between 100% and 200%)
  useLayoutEffect(() => {
    const width = containerRef.current?.clientWidth ?? 0
    const box = highlightBox(xPosition, yPosition, xPositionLeft, xPositionEnd, yPositionEnd)
    const fit = width > 0 ? (width - 24) / box.width : 2
    // On phones a full-width fit makes the print too small to read; lead with the start of the entry instead
    const floor = width > 0 && width < 420 ? 1.4 : 1
    fitScale.current = Math.round(Math.min(2, Math.max(floor, fit)) * 20) / 20
    setScale(fitScale.current)
  }, [xPosition, yPosition, xPositionLeft, xPositionEnd, yPositionEnd])

  // When the PDF page renders, scroll to the soldier's Y position
  const onPageRenderSuccess = useCallback(() => {
    setLoading(false)
    if (containerRef.current && scale != null && currentPage === pageNumber) {
      const scrollTarget = yPosition * scale
      const containerHeight = containerRef.current.clientHeight
      const scrollTop = Math.max(0, scrollTarget - containerHeight / 3)
      containerRef.current.scrollTop = scrollTop
      // Bring the start of the entry into view when the page is wider than the viewer
      const box = highlightBox(xPosition, yPosition, xPositionLeft, xPositionEnd, yPositionEnd)
      containerRef.current.scrollLeft = Math.max(0, box.left * scale - 12)
    }
  }, [xPosition, xPositionLeft, xPositionEnd, yPosition, yPositionEnd, scale, currentPage, pageNumber])

  const onDocumentLoadSuccess = ({ numPages: n }: { numPages: number }) => {
    setNumPages(n)
  }

  const onDocumentLoadError = () => {
    setError(true)
    setLoading(false)
  }

  // Navigation handlers
  const goToPrevPage = () => {
    setLoading(true)
    setCurrentPage(p => Math.max(1, p - 1))
  }
  const goToNextPage = () => {
    setLoading(true)
    setCurrentPage(p => Math.min(numPages || p, p + 1))
  }
  const zoomIn = () => setScale(s => Math.min(3, (s ?? 2) + 0.25))
  const zoomOut = () => setScale(s => Math.max(0.5, (s ?? 2) - 0.25))
  const resetView = () => {
    setCurrentPage(pageNumber)
    setScale(fitScale.current)
    setLoading(true)
  }

  if (error) {
    return (
      <div className="pdf-viewer-error">
        Strana iz knjige trenutno ne može da se prikaže.
      </div>
    )
  }

  return (
    <div className="pdf-viewer-container">
      <div className="pdf-viewer-toolbar">
        <div className="pdf-viewer-controls-group">
          <button onClick={goToPrevPage} disabled={currentPage <= 1} aria-label="Prethodna strana">
            <ChevronLeftIcon />
          </button>
          <span className="pdf-viewer-page">
            str. {currentPage}{numPages ? ` / ${numPages}` : ''}
          </span>
          <button onClick={goToNextPage} disabled={currentPage >= (numPages || 1)} aria-label="Sledeća strana">
            <ChevronRightIcon />
          </button>
          {currentPage !== pageNumber && (
            <button onClick={resetView}>
              <TargetIcon size={16} /> Nazad na zapis
            </button>
          )}
        </div>
        <div className="pdf-viewer-controls-group">
          <button onClick={zoomOut} aria-label="Umanji"><MinusIcon /></button>
          <span className="pdf-viewer-zoom-info">{scale != null ? `${Math.round(scale * 100)}%` : ''}</span>
          <button onClick={zoomIn} aria-label="Uvećaj"><PlusIcon /></button>
        </div>
      </div>

      {/* Scrollable PDF area */}
      <div className="pdf-viewer-scroll" ref={containerRef}>
        {loading && <div className="pdf-viewer-loading">Učitavanje strane…</div>}
        {scale != null && <div className="pdf-viewer-page-wrap">
          <Document
            file={pdfFile}
            options={pdfOptions}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading=""
          >
            <Page
              pageNumber={currentPage}
              scale={scale}
              onRenderSuccess={onPageRenderSuccess}
              renderTextLayer={true}
              renderAnnotationLayer={false}
            />
          </Document>

          {/* Highlight box around the soldier's entry */}
          {currentPage === pageNumber && !loading && (() => {
            const box = highlightBox(xPosition, yPosition, xPositionLeft, xPositionEnd, yPositionEnd)
            return (
              <div
                className="pdf-highlight-box"
                style={{
                  top: `${box.top * scale}px`,
                  left: `${Math.max(0, box.left) * scale}px`,
                  width: `${box.width * scale}px`,
                  height: `${box.height * scale}px`,
                }}
              />
            )
          })()}
        </div>}
      </div>

      {/* Footer with link to full document */}
      {sourceHref && (
        <div className="pdf-viewer-footer">
          <Link href={sourceHref}>Cela knjiga na strani Izvori</Link>
        </div>
      )}
    </div>
  )
}
