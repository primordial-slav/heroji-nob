// The photos and documents a form sends, one message a file (FormSubmit's AJAX endpoint drops attachments). Each goes
// through the site's own /api/prilog, which passes it on to FormSubmit and reads its answer, so the form knows it
// arrived, tries again when it didn't, and names the files that still didn't (2026-11-20: sent straight to FormSubmit,
// whose answer a page can't read, a family's photo was lost four times and the form said "sent").
// On Vercel the route can't reach FormSubmit (Cloudflare refuses its servers, 2026-11-21), so a file the route
// doesn't get through goes straight from the browser, where only a broken connection shows as a failure.
// Vercel takes at most 4.5 MB in a request: photos are shrunk below ROUTE_MAX_BYTES (lib/images.ts); only a larger PDF
// still goes straight to FormSubmit, where only a broken connection shows as a failure.

export const ROUTE_MAX_BYTES = 4_300_000
const DIRECT = `https://formsubmit.co/${process.env.NEXT_PUBLIC_REPORT_EMAIL}`
const TRIES = 3

export interface Attachment {
  name: string                    // the visitor's own name for the file, to name it if it doesn't arrive
  subject: string                 // 'Fotografija: …' or 'Prilog: …'
  field: 'Fotografija' | 'Prilog' // the message's field that carries the file
  fields: Record<string, string>  // the rest of the message: Borac, ID, the sender's name
  replyTo?: string
  blob: Blob
  filename: string
}

const pause = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

async function sendOne(a: Attachment): Promise<boolean> {
  if (a.blob.size > ROUTE_MAX_BYTES) return sendDirect(a)
  for (let i = 0; i < TRIES; i++) {
    if (i) await pause(1500 * i)
    const body = new FormData()
    body.append('_subject', a.subject)
    body.append('field', a.field)
    for (const [key, value] of Object.entries(a.fields)) body.append(key, value)
    if (a.replyTo) body.append('_replyto', a.replyTo)
    body.append('file', a.blob, a.filename)
    try {
      const res = await fetch('/api/prilog', { method: 'POST', body })
      if (res.ok && (await res.json())?.ok === true) return true
      // refused for what it is (too large, not a photo or a PDF): another try won't help
      if (res.status >= 400 && res.status < 500) return false
      // FormSubmit turned the server away (502): Cloudflare in front of it refuses Vercel's servers, though it takes
      // the same message from a visitor's browser (2026-11-21: every photo sent through the route since the deploy
      // at 03:12 was lost, E. Goldrick's and V. Mihić's). Send it from the browser, as before the route
      if (res.status === 502) return sendDirect(a)
    } catch {
      // the connection broke: try again
    }
  }
  return sendDirect(a)
}

async function sendDirect(a: Attachment): Promise<boolean> {
  const body = new FormData()
  body.append('_subject', a.subject)
  body.append('_template', 'table')
  body.append('_captcha', 'false')
  for (const [key, value] of Object.entries(a.fields)) body.append(key, value)
  if (a.replyTo) body.append('_replyto', a.replyTo)
  body.append(a.field, a.blob, a.filename)
  try {
    await fetch(DIRECT, { method: 'POST', mode: 'no-cors', body })
    return true
  } catch {
    return false
  }
}

/** Sends the files one after another, telling `onFile` which is on its way; answers with those that didn't arrive */
export async function sendAttachments(items: Attachment[], onFile: (n: number, of: number) => void): Promise<Attachment[]> {
  const lost: Attachment[] = []
  for (let i = 0; i < items.length; i++) {
    onFile(i + 1, items.length)
    if (!(await sendOne(items[i]))) lost.push(items[i])
  }
  return lost
}
