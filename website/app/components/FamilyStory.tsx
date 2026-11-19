'use client'

import { useState } from 'react'
import type { FamilyContribution, FamilyPiece } from '@/app/data/family'
import { useT } from '@/app/i18n/LangContext'
import { ChevronLeftIcon, ChevronRightIcon, CloseIcon } from './Icons'
import { useLightboxKeys } from './PhotoLightbox'
import s from './FamilyStory.module.css'

// What a family sent about the soldier: a story, photographs, documents, with who sent it. Their words are shown as sent;
// only the heading, the month and the labels are in the page's language.
//
// One photo alone is his portrait at the top of the record (data/portraits.ts) and isn't shown again. Once a family has
// sent more than that one, every photo and document stands under the story as an album (the user's choice of 2026-11-19,
// variant A of admin/mockups/kartica-*.html on the admin-panel branch), the portrait's photo first; a click opens it in
// a viewer with its pages and what it says (a transcription), the arrows stepping through the pages and the pieces.

/** A piece as the album shows it: its pages (the first is the piece), who sent it and when */
interface ShownPiece extends FamilyPiece {
  all: string[]
  from: string
  date: string
}

export default function FamilyStory({ items }: { items: FamilyContribution[] }) {
  const t = useT().family
  const [open, setOpen] = useState<{ piece: number; page: number } | null>(null)
  const sentOn = (date: string) => {
    const [year, month] = date.split('-').map(Number)
    return t.sent(year, month || undefined)
  }

  const pieces: ShownPiece[] = items.flatMap((item) => [
    ...(item.photo ? [{ kind: 'photo' as const, file: item.photo, caption: item.photoCaption, all: [item.photo], from: item.from, date: item.date }] : []),
    ...(item.pieces ?? []).map((p) => ({ ...p, all: [p.file, ...(p.pages ?? [])], from: item.from, date: item.date })),
  ])
  const portrait = items.find((item) => item.photo)
  // an album when there is more than the portrait: two pieces or more, or a single piece that isn't the portrait (Krnić
  // Blaž's photo in a postwar uniform, kept out of the portrait, had shown nowhere)
  const album = pieces.length > 1 || (pieces.length === 1 && !portrait)
  // Without an album, as before: a story, and a photo that is not the portrait beside its story
  const shown = items
    .map((item) => (album || item === portrait ? { ...item, photo: undefined } : item))
    .filter((item) => item.photo || item.text)
  if (shown.length === 0 && !album) return null

  return (
    <section className="family-story">
      {/* photos from a public page, not the family, say so ("Sa Facebook stranice"); the credit names the page */}
      <h3>{items.every((item) => item.origin === 'facebook') ? t.titleFacebook : t.title}</h3>
      {shown.map((item, i) => (
        <figure key={i} className={item.photo ? 'family-item has-photo' : 'family-item'}>
          {item.photo && <img src={`/porodica/${item.photo}`} alt={item.photoCaption ?? ''} />}
          <figcaption>
            {item.photoCaption && <p className="family-caption">{item.photoCaption}</p>}
            {item.text && <p className="family-text">{item.text}</p>}
            {/* a sender who did not allow his name: the date alone */}
            <p className="family-from">{item.from && `${item.from} · `}{sentOn(item.date)}</p>
          </figcaption>
        </figure>
      ))}
      {album && (
        <ul className={s.album}>
          {pieces.map((piece, i) => (
            <li key={`${piece.file}-${i}`}>
              <button type="button" className={s.piece} data-kind={piece.kind} onClick={() => setOpen({ piece: i, page: 0 })}
                aria-label={t.open(piece.caption ?? t.kind[piece.kind])}>
                <span className={s.image}>
                  <img src={`/porodica/${piece.file}`} alt="" loading="lazy" />
                  {piece.all.length > 1 && <span className={s.pages}>{t.pages(piece.all.length)}</span>}
                </span>
                <span className={s.caption}>{piece.caption ?? t.kind[piece.kind]}</span>
                {piece.caption && <span className={s.kind}>{t.kind[piece.kind]}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      {open && <FamilyViewer pieces={pieces} at={open} onMove={setOpen} onClose={() => setOpen(null)} sentOn={sentOn} />}
    </section>
  )
}

// A piece opened over the page, as large as the screen allows: a photo black and white like every portrait on the site,
// a document as it is. Under it its caption, what it is, the page and who sent it, the page's transcription where there
// is one, and the pages to choose from. The arrows (and the keys) go to the next page, then the next piece. Escape, the
// X or a click beside it closes it, and only it: the record under it stays open.
function FamilyViewer({ pieces, at, onMove, onClose, sentOn }: {
  pieces: ShownPiece[]
  at: { piece: number; page: number }
  onMove: (at: { piece: number; page: number }) => void
  onClose: () => void
  sentOn: (date: string) => string
}) {
  const t = useT().family
  const steps = pieces.flatMap((p, piece) => p.all.map((_, page) => ({ piece, page })))
  const here = steps.findIndex((x) => x.piece === at.piece && x.page === at.page)
  const step = (dir: -1 | 1) => {
    const to = steps[here + dir]
    if (to) onMove(to)
  }
  const closeRef = useLightboxKeys(onClose, step)
  const piece = pieces[at.piece]
  const what = piece.caption ?? t.kind[piece.kind]
  const transcript = piece.transcripts?.[at.page]

  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={what} onClick={onClose}>
      <button ref={closeRef} type="button" className="lightbox-close" onClick={onClose} aria-label={t.close}>
        <CloseIcon size={22} />
      </button>
      <div className={s.viewer} onClick={(e) => e.stopPropagation()}>
        <div className={s.stage}>
          <button type="button" className={s.arrow} onClick={() => step(-1)} disabled={here <= 0} aria-label={t.previous}>
            <ChevronLeftIcon size={20} />
          </button>
          <img key={piece.all[at.page]} className={s.big} data-kind={piece.kind} src={`/porodica/${piece.all[at.page]}`} alt={what} />
          <button type="button" className={s.arrow} onClick={() => step(1)} disabled={here >= steps.length - 1} aria-label={t.next}>
            <ChevronRightIcon size={20} />
          </button>
        </div>
        <div className={s.about}>
          <p className={s.what}>{what}</p>
          <p className={s.meta}>
            {t.kind[piece.kind]}
            {piece.all.length > 1 && <> · {t.page(at.page + 1, piece.all.length)}</>}
            {' · '}{piece.from && `${piece.from} · `}{sentOn(piece.date)}
          </p>
          {transcript && (
            <div className={s.transcript}>
              <p className={s.label}>{t.transcript}</p>
              <p>{transcript}</p>
            </div>
          )}
          {piece.all.length > 1 && (
            <div className={s.thumbs}>
              {piece.all.map((file, page) => (
                <button key={file} type="button" aria-label={t.page(page + 1, piece.all.length)} aria-current={page === at.page || undefined}
                  onClick={() => onMove({ piece: at.piece, page })}>
                  <img src={`/porodica/${file}`} alt="" />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
