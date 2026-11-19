'use client'

import { useEffect, useRef } from 'react'
import { CloseIcon } from './Icons'
import { useT } from '@/app/i18n/LangContext'

/** Something opened over the record: focus on its close button, and Escape closes it and only it. Returns that button's ref. */
export function useLightboxKeys(onClose: () => void, onArrow?: (dir: -1 | 1) => void) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose
  // the arrows step through what is shown (a family's album) where it has more than one thing
  const onArrowRef = useRef(onArrow)
  onArrowRef.current = onArrow

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    closeRef.current?.focus()
    // before the record's own key handler (on document), so Escape and the arrows stay here
    const onKey = (e: KeyboardEvent) => {
      if (['Escape', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        e.stopPropagation()
        e.preventDefault()
        if (e.key === 'Escape') onCloseRef.current()
        else onArrowRef.current?.(e.key === 'ArrowLeft' ? -1 : 1)
      }
    }
    window.addEventListener('keydown', onKey, true)
    return () => {
      window.removeEventListener('keydown', onKey, true)
      previous?.focus()
    }
  }, [])
  return closeRef
}

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
  const t = useT().record
  const closeRef = useLightboxKeys(onClose)

  // fixed over the whole window (no ancestor of the record transforms it)
  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={`${t.photo} ${name}`} onClick={onClose}>
      <button ref={closeRef} type="button" className="lightbox-close" onClick={onClose} aria-label={t.closePhoto}>
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
            {t.photo} {href ? <a href={href} target="_blank" rel="noopener noreferrer">{t.photoCredit(credit)}</a> : t.photoCredit(credit)}
          </span>
        </figcaption>
      </figure>
    </div>
  )
}
