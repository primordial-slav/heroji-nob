import type { Metadata } from 'next'
import { FINISHED_LANGS, HTML_LANG, OG_LOCALE, isFinished, localePath, type Lang } from './config'
import { messagesFor } from './index'

/**
 * A page's title, description and its addresses in the other finished languages; a language that is not
 * finished yet (config.ts) is left out of search engines.
 * `path` is the page's address without the language: '/', '/izvori', '/units/prva-licka-brigada'.
 */
export function pageMetadata(lang: Lang, path: string, page: { title?: string; description?: string } = {}): Metadata {
  const t = messagesFor(lang)
  const description = page.description ?? t.site.description
  const title = page.title ? `${page.title} · ${t.site.name}` : t.site.name
  return {
    title,
    description,
    alternates: {
      canonical: localePath(lang, path),
      languages: {
        ...Object.fromEntries(FINISHED_LANGS.map((l) => [HTML_LANG[l], localePath(l, path)])),
        'x-default': path,
      },
    },
    openGraph: { title, description, locale: OG_LOCALE[lang], siteName: t.site.name },
    ...(isFinished(lang) ? {} : { robots: { index: false } }),
  }
}

/** The printable memorial card (/kartica): not for search engines */
export function cardMetadata(lang: Lang): Metadata {
  const t = messagesFor(lang).card
  return { ...pageMetadata(lang, '/kartica', { title: t.title, description: t.description }), robots: { index: false } }
}
