// One photo or document from the site's forms (KnowSoldierForm, MissingSoldierForm), passed on to FormSubmit's regular
// endpoint, which mails it to us with the file attached. The forms used to send it there themselves, but a page can't
// read FormSubmit's answer across origins, so a file that didn't arrive looked sent: a family's photo was lost four
// times on 2026-11-20 (Palčič Dino). Here the answer is read and the form told, so it can try again or say so.
//
// FormSubmit answers a message it sent with its thank-you page ("The form was submitted successfully", tested
// 2026-11-20) or a redirect to _next; anything else (an activation or spam page, an error) is a failure.
// Vercel takes at most 4.5 MB in a request: the forms shrink photos below MAX_BYTES (lib/images.ts) and send a larger
// PDF straight to FormSubmit (lib/attachments.ts).
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const maxDuration = 30

const TO = process.env.NEXT_PUBLIC_REPORT_EMAIL
const MAX_BYTES = 4_400_000
// what the message may carry besides the file: the names the forms give their fields
const FIELDS = ['Borac', 'ID', 'Ime pošiljaoca', 'Pošiljalac']
const FILE_FIELDS = ['Fotografija', 'Prilog']

const answer = (ok: boolean, status: number) => Response.json({ ok }, { status })

export async function POST(request: Request) {
  if (!TO) return answer(false, 503)
  // only the site's own pages may send through it
  const origin = request.headers.get('origin')
  const host = request.headers.get('host')
  if (!origin || !host || new URL(origin).host !== host) return answer(false, 403)

  let form: FormData
  try {
    form = await request.formData()
  } catch {
    return answer(false, 400)
  }
  // a Blob, not a File: Node 18 (the local server) has no global File, though the form gives the file its name
  const file = form.get('file')
  if (!(file instanceof Blob) || file.size === 0) return answer(false, 400)
  if (file.size > MAX_BYTES) return answer(false, 413)
  if (!file.type.startsWith('image/') && file.type !== 'application/pdf') return answer(false, 415)
  const subject = String(form.get('_subject') ?? '')
  if (!/^(Fotografija|Prilog): /.test(subject) || subject.length > 300) return answer(false, 400)
  const field = String(form.get('field') ?? '')
  if (!FILE_FIELDS.includes(field)) return answer(false, 400)

  const out = new FormData()
  out.append('_subject', subject)
  out.append('_template', 'table')
  out.append('_captcha', 'false')
  for (const key of FIELDS) {
    const value = form.get(key)
    if (typeof value === 'string' && value.trim()) out.append(key, value.trim().slice(0, 300))
  }
  const replyTo = form.get('_replyto')
  if (typeof replyTo === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(replyTo.trim())) out.append('_replyto', replyTo.trim().slice(0, 200))
  const filename = String((file as Blob & { name?: string }).name ?? '').replace(/[^\w.-]/g, '_').slice(0, 80) || 'prilog'
  out.append(field, file, filename)

  try {
    const res = await fetch(`https://formsubmit.co/${TO}`, {
      method: 'POST',
      body: out,
      // as the form's own page would send it: FormSubmit ties the address's activation to the site
      headers: { Origin: origin, Referer: `${origin}/` },
      redirect: 'manual',
    })
    const ok = res.status >= 300 && res.status < 400 ? true : res.ok && /submitted successfully/i.test(await res.text())
    return answer(ok, ok ? 200 : 502)
  } catch {
    return answer(false, 502)
  }
}
