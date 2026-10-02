'use client'

import { useState, useRef, useCallback, useEffect, useLayoutEffect } from 'react'
import Link from 'next/link'
import { ChevronLeftIcon, ChevronRightIcon, MinusIcon, PlusIcon, TargetIcon } from './Icons'
import { highlightBox, highlightBoxes } from '@/app/lib/entryBox'
import { useT } from '@/app/i18n/LangContext'
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
  rects?: number[][]       // A name that runs on to the next line: a box for each of its lines
  sourceHref?: string      // Link to the Sources page anchor for "View full document"
  flash?: number           // a new number: go back to the entry and flash its box (a step of the life line asked)
}

export default function PdfViewer({
  pdfFile, pageNumber, yPosition, yPositionEnd, xPosition, xPositionLeft, xPositionEnd, rects, sourceHref, flash,
}: PdfViewerProps) {
  const t = useT()
  const [numPages, setNumPages] = useState<number | null>(null)
  const [currentPage, setCurrentPage] = useState(pageNumber)
  const [scale, setScale] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const fitScale = useRef(2)
  const [flashing, setFlashing] = useState(0)

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

  // Scroll the entry a third of the way down the viewer, its start in view when the page is wider than the viewer
  const scrollToEntry = useCallback((smooth = false) => {
    const el = containerRef.current
    if (!el || scale == null) return
    const box = highlightBox(xPosition, yPosition, xPositionLeft, xPositionEnd, yPositionEnd)
    el.scrollTo({
      top: Math.max(0, yPosition * scale - el.clientHeight / 3),
      left: Math.max(0, box.left * scale - 12),
      behavior: smooth ? 'smooth' : 'auto',
    })
  }, [xPosition, xPositionLeft, xPositionEnd, yPosition, yPositionEnd, scale])

  // When the PDF page renders, scroll to the soldier's entry
  const onPageRenderSuccess = useCallback(() => {
    setLoading(false)
    if (currentPage === pageNumber) scrollToEntry()
  }, [scrollToEntry, currentPage, pageNumber])

  // A step of the life line points at the entry: back to its page if the reader turned away, then flash its box
  useEffect(() => {
    if (!flash) return
    if (currentPage !== pageNumber) {
      setLoading(true)
      setCurrentPage(pageNumber)
    } else {
      scrollToEntry(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)
    }
    setFlashing(flash)
    // only a new flash moves the page
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flash])

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
        {t.viewer.failed}
      </div>
    )
  }

  return (
    <div className="pdf-viewer-container">
      <div className="pdf-viewer-toolbar">
        <div className="pdf-viewer-controls-group">
          <button onClick={goToPrevPage} disabled={currentPage <= 1} aria-label={t.viewer.previous}>
            <ChevronLeftIcon />
          </button>
          <span className="pdf-viewer-page">
            {t.viewer.page(currentPage, numPages)}
          </span>
          <button onClick={goToNextPage} disabled={currentPage >= (numPages || 1)} aria-label={t.viewer.next}>
            <ChevronRightIcon />
          </button>
          {currentPage !== pageNumber && (
            <button onClick={resetView}>
              <TargetIcon size={16} /> {t.viewer.back}
            </button>
          )}
        </div>
        <div className="pdf-viewer-controls-group">
          <button onClick={zoomOut} aria-label={t.viewer.zoomOut}><MinusIcon /></button>
          <span className="pdf-viewer-zoom-info">{scale != null ? `${Math.round(scale * 100)}%` : ''}</span>
          <button onClick={zoomIn} aria-label={t.viewer.zoomIn}><PlusIcon /></button>
        </div>
      </div>

      {/* Scrollable PDF area */}
      <div className="pdf-viewer-scroll" ref={containerRef}>
        {loading && <div className="pdf-viewer-loading">{t.record.loadingPage}</div>}
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
          {currentPage === pageNumber && !loading &&
            highlightBoxes(xPosition, yPosition, xPositionLeft, xPositionEnd, yPositionEnd, rects).map((box, i) => (
              <div
                key={`${i}:${flashing}`}
                className={`pdf-highlight-box${flashing ? ' is-flash' : ''}`}
                style={{
                  top: `${box.top * scale}px`,
                  left: `${Math.max(0, box.left) * scale}px`,
                  width: `${box.width * scale}px`,
                  height: `${box.height * scale}px`,
                }}
              />
            ))}
        </div>}
      </div>

      {/* Footer with link to full document */}
      {sourceHref && (
        <div className="pdf-viewer-footer">
          <Link href={sourceHref}>{t.viewer.wholeBook}</Link>
        </div>
      )}
    </div>
  )
}
