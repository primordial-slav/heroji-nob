'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Unit } from '@/app/data/units'
import { useFuseSearch } from '@/app/lib/useFuseSearch'
import type { Soldier } from '@/app/lib/types'
import SoldierModal from '@/app/components/SoldierModal'

interface UnitPageClientProps {
  unit: Unit
}

export default function UnitPageClient({ unit }: UnitPageClientProps) {
  const [soldiers, setSoldiers] = useState<Soldier[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(50)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  const [showModal, setShowModal] = useState(false)

  const { results, searchTerm, setSearchTerm } = useFuseSearch(
    soldiers,
    { showAllOnEmpty: true }
  )

  useEffect(() => {
    // Load soldier data for this unit
    fetch(unit.dataFile)
      .then(res => res.json())
      .then(data => {
        setSoldiers(data)
        setLoading(false)
      })
      .catch(() => {
        setLoading(false)
      })
  }, [unit])

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
            <div className="stat-value">{results.length.toLocaleString()}</div>
          </div>
        </div>
      </section>

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

      {/* Soldier Detail Modal */}
      {showModal && selectedSoldier && (
        <SoldierModal
          soldier={selectedSoldier}
          unitName={unit.name}
          onClose={closeModal}
        />
      )}
    </div>
  )
}
