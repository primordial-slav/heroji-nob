import type { Metadata } from 'next'
import { Golos_Text, PT_Serif } from 'next/font/google'
import './globals.css'
import HomeLink from './components/HomeLink'
import Navigation from './components/Navigation'
import ThemeToggle from './components/ThemeToggle'
import { ThemeProvider } from './lib/ThemeContext'

// Self-hosted at build time; both faces cover Serbo-Croatian Latin and Cyrillic
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

export const metadata: Metadata = {
  title: 'Knjiga boraca',
  description: 'Spiskovi boraca partizanskih jedinica, pretraživi po imenu, sa stranom iz knjige uz svaki zapis.',
}

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="sr-Latn" className={`${golos.variable} ${ptSerif.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <ThemeProvider>
          <header className="masthead">
            <div className="container masthead-bar">
              <HomeLink className="site-name">Knjiga boraca</HomeLink>
              <Navigation />
              <ThemeToggle />
            </div>
          </header>
          <main>
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  )
}
