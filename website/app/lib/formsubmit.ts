// Where the forms send: FormSubmit's key for the site's address, the random string it gave when knjigaboraca.org was
// activated (2026-11-21), in place of the plain address. FormSubmit limits each key on its own: from 2026-11-23 17:49
// UTC it refused every message sent to the plain address ("Rate limit exceeded", HTTP 429, still so on 11-24 at 08:44,
// after about 190 messages in 30 hours, one a photo), while the same inbox took them through this key at once. The
// key also keeps the address out of the page's code. The plain address stays for mail (mailtoHref, the footer).
export const FORMSUBMIT_KEY = process.env.NEXT_PUBLIC_FORMSUBMIT_KEY || 'e6a56b1ed6120f60d362de85980a7682'
export const FORMSUBMIT_AJAX = `https://formsubmit.co/ajax/${FORMSUBMIT_KEY}`
export const FORMSUBMIT_POST = `https://formsubmit.co/${FORMSUBMIT_KEY}`

// FormSubmit answers 200 even when it did not deliver the message (e.g. "This form needs Activation"),
// with {"success": "false", "message": ...} in the body; only "success": "true" means it was sent.
export async function wasDelivered(res: Response): Promise<boolean> {
  if (!res.ok) return false
  try {
    const data = await res.json()
    return data?.success === true || data?.success === 'true'
  } catch {
    return false
  }
}

// An address a visitor typed, good enough for FormSubmit's reply-to: one it can't read makes it turn the whole message
// away, so a doubtful one goes as text only (2026-11-23: forms that wouldn't send)
export const looksLikeEmail = (s: string) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s.trim())

/** When FormSubmit can't be reached: the same message as an email to the site's address, ready in the visitor's mail
 *  program (mailto: bodies are cut by some programs past about 1,800 characters, so a long text is shortened) */
export function mailtoHref(subject: string, fields: [string, string][]): string {
  const body = fields.filter(([, v]) => v.trim()).map(([k, v]) => `${k}: ${v.length > 1500 ? `${v.slice(0, 1500)}…` : v}`).join('\n\n')
  return `mailto:${process.env.NEXT_PUBLIC_REPORT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
}
