import type { Metadata } from 'next'
import './globals.css'
import Navigation from './components/Navigation'

export const metadata: Metadata = {
  title: 'Naši Heroji - 1st Lika Proletarian Brigade',
  description: 'Memorial website honoring the soldiers of the 1st Lika Proletarian Brigade',
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
          <div className="container">
            <h1>Naši Heroji</h1>
            <p>Partizanska memorijalna baza podataka</p>
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
