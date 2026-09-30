'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Unit } from '@/app/data/units'
import { useFuseSearch } from '@/app/lib/useFuseSearch'
import type { Soldier } from '@/app/lib/types'
import SoldierModal from '@/app/components/SoldierModal'
import SoldierResults from '@/app/components/SoldierResults'
import { ArrowLeftIcon, SearchIcon } from '@/app/components/Icons'
import { sqQuotes } from '@/app/lib/typography'

interface UnitPageClientProps {
  unit: Unit
}

export default function UnitPageClient({ unit }: UnitPageClientProps) {
  const [soldiers, setSoldiers] = useState<Soldier[]>([])
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)

  const { results, searchTerm, setSearchTerm } = useFuseSearch(
    soldiers,
    { showAllOnEmpty: true }
  )

  useEffect(() => {
    fetch(unit.dataFile)
      .then(res => res.json())
      .then(data => setSoldiers(data))
      .catch(() => setLoadFailed(true))
      .finally(() => setLoading(false))
  }, [unit])

  return (
    <div>
      <section className="container unit-hero">
        <Link href="/" className="back-link"><ArrowLeftIcon size={16} /> Sve jedinice</Link>
        <div className="unit-hero-body">
          <img src={unit.image} alt={unit.name} className="unit-hero-photo" />
          <div>
            <h1>{sqQuotes(unit.name)}</h1>
            <p className="unit-hero-desc">{unit.description}</p>
          </div>
        </div>
      </section>

      <div className="container">
        <div className="unit-search">
          <label htmlFor="unit-search">Pretraga u ovoj jedinici</label>
          <div className="finder-field">
            <span className="search-icon"><SearchIcon size={20} /></span>
            <input
              id="unit-search"
              type="search"
              className="search-input"
              placeholder="Prezime, ime ili mesto"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
        </div>

        <div id="results">
          {loading ? (
            <ul className="loading-rows" aria-label="Učitavanje spiska">
              {Array.from({ length: 8 }, (_, i) => <li key={i} />)}
            </ul>
          ) : loadFailed ? (
            <div className="empty">
              <h2>Spisak se nije učitao</h2>
              <p>Proverite internet vezu i osvežite stranu.</p>
            </div>
          ) : results.length === 0 ? (
            <div className="empty">
              <h2>Nema boraca za „{searchTerm}“ u ovoj jedinici</h2>
              <p>
                Pokušajte samo prezime, ili potražite na <Link href="/">početnoj strani</Link> u
                svim jedinicama.
              </p>
            </div>
          ) : (
            <SoldierResults
              results={results}
              onSelect={setSelectedSoldier}
              scrollTargetId="results"
            />
          )}
        </div>
      </div>

      {selectedSoldier && (
        <SoldierModal
          soldier={selectedSoldier}
          unitName={unit.name}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
