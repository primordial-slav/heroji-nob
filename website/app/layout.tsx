import type { Metadata } from 'next'
import './globals.css'
import Navigation from './components/Navigation'

export const metadata: Metadata = {
  title: 'Knjiga Boraca - Partizanska Baza Podataka',
  description: 'Baza podataka boraca partizanskog pokreta',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="sr">
      <body>
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
      </body>
    </html>
  )
}
