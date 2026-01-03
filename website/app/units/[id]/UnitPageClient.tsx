'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Unit } from '@/app/data/units'

interface Soldier {
  last_name: string
  middle_name: string
  first_name: string
  additional_info: string
}

interface UnitPageClientProps {
  unit: Unit
}

export default function UnitPageClient({ unit }: UnitPageClientProps) {
  const [soldiers, setSoldiers] = useState<Soldier[]>([])
  const [filteredSoldiers, setFilteredSoldiers] = useState<Soldier[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load soldier data for this unit
    fetch(unit.dataFile)
      .then(res => res.json())
      .then(data => {
        setSoldiers(data)
        setFilteredSoldiers(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading soldiers:', err)
        setLoading(false)
      })
  }, [unit])

  useEffect(() => {
    // Filter soldiers based on search term
    if (!searchTerm) {
      setFilteredSoldiers(soldiers)
      return
    }

    const term = searchTerm.toLowerCase()
    const filtered = soldiers.filter(soldier => {
      const fullName = `${soldier.last_name} ${soldier.middle_name} ${soldier.first_name}`.toLowerCase()
      const info = soldier.additional_info.toLowerCase()
      return fullName.includes(term) || info.includes(term)
    })
    setFilteredSoldiers(filtered)
  }, [searchTerm, soldiers])

  const formatSoldierName = (soldier: Soldier) => {
    const parts = [soldier.last_name]
    if (soldier.middle_name) parts.push(soldier.middle_name)
    if (soldier.first_name) parts.push(soldier.first_name)
    return parts.join(' ')
  }

  if (loading) {
    return <div className="loading">Učitavanje...</div>
  }

  return (
    <div>
      <div className="unit-header">
        <Link href="/" className="back-link">← Nazad na sve jedinice</Link>
        <div className="unit-header-content">
          <div className="unit-header-image">
            <Image
              src={unit.image}
              alt={unit.name}
              width={300}
              height={225}
              className="unit-header-img"
            />
          </div>
          <div className="unit-header-info">
            <h1 className="unit-header-title">{unit.name}</h1>
            <p className="unit-header-description">{unit.description}</p>
          </div>
        </div>
      </div>

      <section className="search-section">
        <h2 style={{ marginBottom: '1rem' }}>Pretraži borce jedinice</h2>
        <input
          type="text"
          className="search-input"
          placeholder="Pretraži po imenu, lokaciji..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="stats">
          <div className="stat-item">
            <div className="stat-label">Ukupno boraca</div>
            <div className="stat-value">{soldiers.length.toLocaleString()}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Rezultati pretrage</div>
            <div className="stat-value">{filteredSoldiers.length.toLocaleString()}</div>
          </div>
        </div>
      </section>

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
    </div>
  )
}
