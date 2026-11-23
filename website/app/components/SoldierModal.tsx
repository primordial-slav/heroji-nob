'use client'

import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import type { Soldier, SoldierSource } from '@/app/lib/types'
import { SoldierName } from './SoldierResults'
import { ChevronDownIcon, ChevronLeftIcon, ChevronRightIcon, CloseIcon } from './Icons'
import { entriesOf, hasPage, isFamily, isPoreklo, unitByName } from '@/app/lib/records'
import { sourceTitle } from '@/app/lib/recordSources'
import { recordFacts, type Fact as RecordFact, type FactKey } from '@/app/lib/recordFacts'
import { eventLines } from '@/app/lib/warEvents'
import { loadKin, type Kin } from '@/app/lib/searchIndex'
import type { RecordWalk } from '@/app/lib/useRecordWalk'
import { units } from '@/app/data/units'
import { photoPosition } from '@/app/data/photoFocus'
import RecordActions from './RecordActions'
import EntryStrip from './EntryStrip'
import { SoldierMedals, honoursLine } from './Medal'
import { wasDelivered } from '@/app/lib/formsubmit'
import KnowSoldierForm from './KnowSoldierForm'
import FamilyStory from './FamilyStory'
import FamilyMark, { FamilyDot } from './FamilyMark'
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
  /** Opened from a search: its results, in place of the unit's list, for the record before and after this one */
  walk?: RecordWalk
  onClose: () => void
}

