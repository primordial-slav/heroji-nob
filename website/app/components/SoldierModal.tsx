'use client'

import { lazy, Suspense, useCallback, useEffect, useId, useRef, useState } from 'react'
import type { Soldier, SoldierSource } from '@/app/lib/types'
import { SoldierName } from './SoldierResults'
import { ChevronLeftIcon, ChevronRightIcon, CloseIcon } from './Icons'
import { entriesOf, hasPage, isFamily, isMuseum, isPoreklo, unitByName } from '@/app/lib/records'
import { sourceTitle } from '@/app/lib/recordSources'
import { recordFacts, type Fact as RecordFact, type FactKey } from '@/app/lib/recordFacts'
import { loadKin, type Kin } from '@/app/lib/searchIndex'
import { units } from '@/app/data/units'
import { photoPosition } from '@/app/data/photoFocus'
import RecordActions from './RecordActions'
import { SoldierMedals, honoursLine } from './Medal'
import { wasDelivered } from '@/app/lib/formsubmit'
import KnowSoldierForm from './KnowSoldierForm'
import FamilyStory from './FamilyStory'
import { contributionsFor } from '@/app/data/family'
import RelationsTree, { type KinCounts, type KinPart, type KinRequest } from './RelationsTree'
import LifeLine from './LifeLine'
import SoldierPortrait from './SoldierPortrait'
import { portraitFor } from '@/app/data/portraits'
import { useLang, useLocalePath, useT, useUnitText, type UnitNames } from '@/app/i18n/LangContext'
import { LANG_NAMES, type Lang } from '@/app/i18n/config'
import { quoteMarks } from '@/app/i18n/format'
import { titlePart } from '@/app/i18n/sourceNames'
import RichText from '@/app/i18n/RichText'
import { unitImageProps } from '@/app/lib/unitImage'

// The unit photo spans the dialog: the whole screen up to 640px, the dialog above (52rem with the life line)
const RECORD_PHOTO_SIZES = '(max-width: 640px) 100vw, 832px'

// Lazy-load PdfViewer so PDF.js (~500KB) is not in the initial bundle
const PdfViewer = lazy(() => import('./PdfViewer'))

/** A book's title with the list it names after " — " in the page's language ("tom 3" is "volume 3" in English);
 *  the Cyrillic pages keep the title as it is, the book's name and the list in one script */
function bookTitle(entry: SoldierSource, lang: Lang): string {
  const title = sourceTitle(entry)
  const cut = title.lastIndexOf(' — ')
  return cut < 0 || lang === 'sr-cyrl' ? title : `${title.slice(0, cut)} — ${titlePart(title, lang)}`
}

/** A unit's name (as the records give it, in Serbo-Croatian) in the page's language */
function shownUnitName(name: string, lang: Lang, unitText: UnitNames): string {
  const unit = unitByName(name)
  return unit ? unitText.name(unit) : quoteMarks(lang, name)
}

interface Fact extends RecordFact {
  link?: { text: string; open: () => void }
}

interface SoldierModalProps {
  soldier: Soldier
  unitName?: string
  // Opens another record in this dialog: the one before or after this one in the unit's list, a name in the trees
  onOpen?: (soldier: Soldier) => void
  onClose: () => void
}

