'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { units } from './data/units'
import { useFuseSearch } from './lib/useFuseSearch'
import type { Soldier } from './lib/types'
import SoldierModal from './components/SoldierModal'
import SoldierResults, { countBorci } from './components/SoldierResults'
import { SearchIcon } from './components/Icons'
import { sqQuotes } from './lib/typography'
import BandPhoto from './components/BandPhoto'

const EXAMPLES = ['Končar', 'Petar Abramović', 'Gračac']

export default function Home() {
  const [allSoldiers, setAllSoldiers] = useState<Soldier[]>([])
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)

  const { results, searchTerm, setSearchTerm, isSearching } = useFuseSearch(
    allSoldiers,
    { showAllOnEmpty: false }
  )

  useEffect(() => {
    // Load every unit's list in the background; the page is usable meanwhile
    const loadAllSoldiers = async () => {
      try {
        const lists = await Promise.all(
          units.map(async (unit) => {
            const response = await fetch(unit.dataFile)
            const data: Soldier[] = await response.json()
            return data.map((soldier) => ({ ...soldier, unit: unit.name }))
          })
        )
        setAllSoldiers(lists.flat())
      } catch {
        setLoadFailed(true)
      } finally {
        setLoading(false)
      }
    }

    loadAllSoldiers()
  }, [])

  const hasQuery = searchTerm.trim().length > 0

  return (
    <div>
      <section className="masthead" aria-labelledby="finder-title">
        <div className="container finder">
          <h1 id="finder-title">Pretraga boraca</h1>
          <div className="finder-field">
            <label htmlFor="search" className="visually-hidden">Prezime, ime ili mesto</label>
            <span className="search-icon"><SearchIcon size={20} /></span>
            <input
              id="search"
              type="search"
              className="search-input"
              placeholder="Prezime, ime ili mesto"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <p className="finder-hint">
            <span>Na primer:</span>
            {EXAMPLES.map((example) => (
              <button key={example} type="button" onClick={() => setSearchTerm(example)}>
                {example}
              </button>
            ))}
          </p>
          <BandPhoto units={units} />
        </div>
      </section>

      <div className="container section" id="results">
        {hasQuery ? (
          loading ? (
            <>
              <p className="results-count">Učitavanje spiskova…</p>
              <ul className="loading-rows" aria-hidden="true">
                {Array.from({ length: 6 }, (_, i) => <li key={i} />)}
              </ul>
            </>
          ) : loadFailed ? (
            <div className="empty">
              <h2>Spiskovi se nisu učitali</h2>
              <p>Proverite internet vezu i osvežite stranu.</p>
            </div>
          ) : isSearching && results.length === 0 ? (
            <div className="empty">
              <h2>Nema boraca za „{searchTerm}“</h2>
              <p>
                Pokušajte samo prezime, ili ime i prezime bez očevog imena. Knjige često
                beleže očevo ime u genitivu, na primer „Milorada“ umesto „Milorad“.
              </p>
            </div>
          ) : (
            <SoldierResults
              results={results}
              showUnit
              onSelect={setSelectedSoldier}
              scrollTargetId="results"
            />
          )
        ) : (
          <>
            <div className="section-head">
              <h2>Jedinice</h2>
              <p className="section-note">Izaberite jedinicu da vidite ceo spisak.</p>
            </div>
            <ul className="unit-grid">
              {units.map((unit) => (
                <li key={unit.id}>
                  <Link href={`/units/${unit.id}`} className="unit-card">
                    <div className="unit-card-photo">
                      <img src={unit.image} alt="" loading="lazy" />
                    </div>
                    <div className="unit-card-body">
                      <h3 className="unit-name">{sqQuotes(unit.name)}</h3>
                      <p className="unit-desc">{unit.description}</p>
                      <p className="unit-count">{countBorci(unit.soldierCount).text}</p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      {selectedSoldier && (
        <SoldierModal
          soldier={selectedSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
