'use client'

import { useEffect, useRef } from 'react'
import { CloseIcon } from './Icons'

// A soldier's photograph opened over the page: as large as the screen allows but never past twice its own size
// (a book's small print gets no bigger than that), with his name and where the photo comes from. Escape, the
// close button or a click beside the photo closes it, and only it: the record under it stays open.
export default function PhotoLightbox({ src, name, credit, href, onClose }: {
  src: string
  name: string
  credit: string
  href?: string
  onClose: () => void
}) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    closeRef.current?.focus()
    // before the record's own key handler (on document), so Escape and the arrows stay here
    const onKey = (e: KeyboardEvent) => {
      if (['Escape', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.stopPropagation()
        e.preventDefault()
        if (e.key === 'Escape') onCloseRef.current()
      }
    }
    window.addEventListener('keydown', onKey, true)
    return () => {
      window.removeEventListener('keydown', onKey, true)
      previous?.focus()
    }
  }, [])

  // fixed over the whole window (no ancestor of the record transforms it)
  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={`Fotografija: ${name}`} onClick={onClose}>
      <button ref={closeRef} type="button" className="lightbox-close" onClick={onClose} aria-label="Zatvori fotografiju">
        <CloseIcon size={22} />
      </button>
      <figure className="lightbox-figure" onClick={(e) => e.stopPropagation()}>
        <img
          src={src}
          alt={name}
          onLoad={(e) => {
            const img = e.currentTarget
            img.style.maxHeight = `min(80vh, ${img.naturalHeight * 2}px)`
            img.style.maxWidth = `min(90vw, ${img.naturalWidth * 2}px)`
          }}
        />
        <figcaption>
          <span className="lightbox-name">{name}</span>
          <span className="lightbox-credit">
            Fotografija: {href ? <a href={href} target="_blank" rel="noopener noreferrer">{credit}</a> : credit}
          </span>
        </figcaption>
      </figure>
    </div>
  )
}
