'use client'

import { useState, useEffect } from 'react'

interface Soldier {
  last_name: string
  middle_name: string
  first_name: string
  additional_info: string
}

export default function Home() {
  const [soldiers, setSoldiers] = useState<Soldier[]>([])
  const [filteredSoldiers, setFilteredSoldiers] = useState<Soldier[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load soldier data
    fetch('/soldiers.json')
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
  }, [])

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
    return <div className="loading">Loading heroes...</div>
  }

  return (
    <div>
      <section className="search-section">
        <h2 style={{ marginBottom: '1rem' }}>Search Heroes</h2>
        <input
          type="text"
          className="search-input"
          placeholder="Search by name, location, unit..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="stats">
          <div className="stat-item">
            <div className="stat-label">Total Heroes</div>
            <div className="stat-value">{soldiers.length.toLocaleString()}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Search Results</div>
            <div className="stat-value">{filteredSoldiers.length.toLocaleString()}</div>
          </div>
        </div>
      </section>

      {filteredSoldiers.length === 0 ? (
        <div className="no-results">
          No heroes found matching "{searchTerm}"
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
