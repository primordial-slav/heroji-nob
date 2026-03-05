'use client'

import { useState, useRef, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// Configure PDF.js worker from CDN to avoid Next.js Terser bundling issues
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface PdfViewerProps {
  pdfFile: string          // URL path like "/pdfs/prva-proleterska-1.pdf"
  pageNumber: number       // 1-indexed page to show
  yPosition: number        // Y coordinate in PDF points to scroll to
}

export default function PdfViewer({ pdfFile, pageNumber, yPosition }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(pageNumber)
  const [scale, setScale] = useState(1.5)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // When the PDF page renders, scroll to the soldier's Y position
  const onPageRenderSuccess = useCallback(() => {
    setLoading(false)
    if (containerRef.current && currentPage === pageNumber) {
      // PDF coordinates are in points (72 points = 1 inch)
      // react-pdf renders at the given scale, so multiply yPosition by scale
      const scrollTarget = yPosition * scale
      // Center the view: scroll so the soldier's line is ~1/3 from the top
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
    setScale(1.5)
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
      {/* Toolbar */}
      <div className="pdf-viewer-toolbar">
        <button onClick={goToPrevPage} disabled={currentPage <= 1} title="Prethodna strana">
          &#8249;
        </button>
        <span className="pdf-viewer-page-info">
          Strana {currentPage}{numPages ? ` / ${numPages}` : ''}
        </span>
        <button onClick={goToNextPage} disabled={currentPage >= (numPages || 1)} title="Sledeća strana">
          &#8250;
        </button>
        <span className="pdf-viewer-separator">|</span>
        <button onClick={zoomOut} title="Umanji">&#8722;</button>
        <span className="pdf-viewer-zoom-info">{Math.round(scale * 100)}%</span>
        <button onClick={zoomIn} title="Uvećaj">&#43;</button>
        {currentPage !== pageNumber && (
          <>
            <span className="pdf-viewer-separator">|</span>
            <button onClick={resetView} title="Vrati na poziciju borca" className="pdf-viewer-reset-btn">
              &#8634; Nazad
            </button>
          </>
        )}
      </div>

      {/* Scrollable PDF area */}
      <div className="pdf-viewer-scroll" ref={containerRef}>
        {loading && <div className="pdf-viewer-loading">Učitavanje PDF-a...</div>}
        <div style={{ position: 'relative' }}>
          <Document
            file={pdfFile}
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

          {/* Highlight indicator for the soldier's position */}
          {currentPage === pageNumber && !loading && (
            <div
              className="pdf-viewer-highlight"
              style={{
                top: `${yPosition * scale}px`,
              }}
            >
              <div className="pdf-highlight-bar" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
