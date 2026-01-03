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
            <p>1st Lika Proletarian Brigade "Marko Orešković"</p>
          </div>
        </header>
        <Navigation />
        <main className="container">
          {children}
        </main>
        <footer className="footer">
          <div className="container">
            <p>In memory of 9,368 heroes who fought for freedom</p>
          </div>
        </footer>
      </body>
    </html>
  )
}
