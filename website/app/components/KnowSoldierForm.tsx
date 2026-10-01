'use client'

import { useRef, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { recordPath } from '@/app/lib/records'
import { shrinkPhoto } from '@/app/lib/images'
import { wasDelivered } from '@/app/lib/formsubmit'
import { useLang, useT } from '@/app/i18n/LangContext'
import { LANG_NAMES } from '@/app/i18n/config'

const ENDPOINT = `https://formsubmit.co/ajax/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`
// FormSubmit's AJAX endpoint drops attachments; its regular endpoint keeps them but answers with a page we
// can't read cross-origin. So the text goes through AJAX (and we know it arrived), the photo separately here.
const PHOTO_ENDPOINT = `https://formsubmit.co/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`
// The form service takes at most 10 MB per message
const MAX_PHOTO_BYTES = 9_500_000

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
  const [photo, setPhoto] = useState<File | null>(null)
  const [photoError, setPhotoError] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [mayPublish, setMayPublish] = useState(false)
  const [photoLost, setPhotoLost] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const canSend = (story.trim() || photo) && name.trim() && !photoError

  const choosePhoto = (file: File | null) => {
    setPhotoError('')
    setPhoto(null)
    if (!file) {
      if (fileInput.current) fileInput.current.value = ''
      return
    }
    if (!file.type.startsWith('image/')) {
      setPhotoError(t.notImage)
      return
    }
    setPhoto(file)
  }

  const send = async () => {
    if (!canSend) return
    setStatus('sending')
    const link = unit ? new URL(recordPath(unit, soldier.soldier_id, lang), window.location.origin).toString() : ''
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
      'Dozvola za objavu': mayPublish ? 'Da, uz ime pošiljaoca' : 'Ne',
    }
    if (email.trim()) fields._replyto = email.trim()

    try {
      const blob = photo ? await shrinkPhoto(photo) : null
      if (photo && blob && blob.size > MAX_PHOTO_BYTES) {
        setPhotoError(t.tooLarge)
        setStatus('open')
        return
      }
      if (photo) fields['Fotografija'] = 'stiže u posebnoj poruci („Fotografija: …“)'

      const res = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(fields),
      })
      if (!(await wasDelivered(res))) {
        setStatus('error')
        return
      }

      if (photo && blob) {
        const body = new FormData()
        body.append('_subject', `Fotografija: ${soldier.full_name} (${soldier.soldier_id})`)
        body.append('_template', 'table')
        body.append('_captcha', 'false')
        body.append('Borac', soldier.full_name)
        body.append('ID', soldier.soldier_id)
        body.append('Ime pošiljaoca', name)
        if (email.trim()) body.append('_replyto', email.trim())
        const ext = blob.type === 'image/jpeg' ? 'jpg' : photo.name.split('.').pop() || 'jpg'
        body.append('Fotografija', blob, `${soldier.soldier_id}.${ext}`)
        // The answer is opaque (no CORS on this endpoint); only a network error shows as a failure
        try {
          await fetch(PHOTO_ENDPOINT, { method: 'POST', mode: 'no-cors', body })
        } catch {
          setPhotoLost(true)
        }
      }
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

  if (status === 'sent') {
    return (
      <div className="know-soldier" role="status">
        <p className="know-soldier-done">
          {t.thanks}
          {email.trim() && ` ${t.willReply}`}
          {photoLost && ` ${t.photoLost}`}
        </p>
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

      <span className="know-label">{t.photo} <span className="know-optional">{t.optional}</span></span>
      <div className="know-file">
        <input
          ref={fileInput}
          id="know-photo"
          type="file"
          accept="image/*"
          className="visually-hidden"
          onChange={(e) => choosePhoto(e.target.files?.[0] ?? null)}
        />
        <label htmlFor="know-photo" className="btn btn-secondary">
          {photo ? t.chooseOther : t.choosePhoto}
        </label>
        {photo && (
          <>
            <span className="know-file-name">{photo.name}</span>
            <button type="button" className="report-error-link" onClick={() => choosePhoto(null)}>{t.remove}</button>
          </>
        )}
      </div>
      {photoError && <p className="know-error">{photoError}</p>}

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

      <label className="know-check">
        <input type="checkbox" checked={mayPublish} onChange={(e) => setMayPublish(e.target.checked)} />
        {t.consent}
      </label>

      {status === 'error' && (
        <p className="know-error">{t.error}</p>
      )}

      <div className="report-actions">
        <button type="submit" className="btn btn-primary" disabled={!canSend || status === 'sending'}>
          {status === 'sending' ? t.sending : t.send}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setStatus('closed')}>
          {t.cancel}
        </button>
      </div>
    </form>
  )
}
