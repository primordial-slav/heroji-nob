'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { units } from './data/units'

interface Soldier {
  last_name: string
  middle_name: string
  first_name: string
  additional_info: string
}

export default function Home() {
  const [allSoldiers, setAllSoldiers] = useState<Soldier[]>([])
  const [filteredSoldiers, setFilteredSoldiers] = useState<Soldier[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [showingSearch, setShowingSearch] = useState(false)

  useEffect(() => {
    // Load all soldier data
    fetch('/soldiers.json')
      .then(res => res.json())
      .then(data => {
        setAllSoldiers(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading soldiers:', err)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    // Filter soldiers based on search term
    if (!searchTerm) {
      setFilteredSoldiers([])
      setShowingSearch(false)
      return
    }

    setShowingSearch(true)
    const term = searchTerm.toLowerCase()
    const filtered = allSoldiers.filter(soldier => {
      const fullName = `${soldier.last_name} ${soldier.middle_name} ${soldier.first_name}`.toLowerCase()
      const info = soldier.additional_info.toLowerCase()
      return fullName.includes(term) || info.includes(term)
    })
    setFilteredSoldiers(filtered)
  }, [searchTerm, allSoldiers])

  const formatSoldierName = (soldier: Soldier) => {
    const parts = [soldier.last_name]
    if (soldier.middle_name) parts.push(soldier.middle_name)
    if (soldier.first_name) parts.push(soldier.first_name)
    return parts.join(' ')
  }

  const totalSoldiers = units.reduce((sum, unit) => sum + unit.soldierCount, 0)

  if (loading) {
    return <div className="loading">Učitavanje...</div>
  }

  return (
    <div>
      <section className="search-section">
        <h2 style={{ marginBottom: '1rem' }}>Pretraži partizane</h2>
        <input
          type="text"
          className="search-input"
          placeholder="Pretraži po imenu, lokaciji, jedinici..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="stats">
          <div className="stat-item">
            <div className="stat-label">Ukupno heroja</div>
            <div className="stat-value">{totalSoldiers.toLocaleString()}</div>
          </div>
          {showingSearch && (
            <div className="stat-item">
              <div className="stat-label">Rezultati pretrage</div>
              <div className="stat-value">{filteredSoldiers.length.toLocaleString()}</div>
            </div>
          )}
        </div>
      </section>

      {showingSearch ? (
        // Show search results
        <>
          {filteredSoldiers.length === 0 ? (
            <div className="no-results">
              Nema rezultata za "{searchTerm}"
            </div>
          ) : (
            <div className="soldiers-grid">
              {filteredSoldiers.map((soldier, index) => (
                <div key={index} className="soldier-card">
                  <div className="soldier-name">
                    {formatSoldierName(soldier)}
                  </div>
                  {soldier.additional_info && (
                    <div className="soldier-info">
                      {soldier.additional_info}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        // Show unit cards
        <>
          <section style={{ marginTop: '2rem' }}>
            <h2 className="section-title">Jedinice</h2>
            <div className="units-grid">
              {units.map(unit => (
                <Link href={`/units/${unit.id}`} key={unit.id} className="unit-card">
                  <div className="unit-image-container">
                    <Image
                      src={unit.image}
                      alt={unit.name}
                      width={400}
                      height={300}
                      className="unit-image"
                    />
                  </div>
                  <div className="unit-info">
                    <h3 className="unit-name">{unit.name}</h3>
                    <p className="unit-description">{unit.description}</p>
                    <div className="unit-stats">
                      <span className="unit-soldier-count">
                        {unit.soldierCount.toLocaleString()} boraca
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
