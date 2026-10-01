// The site's languages. Serbo-Croatian is the site's own language and keeps the plain addresses
// (/, /units/<id>, /izvori); the others live under their code: /sl, /mk/units/<id>, /en/izvori.

export const LANGS = ['sr', 'sl', 'mk', 'en'] as const
export type Lang = (typeof LANGS)[number]

export const DEFAULT_LANG: Lang = 'sr'
export const PREFIXED_LANGS = LANGS.filter((l) => l !== DEFAULT_LANG)

/**
 * The languages offered in the language bar above the header, in this order. A language goes here once its text
 * is finished and read through (VOICE.md, "Other languages"). Until then its pages still build at their address,
 * for checking, but nothing links to them and search engines are asked to leave them out.
 */
export const FINISHED_LANGS: readonly Lang[] = ['sr', 'sl', 'mk', 'en']

export function isFinished(lang: Lang): boolean {
  return FINISHED_LANGS.includes(lang)
}

export function isLang(value: string | undefined | null): value is Lang {
  return LANGS.includes(value as Lang)
}

/** The html lang attribute */
export const HTML_LANG: Record<Lang, string> = { sr: 'sr-Latn', sl: 'sl', mk: 'mk', en: 'en' }

/** For Open Graph */
export const OG_LOCALE: Record<Lang, string> = { sr: 'sr_RS', sl: 'sl_SI', mk: 'mk_MK', en: 'en_GB' }

/** Each language by its own name, for the language bar; the code where there is no room for the name */
export const LANG_NAMES: Record<Lang, { code: string; name: string }> = {
  sr: { code: 'SH', name: 'Srpskohrvatski' },
  sl: { code: 'SL', name: 'Slovenščina' },
  mk: { code: 'MK', name: 'Македонски' },
  en: { code: 'EN', name: 'English' },
}

/** '/units/x' in a language: '/units/x' (sr), '/en/units/x' */
export function localePath(lang: Lang, path: string): string {
  if (lang === DEFAULT_LANG) return path
  return path === '/' ? `/${lang}` : `/${lang}${path}`
}

/** '/en/units/x' -> { lang: 'en', path: '/units/x' }; '/units/x' -> { lang: 'sr', path: '/units/x' } */
export function splitPath(pathname: string): { lang: Lang; path: string } {
  const first = pathname.split('/')[1]
  if (first !== DEFAULT_LANG && isLang(first)) {
    return { lang: first, path: pathname.slice(first.length + 1) || '/' }
  }
  return { lang: DEFAULT_LANG, path: pathname || '/' }
}
