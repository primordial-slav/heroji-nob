'use client'

import { useEffect, useState } from 'react'
import { pdfjs } from 'react-pdf'
import type { SoldierSource } from '@/app/lib/types'
import { CROP_GAP, cropBoxes } from '@/app/lib/entryBox'
import { useT } from '@/app/i18n/LangContext'

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'

// Sharp enough for print at the card's width
const SCALE = 3

// The entry cut out of its scanned book page, as an image; `onImage` gets the image too
export default function EntryCrop({ entry, onSettled, onImage }: {
  entry: SoldierSource
  onSettled?: () => void
  onImage?: (src: string) => void
}) {
  const t = useT().crop
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
        // Render only the entry's parts of the page, each on its own canvas: PDF.js whitens the whole canvas it draws on
        const parts: HTMLCanvasElement[] = []
        for (const box of cropBoxes(entry)) {
          const x = Math.max(0, box.left * SCALE)
          const y = Math.max(0, box.top * SCALE)
          const width = Math.min(viewport.width - x, box.width * SCALE)
          const height = Math.min(viewport.height - y, box.height * SCALE)
          const canvas = document.createElement('canvas')
          canvas.width = Math.round(width)
          canvas.height = Math.round(height)
          await page.render({
            canvasContext: canvas.getContext('2d')!,
            viewport,
            transform: [1, 0, 0, 1, -x, -y],
          }).promise
          parts.push(canvas)
        }
        if (!cancelled) {
          // one under the other, where the entry runs on to another column
          let whole = parts[0]
          if (parts.length > 1) {
            const gap = Math.round(CROP_GAP * SCALE)
            whole = document.createElement('canvas')
            whole.width = Math.max(...parts.map((p) => p.width))
            whole.height = parts.reduce((all, p) => all + p.height, 0) + gap * (parts.length - 1)
            const context = whole.getContext('2d')!
            context.fillStyle = '#ffffff'
            context.fillRect(0, 0, whole.width, whole.height)
            let top = 0
            for (const part of parts) {
              context.drawImage(part, 0, top)
              top += part.height + gap
            }
          }
          const image = whole.toDataURL('image/png')
          setSrc(image)
          onImage?.(image)
        }
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
    // onImage is the caller's and changes with its renders; the entry alone decides what is cut
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry, onSettled])

  if (failed) return <p className="entry-crop-missing">{t.failed}</p>
  if (!src) return <div className="entry-crop-loading" aria-label={t.loading} />
  return <img className="entry-crop" src={src} alt={t.alt} />
}
