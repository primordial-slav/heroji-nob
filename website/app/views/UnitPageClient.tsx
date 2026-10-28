'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { Unit } from '@/app/data/units'
import { useServerSearch } from '@/app/lib/useServerSearch'
import { PAGE_SIZES, fullRecord, loadKin } from '@/app/lib/searchIndex'
import type { Soldier } from '@/app/lib/types'
import SoldierModal, { usePreloadSoldierModal } from '@/app/components/LazySoldierModal'
import SoldierResults from '@/app/components/SoldierResults'
import { ArrowLeftIcon, SearchIcon } from '@/app/components/Icons'
import { RECORD_PARAM } from '@/app/lib/records'
import { photoPosition } from '@/app/data/photoFocus'
import { unitImageProps } from '@/app/lib/unitImage'
import SearchFilters, { FilterToggle, ShareSearch } from '@/app/components/SearchFilters'
import { NO_FILTERS, filterCount, readSearch, writeSearch } from '@/app/lib/searchFilters'
import { useLang, useLocalePath, useT, useUnitText } from '@/app/i18n/LangContext'
import RichText from '@/app/i18n/RichText'

interface UnitPageClientProps {
  unit: Unit
  /** The list's first page, full records, in the page itself */
  firstPage: Soldier[]
  /** How many soldiers the list has */
  total: number
}

const NO_SOLDIERS: Soldier[] = []
// The photo runs across the whole window, a little wider than it (.unit-hero-photo)
const HERO_SIZES = '104vw'

