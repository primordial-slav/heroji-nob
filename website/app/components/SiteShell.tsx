import type { ReactNode } from 'react'
import { Golos_Text, PT_Serif } from 'next/font/google'
import '../globals.css'
import HomeLink from './HomeLink'
import Navigation from './Navigation'
import ThemeToggle from './ThemeToggle'
import LanguageMenu from './LanguageMenu'
import { ThemeProvider } from '../lib/ThemeContext'
import { LangProvider } from '../i18n/LangContext'
import { HTML_LANG, type Lang } from '../i18n/config'
import { messagesFor } from '../i18n'

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

// The page around every route, in its language: the two root layouts ((sr) and (intl)/[lang]) render it
export default function SiteShell({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
    <html lang={HTML_LANG[lang]} className={`${golos.variable} ${ptSerif.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <LangProvider lang={lang}>
          <ThemeProvider>
            <header className="masthead">
              <div className="container masthead-bar">
                <HomeLink className="site-name">{messagesFor(lang).site.name}</HomeLink>
                <Navigation />
                <LanguageMenu />
                <ThemeToggle />
              </div>
            </header>
            <main>
              {children}
            </main>
          </ThemeProvider>
        </LangProvider>
      </body>
    </html>
  )
}
