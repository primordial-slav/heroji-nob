'use client'

import { useState, useRef, useCallback } from 'react'
import Link from 'next/link'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// Self-hosted PDF.js worker (avoids CDN dependency)
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'

// Never let PDF.js compile font code with eval (also blocked by the CSP)
const pdfOptions = { isEvalSupported: false }

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

// Highlight box around the soldier's entry, in PDF points. The extent comes
// from data-extraction/entry_boxes.py; records without one get a one-line box.
function highlightBox(x: number, y: number, xLeft?: number, xEnd?: number, yEnd?: number) {
  const left = xLeft ?? x
  const right = xEnd != null && xEnd > left ? xEnd : left + (x > 150 ? 200 : 250)
  const bottom = yEnd != null && yEnd > y ? yEnd : y + 11
  const padX = 3, padY = 2
  return { left: left - padX, top: y - padY, width: right - left + 2 * padX, height: bottom - y + 2 * padY }
}

export default function PdfViewer({
  pdfFile, pageNumber, yPosition, yPositionEnd, xPosition, xPositionLeft, xPositionEnd, sourceHref,
}: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(pageNumber)
  const [scale, setScale] = useState(2.0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // When the PDF page renders, scroll to the soldier's Y position
  const onPageRenderSuccess = useCallback(() => {
    setLoading(false)
    if (containerRef.current && currentPage === pageNumber) {
      const scrollTarget = yPosition * scale
      const containerHeight = containerRef.current.clientHeight
      const scrollTop = Math.max(0, scrollTarget - containerHeight / 3)
      containerRef.current.scrollTop = scrollTop
    }
  }, [yPosition, scale, currentPage, pageNumber])

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
  const zoomIn = () => setScale(s => Math.min(3, s + 0.25))
  const zoomOut = () => setScale(s => Math.max(0.5, s - 0.25))
  const resetView = () => {
    setCurrentPage(pageNumber)
    setScale(2.0)
    setLoading(true)
  }

  if (error) {
    return (
      <div className="pdf-viewer-error">
        Izvorni PDF dokument nije dostupan.
      </div>
    )
  }

  return (
    <div className="pdf-viewer-container">
      {/* Archival header */}
      <div className="pdf-viewer-header">
        <span className="pdf-viewer-header-star">&#9733;</span>
        <span className="pdf-viewer-header-title">Izvorni dokument</span>
        <span className="pdf-viewer-header-page">
          str. {currentPage}{numPages ? ` / ${numPages}` : ''}
        </span>
      </div>

      {/* Controls */}
      <div className="pdf-viewer-toolbar">
        <div className="pdf-viewer-controls-group">
          <button onClick={goToPrevPage} disabled={currentPage <= 1} title="Prethodna strana">
            &#9664;
          </button>
          <button onClick={goToNextPage} disabled={currentPage >= (numPages || 1)} title="Sledeća strana">
            &#9654;
          </button>
        </div>
        <span className="pdf-viewer-separator" />
        <div className="pdf-viewer-controls-group">
          <button onClick={zoomOut} title="Umanji">&#8722;</button>
          <span className="pdf-viewer-zoom-info">{Math.round(scale * 100)}%</span>
          <button onClick={zoomIn} title="Uvećaj">&#43;</button>
        </div>
        {currentPage !== pageNumber && (
          <>
            <span className="pdf-viewer-separator" />
            <button onClick={resetView} title="Vrati na poziciju borca" className="pdf-viewer-reset-btn">
              &#8634; Nazad
            </button>
          </>
        )}
      </div>

      {/* Scrollable PDF area */}
      <div className="pdf-viewer-scroll" ref={containerRef}>
        {loading && <div className="pdf-viewer-loading">Učitavanje dokumenta...</div>}
        <div style={{ position: 'relative' }}>
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
        </div>
      </div>

      {/* Footer with link to full document */}
      {sourceHref && (
        <div className="pdf-viewer-footer">
          <Link href={sourceHref}>
            Pogledaj ceo dokument &rarr;
          </Link>
        </div>
      )}
    </div>
  )
}
