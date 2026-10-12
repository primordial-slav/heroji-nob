import type { Metadata } from 'next'
import { FINISHED_LANGS, HTML_LANG, OG_LOCALE, isFinished, localePath, type Lang } from './config'
import { messagesFor } from './index'

// The site's own address, so a shared link's preview and the language links are absolute: Vercel's production
// domain when built there, else the local server
const SITE_URL = new URL(process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}` : 'http://localhost:3000')
// The home band's photograph in the red (scripts/make_site_icons.py), shown when a link is shared
const SHARE_IMAGE = { url: '/og.jpg', width: 1200, height: 630 }

/** What every page of a language has: the address links resolve against, the icons, the share image */
export function siteMetadata(lang: Lang): Metadata {
  const t = messagesFor(lang)
  return {
    metadataBase: SITE_URL,
    title: t.site.name,
    description: t.site.description,
    icons: {
      icon: [{ url: '/favicon.ico', sizes: '48x48' }, { url: '/icon.svg', type: 'image/svg+xml' }],
      apple: '/apple-icon.png',
    },
    openGraph: { siteName: t.site.name, locale: OG_LOCALE[lang], images: [SHARE_IMAGE] },
    twitter: { card: 'summary_large_image' },
  }
}

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
    openGraph: { title, description, url: localePath(lang, path), locale: OG_LOCALE[lang], siteName: t.site.name, images: [SHARE_IMAGE] },
    ...(isFinished(lang) ? {} : { robots: { index: false } }),
  }
}

/** The printable memorial card (/kartica): not for search engines */
export function cardMetadata(lang: Lang): Metadata {
  const t = messagesFor(lang).card
  return { ...pageMetadata(lang, '/kartica', { title: t.title, description: t.description }), robots: { index: false } }
}