export default function SoldierModal({ soldier, unitName, onOpen, walk, onClose }: SoldierModalProps) {
  const lang = useLang()
  const unitText = useUnitText()
  const t = useT()
  const to = useLocalePath()
  // The soldier's own entry, then the same soldier's entries in the unit's other books
  const entries: SoldierSource[] = entriesOf(soldier)
  const pages = entries.filter(hasPage)
  const references = entries.filter((e) => hasPage(e) || e.additional_info || e.source_url)
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
  // a unit the family names that isn't on the site stands for "Borci drugih jedinica" (the user, 2026-11-23, Ivančić Paško)
  const allUnits = [soldier.unit_name || unit, ...entries.map((e) => (e.unit_file ? unitOf(e) : undefined))]
    .filter((u, i, list): u is string => Boolean(u) && list.indexOf(u) === i)
  const hasLine = (soldier.life_events?.length ?? 0) > 0
  // With the printed lines shown, the page they come from folds, as the comrades do, till it is asked for
  const foldPage = pages.length > 0
  const [pageOpen, setPageOpen] = useState(false)

  const [showReportForm, setShowReportForm] = useState(false)
  const [reportText, setReportText] = useState('')
  // the sender's address, optional, and whether we may answer there (on by default: the user, 2026-11-23)
  const [reportEmail, setReportEmail] = useState('')
  const [reportMayReply, setReportMayReply] = useState(true)
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
    setPageOpen(true)
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    pageRef.current?.scrollIntoView({ block: foldPage ? 'start' : 'nearest', behavior: reduce ? 'auto' : 'smooth' })
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
    setPageOpen(false)
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
  const previous = onOpen ? (walk ? walk.previous : kin?.previous) : undefined
  const next = onOpen ? (walk ? walk.next : kin?.next) : undefined
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
          // the address only when we may answer there: one we may not use is not kept (00's review, 2026-11-23)
          'Email pošiljaoca': reportEmail.trim() && reportMayReply ? reportEmail.trim() : '',
          'Dozvola za odgovor': reportEmail.trim() ? (reportMayReply ? 'Da' : 'Ne') : '',
          ...(reportEmail.trim() && reportMayReply ? { _replyto: reportEmail.trim() } : {}),
        }),
      })
      setReportStatus((await wasDelivered(res)) ? 'sent' : 'error')
    } catch {
      setReportStatus('error')
    }
  }

  const honours = honoursLine(soldier, t)

  // The record's facts (lib/recordFacts.ts, the memorial card's too); the death links to those who fell the same day.
  // Only the count made for this soldier; the last one's until the fold has counted his
  const comrades: KinCounts = counts.comrades.of === soldier.soldier_id ? counts.comrades : {}
  const links: Partial<Record<FactKey, Fact['link']>> = {
    death: comrades.sameDay ? { text: t.life.sameDay(comrades.sameDay), open: () => openKin('comrades', 'day') } : undefined,
  }
  const facts: Fact[] = recordFacts(soldier, t, unitRecord?.name ?? unit, unitText.shortName).map((f) => ({ ...f, link: links[f.key] }))
  const events = eventLines(soldier, t)

  // The page the entry stands on, and nothing else: the entries themselves, each book's, are under "Reference" above
  // (EntryStrip). Until 2026-11-19 the fold also gave the entries as text, a "još N zapisa" fold and the book's name
  // twice more (the user: "messy and redundant and confusing"); now the book and page are named once, over the viewer
  const sourceBody = (
    <>
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
    </>
  )

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
            <h2 className="modal-title" id="soldier-name"><SoldierName soldier={soldier} /><FamilyDot soldier={soldier} title={t.record.familyDot} /></h2>
            {allUnits.length > 0 && <p className="modal-unit">{allUnits.map((u) => (u === soldier.unit_name ? u : shownUnitName(u, lang, unitText))).join(' · ')}</p>}
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
          {(facts.length > 0 || events.length > 0) && (
            <div className="record-facts-area">
              {facts.length > 0 && (
                <dl className="record-facts">
                  {facts.map((f, i) => (
                    <div key={`${f.key}${i}`} style={{ display: 'contents' }}>
                      <dt>{f.label}</dt>
                      <dd>
                        {f.lines ? f.lines.map((line) => (
                          <span key={line.text} className="record-fact-line">
                            {/* in a new tab: the record stays open */}
                            <a href={to(`/units/${line.unit.id}`)} target="_blank" rel="noopener noreferrer">{line.text}</a>
                            {line.rest}
                          </span>
                        )) : <span>{f.value}</span>}
                        {f.family && <FamilyMark title={t.record.fromFamily} />}
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
              {/* what his unit did that he was part of: the Igman march (lib/warEvents.ts) */}
              {events.map((line) => <p key={line} className="record-event">{line}</p>)}
            </div>
          )}

          {hasLine && (
            <aside className="record-line">
              <LifeLine soldier={soldier} entries={entries} unitName={unitRecord?.name ?? unit} pageOf={pageOf} onShow={showEntry} />
            </aside>
          )}
        </div>

        {/* Every book's entry, the printed lines where its scan is on the site, else the text */}
        {references.length > 0 && (
          <EntryStrip
            key={soldier.soldier_id}
            entries={references}
            label={(e) => (hasPage(e) ? bookLabel(e) : entryLabel(e))}
            title={bookLabel}
            onWholePage={(e) => showEntry(entries.indexOf(e))}
          />
        )}
        <RecordActions soldier={soldier} unit={unitRecord} />

        {(unitRecord || foldPage) && (
          <div className="record-folds">
            {foldPage && (
              <section ref={pageRef} className={`record-fold record-fold-page${pageOpen ? ' is-open' : ''}`} aria-label={t.record.wholePage}>
                <button type="button" className="record-fold-row" aria-expanded={pageOpen} onClick={() => setPageOpen((open) => !open)}>
                  <span className="record-fold-text">
                    <span className="record-fold-title">{t.record.wholePage}</span>
                    {/* open, the viewer's own top line names the book and page */}
                    {page && !pageOpen && <span className="record-fold-summary">{bookLabel(page)}</span>}
                  </span>
                  <ChevronDownIcon size={18} />
                </button>
                {pageOpen && sourceBody}
              </section>
            )}
            {unitRecord && (
              <>
                <RelationsTree part="comrades" soldier={soldier} unit={unitRecord} kin={kin} onOpen={onOpen}
                  request={kinRequest} onCounts={onCounts} />
                <RelationsTree part="neighbours" soldier={soldier} unit={unitRecord} kin={kin} onOpen={onOpen}
                  request={kinRequest} onCounts={onCounts} />
              </>
            )}
          </div>
        )}

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
            <label htmlFor="report-email" className="report-email-label">
              {t.report.email} <span className="know-optional">{t.report.optional}</span>
            </label>
            <input
              id="report-email"
              className="report-email"
              type="email"
              value={reportEmail}
              onChange={(e) => setReportEmail(e.target.value)}
              maxLength={160}
              autoComplete="email"
            />
            {/* by its field, and only once an address is there: without one there is nobody to answer */}
            {reportEmail.trim() && (
              <label className="report-check">
                <input type="checkbox" checked={reportMayReply} onChange={(e) => setReportMayReply(e.target.checked)} />
                <span>{t.report.mayReply}</span>
              </label>
            )}
            <p className="know-hint report-hint">{t.report.emailHint}</p>
            <div className="report-actions">
              <button className="btn btn-primary" onClick={handleReport} disabled={!reportText.trim()}>
                {t.report.send}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => { setShowReportForm(false); setReportText(''); setReportEmail(''); setReportMayReply(true) }}
              >
                {t.report.cancel}
              </button>
            </div>
          </div>
        )}

        {reportStatus === 'sending' && <p className="report-status">{t.report.sending}</p>}
        {reportStatus === 'sent' && (
          <p className="report-status report-success">
            {t.report.sent}
            {reportEmail.trim() && reportMayReply && ` ${t.report.willReply}`}
          </p>
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
          <nav className="record-steps" aria-label={walk ? t.record.stepsFound : t.record.steps}>
            {previous ? (
              <button type="button" className="record-step" onClick={() => onOpen!(previous)}>
                <span className="record-step-label"><ChevronLeftIcon size={16} /> {t.record.previous}</span>
                <span className="record-step-name">{previous.full_name}</span>
              </button>
            ) : <span />}
            {walk && <span className="record-step-at">{t.record.stepOf(walk.at, walk.total)}</span>}
            {next ? (
              <button type="button" className="record-step record-step-next" onClick={() => onOpen!(next)}>
                <span className="record-step-label">{t.record.next} <ChevronRightIcon size={16} /></span>
                <span className="record-step-name">{next.full_name}</span>
              </button>
            ) : <span />}
          </nav>
        )}
      </div>
    </div>
  )
}
