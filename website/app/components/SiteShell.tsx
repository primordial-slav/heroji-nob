import type { ReactNode } from 'react'
import { Golos_Text, PT_Serif } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import '../globals.css'
import SiteFrame, { type LanguageProvider } from './SiteFrame'
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

// Vercel's Web Analytics (the project's Analytics tab: visitors, pages, where they came from), cookieless, its script
// and its counts on the site's own address (a path Vercel gives the project). Only in a build made on Vercel: elsewhere that
// address doesn't exist, and under next dev the package would load a script from another host, which the CSP refuses
const ON_VERCEL = process.env.VERCEL === '1'

// The document: fonts, styles and the theme before the first paint. The 404 page (global-not-found.tsx) puts its
// own frame in it, since it learns its language only in the browser.
export function SiteDocument({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
    <html lang={HTML_LANG[lang]} className={`${golos.variable} ${ptSerif.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        {children}
        {ON_VERCEL && <Analytics />}
      </body>
    </html>
  )
}

// The page around every route, in its language: the two root layouts ((sr) and (intl)/[lang]) render it
export default function SiteShell({ lang, Language, children }: { lang: Lang; Language: LanguageProvider; children: ReactNode }) {
  return (
    <SiteDocument lang={lang}>
      <SiteFrame lang={lang} Language={Language}>{children}</SiteFrame>
    </SiteDocument>
  )
}
