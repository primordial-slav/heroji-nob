'use client'

import { useRef, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { recordPath } from '@/app/lib/records'
import { shrinkPhoto } from '@/app/lib/images'
import { wasDelivered } from '@/app/lib/formsubmit'
import { sendAttachments, type Attachment } from '@/app/lib/attachments'
import { useLang, useT } from '@/app/i18n/LangContext'
import { LANG_NAMES } from '@/app/i18n/config'

const ENDPOINT = `https://formsubmit.co/ajax/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`
// The text goes through FormSubmit's AJAX endpoint (so we know it arrived), each file after it in a message of its own,
// through the site's /api/prilog, which waits for FormSubmit's answer (lib/attachments.ts).
// The form service takes at most 10 MB per message (a PDF over 4.3 MB goes to it straight)
const MAX_FILE_BYTES = 9_500_000
const MAX_FILES = 6

type Status = 'closed' | 'open' | 'sending' | 'sent' | 'error'

// "I know this soldier": a family member or researcher sends what they know, optionally with a photograph.
// It arrives by email; approved items are added by hand to app/data/family.ts (docs/FAMILY_CONTRIBUTIONS.md).
// The form speaks the page's language; the email to us stays in Serbo-Croatian and says which language was used.
export default function KnowSoldierForm({ soldier, unit }: { soldier: Soldier; unit?: Unit }) {
  const lang = useLang()
  const t = useT().know
  const [status, setStatus] = useState<Status>('closed')
  const [relation, setRelation] = useState('')
  const [story, setStory] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [fileError, setFileError] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [mayPublish, setMayPublish] = useState(false)
  const [mayShowName, setMayShowName] = useState(false)
  const [sendingFile, setSendingFile] = useState<[number, number] | null>(null)
  const [lost, setLost] = useState<Attachment[]>([])
  const fileInput = useRef<HTMLInputElement>(null)

  const canSend = (story.trim() || files.length > 0) && name.trim()

  const addFiles = (chosen: FileList | null) => {
    setFileError('')
    const list = Array.from(chosen ?? [])
    if (fileInput.current) fileInput.current.value = ''
    if (list.some((f) => !f.type.startsWith('image/') && f.type !== 'application/pdf')) {
      setFileError(t.notImage)
      return
    }
    const all = [...files, ...list]
    if (all.length > MAX_FILES) setFileError(t.tooMany(MAX_FILES))
    setFiles(all.slice(0, MAX_FILES))
  }

  const send = async () => {
    if (!canSend) return
    setStatus('sending')
    const link = new URL(recordPath(soldier.soldier_id, lang), window.location.origin).toString()
    const fields: Record<string, string> = {
      _subject: `Znam ovog borca: ${soldier.full_name} (${soldier.soldier_id})`,
      _template: 'table',
      Borac: soldier.full_name,
      ID: soldier.soldier_id,
      Jedinica: unit?.name ?? soldier.unit ?? '',
      Link: link,
      Jezik: LANG_NAMES[lang].name,
      'Veza sa borcem': relation,
      'Šta zna': story,
      'Ime pošiljaoca': name,
      'Email pošiljaoca': email,
      'Dozvola za objavu teksta i fotografija': mayPublish ? 'Da' : 'Ne',
      'Dozvola za objavu imena pošiljaoca': mayPublish && mayShowName ? 'Da, prvo slovo imena, prezime i srodstvo' : 'Ne',
    }
    if (email.trim()) fields._replyto = email.trim()

    try {
      const blobs: Blob[] = []
      for (const file of files) {
        // photographs are shrunk; a PDF goes as it is
        const blob = file.type === 'application/pdf' ? file : await shrinkPhoto(file)
        if (blob.size > MAX_FILE_BYTES) {
          setFileError(t.fileTooLarge(file.name))
          setStatus('open')
          return
        }
        blobs.push(blob)
      }
      if (files.length) fields['Prilozi'] = `${files.length}, stižu u posebnim porukama („Fotografija: …“)`

      const res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(fields),
      })
      if (!(await wasDelivered(res))) {
        setStatus('error')
        return
      }

      // one message a file, each waited for; those that still didn't arrive are named, with a button to send them again
      const items: Attachment[] = blobs.map((blob, i) => {
        const isPdf = files[i].type === 'application/pdf'
        const ext = isPdf ? 'pdf' : blob.type === 'image/jpeg' ? 'jpg' : files[i].name.split('.').pop() || 'jpg'
        return {
          name: files[i].name,
          subject: `Fotografija: ${soldier.full_name} (${soldier.soldier_id}) ${i + 1}/${blobs.length}`,
          field: 'Fotografija',
          fields: { Borac: soldier.full_name, ID: soldier.soldier_id, 'Ime pošiljaoca': name },
          replyTo: email.trim() || undefined,
          blob,
          filename: `${soldier.soldier_id}-${i + 1}.${ext}`,
        }
      })
      setLost(await sendAttachments(items, (n, of) => setSendingFile([n, of])))
      setSendingFile(null)
      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'closed') {
    return (
      <div className="know-soldier">
        <p>{t.prompt}</p>
        <button type="button" className="btn btn-secondary" onClick={() => setStatus('open')}>
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
    <form
      className="know-soldier know-soldier-form"
      onSubmit={(e) => { e.preventDefault(); send() }}
    >
      <h3>{t.title}</h3>

      <label htmlFor="know-relation">{t.relation}</label>
      <input
        id="know-relation"
        value={relation}
        onChange={(e) => setRelation(e.target.value)}
        placeholder={t.relationHint}
        maxLength={120}
      />

      <label htmlFor="know-story">{t.story}</label>
      <textarea
        id="know-story"
        value={story}
        onChange={(e) => setStory(e.target.value)}
        rows={4}
        maxLength={4000}
        placeholder={t.storyHint}
      />

      <span className="know-label">{t.files} <span className="know-optional">{t.optional}</span></span>
      <p className="know-hint">{t.filesHint(MAX_FILES)}</p>
      <div className="know-file">
        <input
          ref={fileInput}
          id="know-files"
          type="file"
          accept="image/*,application/pdf"
          multiple
          className="visually-hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
        <label htmlFor="know-files" className="btn btn-secondary">
          {files.length ? t.addMore : t.chooseFiles}
        </label>
      </div>
      {files.length > 0 && (
        <ul className="know-files">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`}>
              <span className="know-file-name">{f.name}</span>
              <button type="button" className="report-error-link" onClick={() => setFiles(files.filter((_, k) => k !== i))}>{t.remove}</button>
            </li>
          ))}
        </ul>
      )}
      {fileError && <p className="know-error">{fileError}</p>}

      <div className="know-pair">
        <div>
          <label htmlFor="know-name">{t.name}</label>
          <input id="know-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} autoComplete="name" />
        </div>
        <div>
          <label htmlFor="know-email">{t.email} <span className="know-optional">{t.optional}</span></label>
          <input
            id="know-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={160}
            autoComplete="email"
          />
        </div>
      </div>
      <p className="know-hint">{t.emailHint}</p>

      {/* two permissions, asked apart: what was sent, and the sender's name beside it (the user, 2026-11-19) */}
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

      {status === 'error' && (
        <p className="know-error">{t.error}</p>
      )}

      <div className="report-actions">
        <button type="submit" className="btn btn-primary" disabled={!canSend || status === 'sending'}>
          {status === 'sending' ? (sendingFile ? t.sendingFile(...sendingFile) : t.sending) : t.send}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setStatus('closed')}>
          {t.cancel}
        </button>
      </div>
    </form>
  )
}
