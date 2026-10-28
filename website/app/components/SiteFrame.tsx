import type { ComponentType, ReactNode } from 'react'
import HomeLink from './HomeLink'
import Navigation from './Navigation'
import ThemeToggle from './ThemeToggle'
import LanguageMenu from './LanguageMenu'
import SiteFooter from './SiteFooter'
import { ThemeProvider } from '../lib/ThemeContext'
import type { Lang } from '../i18n/config'
import { messagesFor } from '../i18n'

export type LanguageProvider = ComponentType<{ lang: Lang; children: ReactNode }>

// The header, the page under it and the footer, in the page's language. Language is the provider of the page's text
// its root layout gives (i18n/LangContext.tsx), so that a page loads only the languages it may be in.
export default function SiteFrame({ lang, Language, children }: { lang: Lang; Language: LanguageProvider; children: ReactNode }) {
  return (
    <Language lang={lang}>
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
    </Language>
  )
}
