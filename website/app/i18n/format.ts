import type { Lang } from './config'

// Number agreement as each language has it (the CLDR rules for whole numbers):
// sr  1 borac, 2 borca, 5 boraca, 21 borac
// sl  1 borec, 2 borca, 3 borci, 5 borcev, 101 borec (by the last two digits)
// mk  1 борец, 2 борци, 21 борец
// en  1 Partisan, 2 Partisans
export type PluralForm = 'one' | 'two' | 'few' | 'other'

export function pluralForm(lang: Lang, n: number): PluralForm {
  const mod10 = n % 10
  const mod100 = n % 100
  switch (lang) {
    case 'sr':
      if (mod10 === 1 && mod100 !== 11) return 'one'
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'few'
      return 'other'
    case 'sl':
      if (mod100 === 1) return 'one'
      if (mod100 === 2) return 'two'
      if (mod100 === 3 || mod100 === 4) return 'few'
      return 'other'
    case 'mk':
      return mod10 === 1 && mod100 !== 11 ? 'one' : 'other'
    case 'en':
      return n === 1 ? 'one' : 'other'
  }
}

/** Picks the form for n: forms.two and forms.few fall back to other */
export function plural(lang: Lang, n: number, forms: { one: string; two?: string; few?: string; other: string }): string {
  const form = pluralForm(lang, n)
  return forms[form] ?? forms.other
}

/** 108150 -> "108.150", in English "108,150" (written out, so server and browser always agree) */
export function formatNumber(lang: Lang, n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, lang === 'en' ? ',' : '.')
}

/** Straight double quotes in a name ('"Marko Orešković"') in the language's own quotation marks */
export function quoteMarks(lang: Lang, text: string): string {
  const [open, close] = QUOTES[lang]
  return text.replace(/"([^"]*)"/g, `${open}$1${close}`)
}

export const QUOTES: Record<Lang, [string, string]> = {
  sr: ['„', '“'],
  sl: ['»', '«'],
  mk: ['„', '“'],
  en: ['‘', '’'],
}

/** A quoted word in running text: „Petrović“, »Petrović«, ‘Petrović’ */
export function quoted(lang: Lang, text: string): string {
  const [open, close] = QUOTES[lang]
  return `${open}${text}${close}`
}
