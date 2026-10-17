import type { Lang } from '@/app/i18n/config'

// Units that have an overview page, /jedinica/<id> (app/(sr)/jedinica/, Serbo-Croatian only so far): their cards
// open it, and it leads on to the soldiers list (/units/<id>). Every other unit, and every other language, opens the
// soldiers list as before.
export const UNIT_PAGES = new Set(['prva-licka-brigada'])

export function unitHref(id: string, lang: Lang): string {
  return lang === 'sr' && UNIT_PAGES.has(id) ? `/jedinica/${id}` : `/units/${id}`
}
