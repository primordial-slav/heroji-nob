import type { Metadata } from 'next'
import MemorialCard from './MemorialCard'

export const metadata: Metadata = {
  title: 'Spomen-kartica · Knjiga boraca',
  description: 'Zapis borca iz knjige boraca, za štampu.',
  robots: { index: false },
}

export default function KarticaPage() {
  return <MemorialCard />
}
