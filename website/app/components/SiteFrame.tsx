import type { ReactNode } from 'react'
import HomeLink from './HomeLink'
import Navigation from './Navigation'
import ThemeToggle from './ThemeToggle'
import LanguageMenu from './LanguageMenu'
import SiteFooter from './SiteFooter'
import { ThemeProvider } from '../lib/ThemeContext'
import { LangProvider } from '../i18n/LangContext'
import type { Lang } from '../i18n/config'
import { messagesFor } from '../i18n'

// The header, the page under it and the footer, in the page's language
export default function SiteFrame({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
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
        <SiteFooter lang={lang} />
      </ThemeProvider>
    </LangProvider>
  )
}
