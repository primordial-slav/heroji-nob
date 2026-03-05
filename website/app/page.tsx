'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { units } from './data/units'
import { useFuseSearch } from './lib/useFuseSearch'
import type { Soldier } from './lib/types'

export default function Home() {
  const [allSoldiers, setAllSoldiers] = useState<Soldier[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(50)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  const [showModal, setShowModal] = useState(false)

  const { results, searchTerm, setSearchTerm, isSearching } = useFuseSearch(
    allSoldiers,
    { showAllOnEmpty: false }
  )

  useEffect(() => {
    // Load soldier data from all units
    const loadAllSoldiers = async () => {
      try {
        const allSoldiersData: Soldier[] = []

        // Fetch data from each unit
        for (const unit of units) {
          const response = await fetch(unit.dataFile)
          const data = await response.json()
          // Add unit name to each soldier
          const soldiersWithUnit = data.map((soldier: Soldier) => ({
            ...soldier,
            unit: unit.name
          }))
          allSoldiersData.push(...soldiersWithUnit)
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

  // Reset page when results change
  useEffect(() => {
    setCurrentPage(1)
  }, [results])

  // Pagination calculations
  const totalPages = Math.ceil(results.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentSoldiers = results.slice(startIndex, endIndex)

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

  const handleSoldierClick = (soldier: Soldier) => {
    setSelectedSoldier(soldier)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setSelectedSoldier(null)
  }

  const totalSoldiers = units.reduce((sum, unit) => sum + unit.soldierCount, 0)

  if (loading) {
    return <div className="loading">Učitavanje...</div>
  }

  return (
    <div>
      <section className="search-section">
        <h2 style={{ marginBottom: '1rem' }}>Pretraži borce</h2>
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
          {isSearching && (
            <div className="stat-item">
              <div className="stat-label">Rezultati pretrage</div>
              <div className="stat-value">{results.length.toLocaleString()}</div>
            </div>
          )}
        </div>
      </section>

      {isSearching ? (
        // Show search results
        <>
          {results.length === 0 ? (
            <div className="no-results">
              Nema rezultata za "{searchTerm}"
            </div>
          ) : (
            <>
              {/* Per-page selector */}
              <div className="pagination-controls" style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  <span style={{ color: 'var(--text-accent-secondary)', fontWeight: 'bold' }}>Prikaži po stranici:</span>
                  {[50, 100, 200].map(count => (
                    <button
                      key={count}
                      onClick={() => handleItemsPerPageChange(count)}
                      className={itemsPerPage === count ? 'page-button active' : 'page-button'}
                    >
                      {count}
                    </button>
                  ))}
                  <span style={{ marginLeft: 'auto', color: 'var(--text-accent-secondary)' }}>
                    Stranica {currentPage} od {totalPages}
                  </span>
                </div>
              </div>

              <div className="soldiers-grid">
                {currentSoldiers.map((soldier, index) => (
                  <div
                    key={startIndex + index}
                    className="soldier-card"
                    onClick={() => handleSoldierClick(soldier)}
                    style={{ cursor: 'pointer' }}
                  >
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

      {/* Soldier Detail Modal */}
      {showModal && selectedSoldier && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeModal}>×</button>
            <h2 className="modal-title">{selectedSoldier.full_name}</h2>
            <div className="modal-details">
              {selectedSoldier.fathers_name && (
                <div className="modal-detail-row">
                  <span className="modal-label">Ime oca:</span>
                  <span className="modal-value">{selectedSoldier.fathers_name}</span>
                </div>
              )}
              {selectedSoldier.birth_year && (
                <div className="modal-detail-row">
                  <span className="modal-label">Godina rođenja:</span>
                  <span className="modal-value">{selectedSoldier.birth_year}</span>
                </div>
              )}
              {selectedSoldier.unit && (
                <div className="modal-detail-row">
                  <span className="modal-label">Jedinica:</span>
                  <span className="modal-value">{selectedSoldier.unit}</span>
                </div>
              )}
              {selectedSoldier.additional_info && (
                <div className="modal-detail-row">
                  <span className="modal-label">Dodatne informacije:</span>
                  <span className="modal-value">{selectedSoldier.additional_info}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
