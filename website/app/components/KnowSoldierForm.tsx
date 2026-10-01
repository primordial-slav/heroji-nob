'use client'

import { useRef, useState } from 'react'
import type { Soldier } from '@/app/lib/types'
import type { Unit } from '@/app/data/units'
import { recordPath } from '@/app/lib/records'
import { shrinkPhoto } from '@/app/lib/images'
import { wasDelivered } from '@/app/lib/formsubmit'

const ENDPOINT = `https://formsubmit.co/ajax/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`
// The form service takes at most 10 MB per message
const MAX_PHOTO_BYTES = 9_500_000

type Status = 'closed' | 'open' | 'sending' | 'sent' | 'error'

// "I know this soldier": a family member or researcher sends what they know, optionally with a photograph.
// It arrives by email; approved items are added by hand to app/data/family.ts (docs/FAMILY_CONTRIBUTIONS.md).
export default function KnowSoldierForm({ soldier, unit }: { soldier: Soldier; unit?: Unit }) {
  const [status, setStatus] = useState<Status>('closed')
  const [relation, setRelation] = useState('')
  const [story, setStory] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [photoError, setPhotoError] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [mayPublish, setMayPublish] = useState(false)
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
      setPhotoError('Izaberite fotografiju (JPG ili PNG).')
      return
    }
    setPhoto(file)
  }

  const send = async () => {
    if (!canSend) return
    setStatus('sending')
    const link = unit ? new URL(recordPath(unit, soldier.soldier_id), window.location.origin).toString() : ''
    const fields: Record<string, string> = {
      _subject: `Znam ovog borca: ${soldier.full_name} (${soldier.soldier_id})`,
      _template: 'table',
      Borac: soldier.full_name,
      ID: soldier.soldier_id,
      Jedinica: unit?.name ?? soldier.unit ?? '',
      Link: link,
      'Veza sa borcem': relation,
      'Šta zna': story,
      'Ime pošiljaoca': name,
      'Email pošiljaoca': email,
      'Dozvola za objavu': mayPublish ? 'Da, uz ime pošiljaoca' : 'Ne',
    }
    if (email.trim()) fields._replyto = email.trim()

    try {
      let res: Response
      if (photo) {
        const blob = await shrinkPhoto(photo)
        if (blob.size > MAX_PHOTO_BYTES) {
          setPhotoError('Fotografija je prevelika. Pošaljite manju (do 9 MB).')
          setStatus('open')
          return
        }
        const body = new FormData()
        Object.entries(fields).forEach(([k, v]) => body.append(k, v))
        const ext = blob.type === 'image/jpeg' ? 'jpg' : photo.name.split('.').pop() || 'jpg'
        body.append('Fotografija', blob, `${soldier.soldier_id}.${ext}`)
        res = await fetch(ENDPOINT, { method: 'POST', headers: { Accept: 'application/json' }, body })
      } else {
        res = await fetch(ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(fields),
        })
      }
      setStatus((await wasDelivered(res)) ? 'sent' : 'error')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'closed') {
    return (
      <div className="know-soldier">
        <p>Imate fotografiju ili znate nešto o ovom borcu?</p>
        <button type="button" className="btn btn-secondary" onClick={() => setStatus('open')}>
          Znam ovog borca
        </button>
      </div>
    )
  }

  if (status === 'sent') {
    return (
      <div className="know-soldier" role="status">
        <p className="know-soldier-done">
          Hvala vam. Pogledaćemo ono što ste poslali.
          {email.trim() && ' Ako nešto ne bude jasno, javićemo vam se.'}
        </p>
      </div>
    )
  }

  return (
    <form
      className="know-soldier know-soldier-form"
      onSubmit={(e) => { e.preventDefault(); send() }}
    >
      <h3>Znam ovog borca</h3>

      <label htmlFor="know-relation">Ko ste vi ovom borcu?</label>
      <input
        id="know-relation"
        value={relation}
        onChange={(e) => setRelation(e.target.value)}
        placeholder="Na primer: unuka, sin, rođak, komšija"
        maxLength={120}
      />

      <label htmlFor="know-story">Šta znate o ovom borcu</label>
      <textarea
        id="know-story"
        value={story}
        onChange={(e) => setStory(e.target.value)}
        rows={4}
        maxLength={4000}
        placeholder="Šta porodica pamti, gde je grob, šta je bilo posle rata, ili šta u zapisu nije tačno."
      />

      <span className="know-label">Fotografija <span className="know-optional">(nije obavezno)</span></span>
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
          {photo ? 'Izaberite drugu' : 'Izaberite fotografiju'}
        </label>
        {photo && (
          <>
            <span className="know-file-name">{photo.name}</span>
            <button type="button" className="report-error-link" onClick={() => choosePhoto(null)}>Ukloni</button>
          </>
        )}
      </div>
      {photoError && <p className="know-error">{photoError}</p>}

      <div className="know-pair">
        <div>
          <label htmlFor="know-name">Vaše ime i prezime</label>
          <input id="know-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} autoComplete="name" />
        </div>
        <div>
          <label htmlFor="know-email">Email <span className="know-optional">(nije obavezno)</span></label>
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
      <p className="know-hint">Email nam služi samo da vam se javimo. Ne objavljujemo ga.</p>

      <label className="know-check">
        <input type="checkbox" checked={mayPublish} onChange={(e) => setMayPublish(e.target.checked)} />
        Dozvoljavam da se fotografija i tekst objave uz ovaj zapis, sa mojim imenom.
      </label>

      {status === 'error' && (
        <p className="know-error">Nije poslato. Proverite vezu sa internetom i pokušajte ponovo.</p>
      )}

      <div className="report-actions">
        <button type="submit" className="btn btn-primary" disabled={!canSend || status === 'sending'}>
          {status === 'sending' ? 'Šalje se…' : 'Pošalji'}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setStatus('closed')}>
          Otkaži
        </button>
      </div>
    </form>
  )
}
