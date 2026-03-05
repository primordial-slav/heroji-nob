import type { Metadata } from 'next'
import './globals.css'
import Navigation from './components/Navigation'
import { ThemeProvider } from './lib/ThemeContext'

export const metadata: Metadata = {
  title: 'Knjiga Boraca - Partizanska Baza Podataka',
  description: 'Baza podataka boraca partizanskog pokreta',
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
    <html lang="sr" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&family=Oswald:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <ThemeProvider>
          <header className="header">
            <div className="header-overlay"></div>
            <div className="container header-content">
              <h1>Knjiga Boraca</h1>
              <p>Baza podataka boraca partizanskog pokreta</p>
            </div>
          </header>
          <Navigation />
          <main className="container">
            {children}
          </main>
          <footer className="footer">
            <div className="container">
              <p>U spomen na sve heroje koji su se borili za slobodu</p>
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  )
}
