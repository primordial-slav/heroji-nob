import type { ReactNode } from 'react'
import styles from './mapa.module.css'

// A count of the killed on the map: it opens the list of exactly those soldiers in a new tab (mapa/spisak)
export function KilledLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener" className={styles.killedLink} title="Spisak se otvara u novoj kartici">
      {children}
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
        strokeLinejoin="round" aria-hidden="true">
        <path d="M14 4h6v6" /><path d="M20 4l-9 9" />
        <path d="M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10" />
      </svg>
    </a>
  )
}
