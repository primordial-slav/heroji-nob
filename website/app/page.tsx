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
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(50)

  useEffect(() => {
    // Load soldier data from all units
    const loadAllSoldiers = async () => {
      try {
        const allSoldiersData: Soldier[] = []

        // Fetch data from each unit
        for (const unit of units) {
          const response = await fetch(unit.dataFile)
          const data = await response.json()
          allSoldiersData.push(...data)
        }

        setAllSoldiers(allSoldiersData)
        setLoading(false)
      } catch (err) {
        console.error('Error loading soldiers:', err)
        setLoading(false)
      }
    }

    loadAllSoldiers()
  }, [])

  useEffect(() => {
    // Filter soldiers based on search term
    if (!searchTerm) {
      setFilteredSoldiers([])
      setShowingSearch(false)
      return
    }

    setShowingSearch(true)
    setCurrentPage(1) // Reset to first page when search changes
    const term = searchTerm.toLowerCase()
    const filtered = allSoldiers.filter(soldier => {
      const fullName = `${soldier.last_name} ${soldier.middle_name} ${soldier.first_name}`.toLowerCase()
      const info = soldier.additional_info.toLowerCase()
      return fullName.includes(term) || info.includes(term)
    })
    setFilteredSoldiers(filtered)
  }, [searchTerm, allSoldiers])

  // Pagination calculations
  const totalPages = Math.ceil(filteredSoldiers.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentSoldiers = filteredSoldiers.slice(startIndex, endIndex)

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage)
    setCurrentPage(1) // Reset to first page when changing items per page
  }

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
            <div className="stat-label">Ukupno boraca</div>
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
            <>
              {/* Per-page selector */}
              <div className="pagination-controls" style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  <span style={{ color: '#6B1A1A', fontWeight: 'bold' }}>Prikaži po stranici:</span>
                  {[50, 100, 200].map(count => (
                    <button
                      key={count}
                      onClick={() => handleItemsPerPageChange(count)}
                      className={itemsPerPage === count ? 'page-button active' : 'page-button'}
                    >
                      {count}
                    </button>
                  ))}
                  <span style={{ marginLeft: 'auto', color: '#6B1A1A' }}>
                    Stranica {currentPage} od {totalPages}
                  </span>
                </div>
              </div>

              <div className="soldiers-grid">
                {currentSoldiers.map((soldier, index) => (
                  <div key={startIndex + index} className="soldier-card">
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

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination" style={{ marginTop: '2rem' }}>
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="page-button"
                  >
                    ← Prethodna
                  </button>

                  {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
                    // Show first few, last few, and pages around current
                    const pageNum = i + 1
                    const showPage =
                      pageNum <= 3 ||
                      pageNum > totalPages - 3 ||
                      (pageNum >= currentPage - 1 && pageNum <= currentPage + 1)

                    if (!showPage && (pageNum === 4 || pageNum === totalPages - 3)) {
                      return <span key={pageNum} style={{ padding: '0 0.5rem' }}>...</span>
                    }

                    if (!showPage) return null

                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={currentPage === pageNum ? 'page-button active' : 'page-button'}
                      >
                        {pageNum}
                      </button>
                    )
                  })}

                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="page-button"
                  >
                    Sledeća →
                  </button>
                </div>
              )}
            </>
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