export default function UnitPageClient({ unit, firstPage, total }: UnitPageClientProps) {
  usePreloadSoldierModal()
  const lang = useLang()
  const unitText = useUnitText()
  const t = useT()
  const to = useLocalePath()
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState(NO_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  // The soldier whose full record is being loaded for the dialog
  const opening = useRef<Soldier | null>(null)
  const filtersSet = filterCount(filters, false) > 0

  // Which page of the list is shown: a new search starts on its first
  const searchKey = JSON.stringify([searchTerm.trim(), filters])
  const [paging, setPaging] = useState({ search: '', page: 1 })
  const [perPage, setPerPage] = useState(PAGE_SIZES[0])
  const page = paging.search === searchKey ? paging.page : 1
  const onPage = (to: number, size: number) => {
    setPaging({ search: searchKey, page: to })
    setPerPage(size)
  }
  // The whole list's first page is in the page itself
  const onFirstPage = !searchTerm.trim() && !filtersSet && page === 1 && perPage === PAGE_SIZES[0]

  // The server searches the unit's soldiers and sends a page of them (useServerSearch)
  const server = useServerSearch({ query: searchTerm, filters, page, perPage, unit: unit.id, enabled: !onFirstPage })

  // The search and its filters are in the address (next to an open record's ?borac=), so a search can be sent as a link
  const [addressRead, setAddressRead] = useState(false)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const fromAddress = readSearch(params)
    if (fromAddress.query) setSearchTerm(fromAddress.query)
    setFilters({ ...fromAddress.filters, unit: '' })
    if (filterCount(fromAddress.filters, false) > 0) setShowFilters(true)
    setAddressRead(true)
  }, [])
  useEffect(() => {
    if (!addressRead) return
    const url = new URL(window.location.href)
    writeSearch(url, searchTerm, filters, false)
    if (url.href !== window.location.href) window.history.replaceState(window.history.state, '', url)
  }, [addressRead, searchTerm, filters])

  // A link to one record (?borac=<id>) opens it once the server has found it, unless the visitor has opened one by then
  const linkHandled = useRef(false)

  // The list has only what search shows; the dialog gets the soldier's full record
  const openSoldier = async (soldier: Soldier) => {
    linkHandled.current = true
    opening.current = soldier
    const record = await fullRecord({ ...soldier, unit: soldier.unit ?? unit.name }).catch(() => soldier)
    if (opening.current === soldier) setSelectedSoldier(record)
  }

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get(RECORD_PARAM)
    if (!id) {
      linkHandled.current = true
      return
    }
    loadKin(unit, id)
      .then((kin) => {
        if (linkHandled.current) return
        linkHandled.current = true
        if (kin) openSoldier(kin.self)
      })
      .catch(() => { linkHandled.current = true })
    // the address is read once, when the page opens
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unit])

  // The address bar follows the open record, so copying it gives that record's link
  useEffect(() => {
    if (!linkHandled.current) return
    const url = new URL(window.location.href)
    if (selectedSoldier) url.searchParams.set(RECORD_PARAM, selectedSoldier.soldier_id)
    else url.searchParams.delete(RECORD_PARAM)
    window.history.replaceState(window.history.state, '', url)
  }, [selectedSoldier])

  // What the list says
  const found = server.result
  const searching = searchTerm.trim().length > 0
  const count = found?.count ?? 0
  const unfiltered = found?.unfiltered ?? 0
  // The page's own first page shows unless the address asks for a search
  const early = onFirstPage
  const waiting = server.pending && count === 0 && !server.failed

  return (
    <div>
      <section className="container unit-hero">
        <Link href={to('/')} className="back-link"><ArrowLeftIcon size={16} /> {t.unit.allUnits}</Link>
        <div className="unit-hero-body">
          <img {...unitImageProps(unit.image, HERO_SIZES)} alt={unitText.name(unit)} className="unit-hero-photo" style={{ objectPosition: photoPosition(unit.id) }} />
          <div>
            <h1>{unitText.name(unit)}</h1>
            <p className="unit-hero-desc">{unitText.description(unit)}</p>
          </div>
        </div>
      </section>

      <div className="container">
        <div className="unit-search">
          <label htmlFor="unit-search">{t.unit.search}</label>
          <div className="finder-field">
            <span className="search-icon"><SearchIcon size={20} /></span>
            <input
              id="unit-search"
              type="search"
              className="search-input"
              placeholder={t.unit.placeholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              maxLength={200}
              autoComplete="off"
              spellCheck={false}
            />
            <FilterToggle
              open={showFilters}
              count={filterCount(filters, false)}
              controls="unit-filters"
              onClick={() => setShowFilters((open) => !open)}
            />
          </div>
          {showFilters && <SearchFilters id="unit-filters" filters={filters} onChange={setFilters} />}
        </div>

        <div id="results">
          {/* A search after an empty result shows the loading rows until its results are in */}
          {early ? (
            <SoldierResults
              results={firstPage}
              paged={{ count: total, firstNear: -1, page: 1, perPage, onPage }}
              onSelect={openSoldier}
              scrollTargetId="results"
            />
          ) : waiting ? (
            <ul className="loading-rows" aria-label={t.results.searching}>
              {Array.from({ length: 8 }, (_, i) => <li key={i} />)}
            </ul>
          ) : server.failed ? (
            <div className="empty">
              <h2>{t.unit.loadFailedTitle}</h2>
              <p>{t.unit.loadFailedText}</p>
            </div>
          ) : count === 0 && filtersSet && unfiltered > 0 ? (
            <div className="empty">
              <h2>{t.filters.noneTitle(searching ? searchTerm : '')}</h2>
              <p>
                <RichText
                  text={t.filters.noneText}
                  render={(part) => (
                    <button type="button" className="link-button" onClick={() => setFilters(NO_FILTERS)}>{part}</button>
                  )}
                />
              </p>
            </div>
          ) : count === 0 ? (
            <div className="empty">
              <h2>{t.unit.noneTitle(searchTerm)}</h2>
              <p>
                <RichText text={t.unit.noneText} render={(part) => <Link href={to('/')}>{part}</Link>} />
              </p>
            </div>
          ) : (
            <SoldierResults
              results={found?.soldiers ?? NO_SOLDIERS}
              paged={{
                count,
                firstNear: found?.firstNear ?? -1,
                page: found?.page ?? page,
                perPage: found?.perPage ?? perPage,
                onPage,
              }}
              onSelect={openSoldier}
              scrollTargetId="results"
              actions={(searching || filtersSet) && <ShareSearch />}
            />
          )}
        </div>
      </div>

      {selectedSoldier && (
        <SoldierModal
          key={selectedSoldier.soldier_id}
          soldier={selectedSoldier}
          unitName={unit.name}
          onOpen={openSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
