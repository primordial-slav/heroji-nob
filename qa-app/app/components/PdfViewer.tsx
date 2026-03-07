'use client'

import { useState, useRef, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'

interface PdfViewerProps {
  pdfFile: string
  pageNumber: number
  yPosition: number
  xPosition: number
}

export default function PdfViewer({ pdfFile, pageNumber, yPosition, xPosition }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(pageNumber)
  const [scale, setScale] = useState(1.0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const onPageRenderSuccess = useCallback(() => {
    setLoading(false)
    if (containerRef.current && currentPage === pageNumber) {
      const scrollTarget = yPosition * scale
      const containerHeight = containerRef.current.clientHeight
      containerRef.current.scrollTop = Math.max(0, scrollTarget - containerHeight / 3)
    }
  }, [yPosition, scale, currentPage, pageNumber])

  const goToPrevPage = () => { setLoading(true); setCurrentPage(p => Math.max(1, p - 1)) }
  const goToNextPage = () => { setLoading(true); setCurrentPage(p => Math.min(numPages || p, p + 1)) }
  const zoomIn = () => setScale(s => Math.min(3, s + 0.25))
  const zoomOut = () => setScale(s => Math.max(0.5, s - 0.25))
  const resetView = () => { setCurrentPage(pageNumber); setScale(1.0); setLoading(true) }

  if (error) {
    return <div className="pdf-error">PDF not available</div>
  }

  return (
    <div className="pdf-container">
      <div className="pdf-toolbar">
        <button onClick={goToPrevPage} disabled={currentPage <= 1}>&#9664;</button>
        <span className="pdf-page-info">p. {currentPage}{numPages ? `/${numPages}` : ''}</span>
        <button onClick={goToNextPage} disabled={currentPage >= (numPages || 1)}>&#9654;</button>
        <span className="pdf-sep" />
        <button onClick={zoomOut}>&#8722;</button>
        <span className="pdf-zoom-info">{Math.round(scale * 100)}%</span>
        <button onClick={zoomIn}>&#43;</button>
        {currentPage !== pageNumber && (
          <>
            <span className="pdf-sep" />
            <button onClick={resetView}>&#8634;</button>
          </>
        )}
      </div>
      <div className="pdf-scroll" ref={containerRef}>
        {loading && <div className="pdf-loading">Loading...</div>}
        <div style={{ position: 'relative' }}>
          <Document
            file={`/pdfs/${pdfFile}`}
            onLoadSuccess={({ numPages: n }) => setNumPages(n)}
            onLoadError={() => { setError(true); setLoading(false) }}
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
          {currentPage === pageNumber && !loading && (
            <div
              className="pdf-highlight"
              style={{
                top: `${(yPosition - 2) * scale}px`,
                left: `${Math.max(0, xPosition - 5) * scale}px`,
                width: xPosition > 200 ? `${250 * scale}px` : `${400 * scale}px`,
                height: `${18 * scale}px`,
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}