export default function SoldierModal({ soldier, unitName, onOpen, onClose }: SoldierModalProps) {
  const lang = useLang()
  const unitText = useUnitText()
  const t = useT()
  const to = useLocalePath()
  // The soldier's own entry, then the same soldier's entries in the unit's other books
  const entries: SoldierSource[] = entriesOf(soldier)
  const pages = entries.filter(hasPage)
  const [shownPage, setShownPage] = useState(0)
  const page = pages[Math.min(shownPage, pages.length - 1)]
  // the line over the page viewer: the book and its page
  const bookLabel = (e: SoldierSource) => `${bookTitle(e, lang)}, ${t.record.page(e.pdf_page!)}`
  const sourceHref = page?.pdf_file ? to(`/izvori#${page.pdf_file.replace('.pdf', '')}`) : undefined
  const unit = unitName || soldier.unit
  const unitRecord = unitByName(unit)
  const portrait = portraitFor(soldier)
  // the units of the soldier's entries from other units' books (a link): he is listed in each of them
  const unitOf = (e: SoldierSource) => units.find((u) => u.dataFile === `/${e.unit_file}`)?.name
  const allUnits = [unit, ...entries.map((e) => (e.unit_file ? unitOf(e) : undefined))]
    .filter((u, i, list): u is string => Boolean(u) && list.indexOf(u) === i)
  const hasLine = (soldier.life_events?.length ?? 0) > 0
  // The record's own entry stays open; its other books fold under it
  const [moreOpen, setMoreOpen] = useState(false)
  const moreId = useId()

  const [showReportForm, setShowReportForm] = useState(false)
  const [reportText, setReportText] = useState('')
  const [reportStatus, setReportStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const dialogRef = useRef<HTMLDivElement>(null)
  const pageRef = useRef<HTMLElement>(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  // A step of the life line shows its entry: that book's page, and the entry's box flashing on it
  const [flash, setFlash] = useState(0)
  const showEntry = (i: number) => {
    const at = pages.indexOf(entries[i])
    if (at < 0) return
    setShownPage(at)
    setFlash((f) => f + 1)
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    pageRef.current?.scrollIntoView({ block: 'nearest', behavior: reduce ? 'auto' : 'smooth' })
  }
  // An entry's line: the other unit, the book, its page, the name as printed there. A list published as a web
  // page links to it; a book whose scan is not on the site, or a family's archive, is only named.
  const entryLabel = (e: SoldierSource) => (
    <>
      {/* the other unit's name, unless the book's title already starts with it */}
      {e.unit_file && unitOf(e) && !sourceTitle(e).startsWith(unitOf(e)!.split(' „')[0]) && <>{shownUnitName(unitOf(e)!, lang, unitText)}: </>}
      {e.source_url && !e.pdf_file && !isPoreklo(e.source_url) && !isFamily(e.source_url)
        ? <a href={e.source_url} target="_blank" rel="noopener noreferrer">{bookTitle(e, lang)}</a>
        : bookTitle(e, lang)}
      {(e.pdf_page ?? e.source_page) != null && `, ${t.record.page((e.pdf_page ?? e.source_page)!)}`}
      {e.name && e.name !== soldier.full_name && <>. {t.record.nameInBook} {e.name}</>}
    </>
  )
  const pageOf = (i: number) => (entries[i] && hasPage(entries[i]) ? entries[i].pdf_page : undefined)

  // The facts link to the folds at the end: how many are in them, and a request to open one on a group
  const [counts, setCounts] = useState<Record<KinPart, KinCounts>>({ comrades: {}, neighbours: {} })
  const onCounts = useCallback((part: KinPart, c: KinCounts) => setCounts((old) => ({ ...old, [part]: c })), [])
  const [kinRequest, setKinRequest] = useState<KinRequest | null>(null)
  const openKin = (part: KinPart, group: KinRequest['group']) => setKinRequest({ part, group, nonce: Date.now() })

  // A new soldier in the same dialog (Prethodni / Sledeći, a name in the trees) starts from his own first book
  useEffect(() => {
    setShownPage(0)
    setFlash(0)
    setMoreOpen(false)
    setKinRequest(null)
    // the counts are not cleared here: on a first opening the folds may have counted him before this runs
  }, [soldier.soldier_id])

  // The record's kin in its unit, which the server finds for it (loadKin): the entries before and after this one in
  // the unit's list, which is in the order of the books, and the comrades tree's groups
  const [kin, setKin] = useState<Kin | null>(null)
  useEffect(() => {
    if (!unitRecord) return
    let live = true
    loadKin(unitRecord, soldier.soldier_id).then((found) => live && setKin(found)).catch(() => {})
    return () => { live = false }
  }, [unitRecord, soldier.soldier_id])
  const previous = onOpen ? kin?.previous : undefined
  const next = onOpen ? kin?.next : undefined
  const stepRef = useRef({ previous, next, onOpen })
  stepRef.current = { previous, next, onOpen }

  // Close on Escape, step through the list with the arrow keys, keep the page behind from scrolling,
  // and move focus into the dialog
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCloseRef.current()
      if ((e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return
      const target = e.target
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest('input, textarea, select'))) return
      const { previous, next, onOpen } = stepRef.current
      const to = e.key === 'ArrowLeft' ? previous : next
      if (to && onOpen) {
        e.preventDefault()
        onOpen(to)
      }
    }
    document.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialogRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      previousFocus?.focus()
    }
  }, [])

  const handleReport = async () => {
    if (!reportText.trim()) return
    setReportStatus('sending')
    try {
      const res = await fetch(`https://formsubmit.co/ajax/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({
          _subject: `Prijava greške: ${soldier.full_name} (${soldier.soldier_id})`,
          Borac: soldier.full_name,
          ID: soldier.soldier_id,
          Jedinica: unit || '',
          Jezik: LANG_NAMES[lang].name,
          'Opis greške': reportText,
        }),
      })
      setReportStatus((await wasDelivered(res)) ? 'sent' : 'error')
    } catch {
      setReportStatus('error')
    }
  }

  const honours = honoursLine(soldier, t)

  // The record's facts (lib/recordFacts.ts, the memorial card's too); the birth, the unit and the death link to the
  // people they share with others. Only the counts made for this soldier; the last one's until the folds have counted his
  const counted = (c: KinCounts): KinCounts => (c.of === soldier.soldier_id ? c : {})
  const comrades = counted(counts.comrades)
  const neighbours = counted(counts.neighbours)
  const links: Partial<Record<FactKey, Fact['link']>> = {
    born: neighbours.place ? { text: t.life.neighbours(neighbours.place.others), open: () => openKin('neighbours', 'place') } : undefined,
    unit: comrades.unit ? { text: t.life.comrades(comrades.unit.size), open: () => openKin('comrades', 'unit') } : undefined,
    death: comrades.sameDay ? { text: t.life.sameDay(comrades.sameDay), open: () => openKin('comrades', 'day') } : undefined,
  }
  const facts: Fact[] = recordFacts(soldier, t, unitRecord?.name ?? unit).map((f) => ({ ...f, link: links[f.key] }))

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={dialogRef}
        className={`modal-content${hasLine ? ' has-line' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="soldier-name"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label={t.record.close}>
          <CloseIcon size={22} />
        </button>

        {unitRecord && !unitRecord.image.includes('/pdf-thumbs/') && (
          <div className="record-photo">
            <img {...unitImageProps(unitRecord.image, RECORD_PHOTO_SIZES)} alt="" style={{ objectPosition: photoPosition(unitRecord.id) }} />
          </div>
        )}
        <SoldierMedals soldier={soldier} look="foto" className="modal-medals" />
        <div className="modal-head">
          <SoldierPortrait soldier={soldier} unitId={unitRecord?.id} portrait={portrait} className="modal-portrait" framed />
          <div>
            <h2 className="modal-title" id="soldier-name"><SoldierName soldier={soldier} /></h2>
            {allUnits.length > 0 && <p className="modal-unit">{allUnits.map((u) => shownUnitName(u, lang, unitText)).join(' · ')}</p>}
            {honours && <p className="modal-honours">{honours}</p>}
            {portrait && (
              <p className="modal-portrait-credit">
                {t.record.photo} {portrait.href
                  ? <a href={portrait.href} target="_blank" rel="noopener noreferrer">{t.record.photoCredit(portrait.credit)}</a>
                  : t.record.photoCredit(portrait.credit)}
              </p>
            )}
          </div>
        </div>
        <FamilyStory items={contributionsFor(soldier.soldier_id, (soldier.other_sources ?? []).map((o) => o.soldier_id))} />

        <div className="record-body">
          {facts.length > 0 && (
            <dl className="record-facts">
              {facts.map((f) => (
                <div key={f.key} style={{ display: 'contents' }}>
                  <dt>{f.label}</dt>
                  <dd>
                    <span>{f.value}</span>
                    {f.link && (
                      <button type="button" className="record-fact-link" onClick={f.link.open}>
                        {f.link.text}<ChevronRightIcon size={14} />
                      </button>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          )}

          {hasLine && (
            <aside className="record-line">
              <LifeLine soldier={soldier} entries={entries} unitName={unitRecord?.name ?? unit} pageOf={pageOf} onShow={showEntry} />
            </aside>
          )}

          <section className="record-page" ref={pageRef}>
            <div className="modal-source-head">
              <h3>{page || !soldier.source_url ? t.record.references : t.record.source}</h3>
            </div>

            {entries.length === 1 && soldier.additional_info && (
              <p className="modal-entry">{soldier.additional_info}</p>
            )}

            {entries.length > 1 && (
              <div className="record-entries">
                <p className="modal-source-label">{entryLabel(entries[0])}</p>
                {entries[0].additional_info && <p className="modal-entry">{entries[0].additional_info}</p>}
                <div className="entries-more">
                  <button type="button" className="entries-more-button" aria-expanded={moreOpen} aria-controls={moreId}
                    onClick={() => setMoreOpen((open) => !open)}>
                    <ChevronRightIcon size={16} />
                    <span>{t.record.moreEntries(entries.length - 1)}</span>
                  </button>
                  {moreOpen ? (
                    <ol className="modal-sources entries-more-list" id={moreId} aria-label={t.record.entries}>
                      {entries.slice(1).map((e, k) => (
                        <li key={k} className="modal-source-entry">
                          <p className="modal-source-label">{entryLabel(e)}</p>
                          {e.additional_info && <p className="modal-entry">{e.additional_info}</p>}
                          {hasPage(e) && (
                            <button type="button" className="entry-show-page" onClick={() => showEntry(k + 1)}>
                              {t.record.showPage}
                            </button>
                          )}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    // the books it holds, each named once
                    <p className="entries-more-books">
                      {entries.slice(1).map((e) => sourceTitle(e).split(' — ')[0])
                        .filter((b, i, list) => list.indexOf(b) === i).join(' · ')}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Over the viewer, outside it, so the menu keeps its focus while the other book's page loads: the book
                shown, and with more than one, a menu of the others (the select lies unseen over the name) */}
            {page && (
              <div className="pdf-book-bar">
                {pages.length > 1 ? (
                  <label className="pdf-book">
                    <span className="pdf-book-name" aria-hidden="true">{bookLabel(page)}</span>
                    <ChevronRightIcon size={14} />
                    <select aria-label={t.record.book} value={pages.indexOf(page)} onChange={(ev) => setShownPage(Number(ev.target.value))}>
                      {pages.map((e, i) => <option key={i} value={i}>{bookLabel(e)}</option>)}
                    </select>
                  </label>
                ) : (
                  <span className="pdf-book-name">{bookLabel(page)}</span>
                )}
              </div>
            )}
            {page && (
              <Suspense fallback={<div className="pdf-viewer-loading">{t.record.loadingPage}</div>}>
                <PdfViewer
                  key={`${page.pdf_file}#${page.pdf_page}#${page.pdf_y}`}
                  pdfFile={`/pdfs/${page.pdf_file}`}
                  pageNumber={page.pdf_page!}
                  yPosition={page.pdf_y ?? 0}
                  yPositionEnd={page.pdf_y_end}
                  xPosition={page.pdf_x ?? 0}
                  xPositionLeft={page.pdf_x_left}
                  xPositionEnd={page.pdf_x_end}
                  rects={page.pdf_rects}
                  sourceHref={sourceHref}
                  flash={flash}
                />
              </Suspense>
            )}

            {!page && soldier.source_url && (
              <p className="modal-source-note">
                {/* a book whose scan is not on the site is named with its page, not linked; so is a family's archive */}
                {isPoreklo(soldier.source_url) || isFamily(soldier.source_url)
                  ? t.record.noScanBook(bookTitle(soldier, lang), soldier.source_page ?? null)
                  : <RichText text={isMuseum(soldier.source_url) ? t.record.noScanMuseum(bookTitle(soldier, lang)) : t.record.noScan}
                      render={(part) => <a href={soldier.source_url} target="_blank" rel="noopener noreferrer">{part}</a>} />}
              </p>
            )}
          </section>
        </div>

        {unitRecord && (
          <div className="record-folds">
            <RelationsTree part="comrades" soldier={soldier} unit={unitRecord} kin={kin} onOpen={onOpen}
              request={kinRequest} onCounts={onCounts} />
            <RelationsTree part="neighbours" soldier={soldier} unit={unitRecord} kin={kin} onOpen={onOpen}
              request={kinRequest} onCounts={onCounts} />
          </div>
        )}

        <RecordActions soldier={soldier} unit={unitRecord} />

        <KnowSoldierForm soldier={soldier} unit={unitRecord} />

        {!showReportForm && reportStatus === 'idle' && (
          <button className="report-error-link" onClick={() => setShowReportForm(true)}>
            {t.report.open}
          </button>
        )}

        {showReportForm && reportStatus === 'idle' && (
          <div className="report-form">
            <label htmlFor="report-text">{t.report.label}</label>
            <textarea
              id="report-text"
              className="report-textarea"
              placeholder={t.report.hint}
              value={reportText}
              onChange={(e) => setReportText(e.target.value)}
              rows={3}
              maxLength={2000}
            />
            <div className="report-actions">
              <button className="btn btn-primary" onClick={handleReport} disabled={!reportText.trim()}>
                {t.report.send}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => { setShowReportForm(false); setReportText('') }}
              >
                {t.report.cancel}
              </button>
            </div>
          </div>
        )}

        {reportStatus === 'sending' && <p className="report-status">{t.report.sending}</p>}
        {reportStatus === 'sent' && (
          <p className="report-status report-success">{t.report.sent}</p>
        )}
        {reportStatus === 'error' && (
          <p className="report-status report-error-msg">
            <RichText
              text={t.report.failed}
              render={(part) => (
                <button className="report-error-link" style={{ marginTop: 0 }} onClick={() => setReportStatus('idle')}>
                  {part}
                </button>
              )}
            />
          </p>
        )}

        {(previous || next) && (
          <nav className="record-steps" aria-label={t.record.steps}>
            {previous ? (
              <button type="button" className="record-step" onClick={() => onOpen!(previous)}>
                <span className="record-step-label"><ChevronLeftIcon size={16} /> {t.record.previous}</span>
                <span className="record-step-name">{previous.full_name}</span>
              </button>
            ) : <span />}
            {next && (
              <button type="button" className="record-step record-step-next" onClick={() => onOpen!(next)}>
                <span className="record-step-label">{t.record.next} <ChevronRightIcon size={16} /></span>
                <span className="record-step-name">{next.full_name}</span>
              </button>
            )}
          </nav>
        )}
      </div>
    </div>
  )
}
