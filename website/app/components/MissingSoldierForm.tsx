'use client'

import { useEffect, useRef, useState } from 'react'
import { shrinkPhoto } from '@/app/lib/images'
import { FORMSUBMIT_AJAX, looksLikeEmail, mailtoHref, wasDelivered } from '@/app/lib/formsubmit'
import { sendAttachments, type Attachment } from '@/app/lib/attachments'
import { useLang, useT } from '@/app/i18n/LangContext'
import { LANG_NAMES } from '@/app/i18n/config'
import s from './MissingSoldierForm.module.css'

// As in KnowSoldierForm: the text goes through FormSubmit's AJAX endpoint (so we know it arrived), each file after it in
// a message of its own, through the site's /api/prilog, which waits for FormSubmit's answer (lib/attachments.ts).
const MAX_FILE_BYTES = 9_500_000
const MAX_FILES = 6
const FATES = ['unknown', 'fell', 'died', 'missing', 'survived'] as const
type Fate = (typeof FATES)[number]

type Status = 'closed' | 'open' | 'sending' | 'sent' | 'error'

// "Not on the site": a family that knows a man fought with the Partisans but finds him in no book here sends what they
// know, with photos of him and of his papers (the user's promise on Reddit, 2026-11-19). It reaches us by email only:
// nothing is published by itself; a man is added by hand after a check, as the family archive's are
// (docs/FAMILY_CONTRIBUTIONS.md). Offered where a search finds no one, and under the results, since he may not be
// among them. The form speaks the page's language; the email to us is in Serbo-Croatian and names the language used.
// The home page also offers it under the search field (MissingSoldierAsk) and from the footer (/#prijava): that one
// opens at once (startOpen) and is taken away again on "Otkaži" (onClose). On a unit's page the unit's name fills the
// unit field (unitName), which the visitor may change.
export default function MissingSoldierForm({ query, unitName, startOpen = false, onClose }: {
  query?: string
  unitName?: string
  startOpen?: boolean
  onClose?: () => void
}) {
  const lang = useLang()
  const t = useT().missing
  const [status, setStatus] = useState<Status>(startOpen ? 'open' : 'closed')
  const [soldier, setSoldier] = useState(() => (startOpen ? query?.trim() ?? '' : ''))
  const firstField = useRef<HTMLInputElement>(null)
  // opened from the line under the search field, the form takes the focus, which also brings it into view
  useEffect(() => {
    if (startOpen) firstField.current?.focus()
  }, [startOpen])
  const [father, setFather] = useState('')
  const [born, setBorn] = useState('')
  const [birthplace, setBirthplace] = useState('')
  const [unit, setUnit] = useState(unitName ?? '')
  const [fate, setFate] = useState<Fate>('unknown')
  const [story, setStory] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [fileError, setFileError] = useState('')
  const [relation, setRelation] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [mayPublish, setMayPublish] = useState(false)
  const [mayShowName, setMayShowName] = useState(false)
  const [sendingFile, setSendingFile] = useState<[number, number] | null>(null)
  const [lost, setLost] = useState<Attachment[]>([])
  const fileInput = useRef<HTMLInputElement>(null)

  const canSend = soldier.trim() && name.trim() && (story.trim() || files.length > 0 || unit.trim() || birthplace.trim())
  // what is missing, said when "Pošalji" is pressed, not a grey button that says nothing (2026-11-23)
  const [missing, setMissing] = useState('')

  const addFiles = (chosen: FileList | null) => {
    setFileError('')
    const list = Array.from(chosen ?? [])
    if (fileInput.current) fileInput.current.value = ''
    if (list.some((f) => !f.type.startsWith('image/'))) {
      setFileError(t.notImage)
      return
    }
    const all = [...files, ...list]
    if (all.length > MAX_FILES) setFileError(t.tooMany(MAX_FILES))
    setFiles(all.slice(0, MAX_FILES))
  }

  const send = async () => {
    if (!canSend) {
      const [which, words] = !soldier.trim() ? ['missing-soldier', t.needSoldier]
        : !name.trim() ? ['missing-name', t.needName] : ['missing-story', t.needSomething]
      setMissing(words)
      document.getElementById(which)?.focus()
      return
    }
    setMissing('')
    setStatus('sending')
    const fields: Record<string, string> = {
      _subject: `Borac kojeg nema na sajtu: ${soldier.trim()}`,
      _template: 'table',
      Borac: soldier.trim(),
      'Ime oca': father.trim(),
      'Godina rođenja': born.trim(),
      'Mesto rođenja': birthplace.trim(),
      Jedinica: unit.trim(),
      Sudbina: { unknown: 'ne zna', fell: 'poginuo', died: 'umro u ratu', missing: 'nestao', survived: 'preživeo rat' }[fate],
      'Šta zna': story.trim(),
      'Veza sa borcem': relation.trim(),
      'Ime pošiljaoca': name.trim(),
      'Email pošiljaoca': email.trim(),
      'Dozvola za objavu teksta i fotografija': mayPublish ? 'Da' : 'Ne',
      'Dozvola za objavu imena pošiljaoca': mayPublish && mayShowName ? 'Da, prvo slovo imena, prezime i srodstvo' : 'Ne',
      Pretraga: query?.trim() ?? '',
      Jezik: LANG_NAMES[lang].name,
      Prilozi: files.length ? `${files.length}, stižu u posebnim porukama („Prilog: …“)` : 'nema',
    }
    if (looksLikeEmail(email)) fields._replyto = email.trim()

    try {
      const blobs: Blob[] = []
      for (const file of files) {
        const blob = await shrinkPhoto(file)
        if (blob.size > MAX_FILE_BYTES) {
          setFileError(t.tooLarge(file.name))
          setStatus('open')
          return
        }
        blobs.push(blob)
      }
      const res = await fetch(FORMSUBMIT_AJAX, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(fields),
      })
      if (!(await wasDelivered(res))) {
        setStatus('error')
        return
      }
      // one message a file, each waited for; those that still didn't arrive are named, with a button to send them again
      const items: Attachment[] = blobs.map((blob, i) => ({
        name: files[i].name,
        subject: `Prilog: ${soldier.trim()} (${i + 1}/${blobs.length})`,
        field: 'Prilog',
        // one word: FormSubmit's regular endpoint writes a space in a field's name as "_" ("Ime_pošiljaoca")
        fields: { Borac: soldier.trim(), Pošiljalac: name.trim() },
        replyTo: email.trim() || undefined,
        blob,
        filename: `prilog-${i + 1}.${blob.type === 'image/jpeg' ? 'jpg' : files[i].name.split('.').pop() || 'jpg'}`,
      }))
      setLost(await sendAttachments(items, (n, of) => setSendingFile([n, of])))
      setSendingFile(null)
      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'closed') {
    return (
      <div className={`know-soldier ${s.callout}`}>
        <p>{t.prompt}</p>
        {/* the name searched for fills the form's first field, unless the visitor has written one */}
        <button type="button" className="btn btn-secondary" onClick={() => { setSoldier((v) => v || query?.trim() || ''); setStatus('open') }}>
          {t.open}
        </button>
      </div>
    )
  }

  const sendAgain = async () => {
    const again = await sendAttachments(lost, (n, of) => setSendingFile([n, of]))
    setSendingFile(null)
    setLost(again)
  }

  if (status === 'sent') {
    return (
      <div className="know-soldier" role="status">
        <p className="know-soldier-done">
          {t.thanks}
          {email.trim() && ` ${t.willReply}`}
        </p>
        {lost.length > 0 && (
          <>
            <p className="know-error">{t.filesLost(lost.map((a) => a.name).join(', '))}</p>
            <button type="button" className="btn btn-secondary" onClick={sendAgain} disabled={!!sendingFile}>
              {sendingFile ? t.sendingFile(...sendingFile) : t.sendAgain}
            </button>
          </>
        )}
      </div>
    )
  }

  return (
    <form className={`know-soldier know-soldier-form ${s.form}`} onSubmit={(e) => { e.preventDefault(); send() }}>
      <h3>{t.title}</h3>
      <p className="know-hint">{t.intro}</p>

      <label htmlFor="missing-soldier">{t.soldier} <span className="know-optional">{t.required}</span></label>
      <input ref={firstField} id="missing-soldier" value={soldier} onChange={(e) => setSoldier(e.target.value)} maxLength={160} autoComplete="off" />

      <div className={s.row}>
        <div>
          <label htmlFor="missing-father">{t.father} <span className="know-optional">{t.optional}</span></label>
          <input id="missing-father" value={father} onChange={(e) => setFather(e.target.value)} maxLength={80} autoComplete="off" />
        </div>
        <div>
          <label htmlFor="missing-born">{t.born} <span className="know-optional">{t.optional}</span></label>
          <input id="missing-born" value={born} onChange={(e) => setBorn(e.target.value)} maxLength={20} inputMode="numeric"
            placeholder={t.bornHint} autoComplete="off" />
        </div>
        <div>
          <label htmlFor="missing-place">{t.birthplace} <span className="know-optional">{t.optional}</span></label>
          <input id="missing-place" value={birthplace} onChange={(e) => setBirthplace(e.target.value)} maxLength={120} autoComplete="off" />
        </div>
      </div>

      <div className={s.row2}>
        <div>
          <label htmlFor="missing-unit">{t.unit} <span className="know-optional">{t.optional}</span></label>
          <input id="missing-unit" value={unit} onChange={(e) => setUnit(e.target.value)} maxLength={160} placeholder={t.unitHint} autoComplete="off" />
        </div>
        <div>
          <label htmlFor="missing-fate">{t.fate}</label>
          <select id="missing-fate" className={s.select} value={fate} onChange={(e) => setFate(e.target.value as Fate)}>
            {FATES.map((f) => <option key={f} value={f}>{t.fates[f]}</option>)}
          </select>
        </div>
      </div>

      <label htmlFor="missing-story">{t.story}</label>
      <textarea id="missing-story" value={story} onChange={(e) => setStory(e.target.value)} rows={5} maxLength={6000} placeholder={t.storyHint} />

      <span className="know-label">{t.files} <span className="know-optional">{t.optional}</span></span>
      <p className="know-hint">{t.filesHint(MAX_FILES)}</p>
      <div className="know-file">
        <input ref={fileInput} id="missing-files" type="file" accept="image/*" multiple className="visually-hidden"
          onChange={(e) => addFiles(e.target.files)} />
        <label htmlFor="missing-files" className="btn btn-secondary">{files.length ? t.addMore : t.chooseFiles}</label>
      </div>
      {files.length > 0 && (
        <ul className={s.files}>
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`}>
              <span className="know-file-name">{f.name}</span>
              <button type="button" className="report-error-link" onClick={() => setFiles(files.filter((_, k) => k !== i))}>{t.remove}</button>
            </li>
          ))}
        </ul>
      )}
      {fileError && <p className="know-error">{fileError}</p>}

      <div className={s.row}>
        <div>
          <label htmlFor="missing-name">{t.name} <span className="know-optional">{t.required}</span></label>
          <input id="missing-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} autoComplete="name" />
        </div>
        <div>
          <label htmlFor="missing-relation">{t.relation} <span className="know-optional">{t.optional}</span></label>
          <input id="missing-relation" value={relation} onChange={(e) => setRelation(e.target.value)} maxLength={120} placeholder={t.relationHint} />
        </div>
        <div>
          <label htmlFor="missing-email">{t.email} <span className="know-optional">{t.optional}</span></label>
          <input id="missing-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} maxLength={160} autoComplete="email" />
        </div>
      </div>
      <p className="know-hint">{t.emailHint}</p>

      {/* two permissions, asked apart, as in KnowSoldierForm: what was sent, and the sender's name beside it */}
      <span className="know-label">{t.consentTitle}</span>
      <p className="know-hint">{t.consentHint}</p>
      <label className="know-check">
        <input type="checkbox" checked={mayPublish} onChange={(e) => { setMayPublish(e.target.checked); if (!e.target.checked) setMayShowName(false) }} />
        {t.consent}
      </label>
      <label className="know-check">
        <input type="checkbox" checked={mayShowName} disabled={!mayPublish} onChange={(e) => setMayShowName(e.target.checked)} />
        {t.consentName}
      </label>

      {missing && status !== 'sending' && <p className="know-error" role="alert">{missing}</p>}
      {status === 'error' && (
        <p className="know-error" role="alert">
          {t.error}{' '}{t.fallback(process.env.NEXT_PUBLIC_REPORT_EMAIL ?? '')}{' '}
          <a href={mailtoHref(`Borac kojeg nema na sajtu: ${soldier.trim()}`, [
            ['Borac', soldier], ['Ime oca', father], ['Godina rođenja', born], ['Mesto rođenja', birthplace], ['Jedinica', unit],
            ['Šta zna', story], ['Ime pošiljaoca', name], ['Veza sa borcem', relation], ['Email pošiljaoca', email],
            ['Dozvola za objavu teksta i fotografija', mayPublish ? 'Da' : 'Ne'],
            ['Dozvola za objavu imena pošiljaoca', mayPublish && mayShowName ? 'Da, prvo slovo imena, prezime i srodstvo' : 'Ne'],
          ])}>{t.openMail}</a>
        </p>
      )}

      <div className="report-actions">
        <button type="submit" className="btn btn-primary" disabled={status === 'sending'}>
          {status === 'sending' ? (sendingFile ? t.sendingFile(...sendingFile) : t.sending) : t.send}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => { setStatus('closed'); onClose?.() }}>{t.cancel}</button>
      </div>
    </form>
  )
}

// "· Nema vašeg borca? Pošaljite nam šta znate o njemu": the rest of the line under the home search field, after the
// count of names (finder-hint, a wrapping flex row). On a phone the dot goes and the question takes a line of its own.
export function MissingSoldierAsk({ open, onOpen }: { open: boolean; onOpen: () => void }) {
  const t = useT().missing
  return (
    <>
      <span className={s.askDot} aria-hidden="true">·</span>
      <span className={s.ask}>
        {t.ask}{' '}
        <button type="button" aria-expanded={open} onClick={onOpen}>{t.askLink}</button>
      </span>
    </>
  )
}
