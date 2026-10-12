import type { ReactNode } from 'react'
import { Golos_Text, PT_Serif } from 'next/font/google'
import '../globals.css'
import SiteFrame from './SiteFrame'
import { HTML_LANG, type Lang } from '../i18n/config'

// Self-hosted at build time; both faces cover Serbo-Croatian, Slovene and Macedonian, Latin and Cyrillic
const golos = Golos_Text({
  subsets: ['latin', 'latin-ext', 'cyrillic'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-golos',
  display: 'swap',
})
const ptSerif = PT_Serif({
  subsets: ['latin', 'latin-ext', 'cyrillic'],
  weight: ['400', '700'],
  variable: '--font-pt-serif',
  display: 'swap',
})

// Inline script to prevent FOUC by setting data-theme before React hydrates
const themeScript = `
  (function() {
    try {
      var theme = localStorage.getItem('theme') || 'system';
      var resolved = theme;
      if (theme === 'system') {
        resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      document.documentElement.setAttribute('data-theme', resolved);
    } catch(e) {}
  })();
`

// The document: fonts, styles and the theme before the first paint. The 404 page (global-not-found.tsx) puts its
// own frame in it, since it learns its language only in the browser.
export function SiteDocument({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
    <html lang={HTML_LANG[lang]} className={`${golos.variable} ${ptSerif.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>{children}</body>
    </html>
  )
}

// The page around every route, in its language: the two root layouts ((sr) and (intl)/[lang]) render it
export default function SiteShell({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
    <SiteDocument lang={lang}>
      <SiteFrame lang={lang}>{children}</SiteFrame>
    </SiteDocument>
  )
}
