export type ShareResult = 'shared' | 'copied' | 'failed' | 'cancelled'

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

/** Phones get their own share sheet (Viber, WhatsApp, mail); elsewhere the link is copied */
export async function shareLink(url: string, title: string): Promise<ShareResult> {
  if (navigator.share && window.matchMedia('(pointer: coarse)').matches) {
    try {
      await navigator.share({ title, url })
      return 'shared'
    } catch (e) {
      if ((e as Error).name === 'AbortError') return 'cancelled'
    }
  }
  return (await copyText(url)) ? 'copied' : 'failed'
}
