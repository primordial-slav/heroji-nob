'use client'

import { useEffect, useState } from 'react'
import { pdfjs } from 'react-pdf'
import type { SoldierSource } from '@/app/lib/types'
import { highlightBox } from '@/app/lib/entryBox'

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'

// Sharp enough for print at the card's width
const SCALE = 3
// Margin around the entry, in PDF points. The highlight box already adds 2pt above and below, which on
// tightly set pages reaches into the neighbouring lines, so the crop takes most of it back.
const PAD_X = 8
const PAD_Y = -1.5

// The entry cut out of its scanned book page, as an image
export default function EntryCrop({ entry, onSettled }: { entry: SoldierSource; onSettled?: () => void }) {
  const [src, setSrc] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    const task = pdfjs.getDocument({ url: `/pdfs/${entry.pdf_file}`, isEvalSupported: false })
    ;(async () => {
      try {
        const doc = await task.promise
        const page = await doc.getPage(entry.pdf_page!)
        const viewport = page.getViewport({ scale: SCALE })
        const box = highlightBox(entry.pdf_x ?? 0, entry.pdf_y ?? 0, entry.pdf_x_left, entry.pdf_x_end, entry.pdf_y_end)
        const x = Math.max(0, (box.left - PAD_X) * SCALE)
        const y = Math.max(0, (box.top - PAD_Y) * SCALE)
        const width = Math.min(viewport.width - x, (box.width + 2 * PAD_X) * SCALE)
        const height = Math.min(viewport.height - y, (box.height + 2 * PAD_Y) * SCALE)
        const canvas = document.createElement('canvas')
        canvas.width = Math.round(width)
        canvas.height = Math.round(height)
        // Render only the entry's part of the page
        await page.render({
          canvasContext: canvas.getContext('2d')!,
          viewport,
          transform: [1, 0, 0, 1, -x, -y],
        }).promise
        if (!cancelled) setSrc(canvas.toDataURL('image/png'))
      } catch {
        if (!cancelled) setFailed(true)
      } finally {
        if (!cancelled) onSettled?.()
      }
    })()
    return () => {
      cancelled = true
      task.destroy()
    }
  }, [entry, onSettled])

  if (failed) return <p className="entry-crop-missing">Isečak iz knjige ne može da se prikaže.</p>
  if (!src) return <div className="entry-crop-loading" aria-label="Učitavanje isečka iz knjige" />
  return <img className="entry-crop" src={src} alt="Zapis kako je odštampan u knjizi" />
}
