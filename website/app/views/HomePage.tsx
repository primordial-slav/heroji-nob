'use client'

import { useState, useEffect, useRef, useMemo, useDeferredValue } from 'react'
import { units } from '@/app/data/units'
import { useFuseSearch } from '@/app/lib/useFuseSearch'
import { SEARCH_INDEX_PARTS, searchIndexPath, fullRecord, loadHomeLists, loadedHomeLists, type HomeLists } from '@/app/lib/searchIndex'
import type { Soldier } from '@/app/lib/types'
import SoldierModal from '@/app/components/SoldierModal'
import SoldierResults from '@/app/components/SoldierResults'
import { SearchIcon } from '@/app/components/Icons'
import { totalNames } from '@/app/lib/totals'
import BandPhoto from '@/app/components/BandPhoto'
import OnThisDay from '@/app/components/OnThisDay'
import UnitsByYear from '@/app/components/UnitsByYear'
import PortraitRails from '@/app/components/PortraitRails'
import { HOME_RESET } from '@/app/components/HomeLink'
import SearchFilters, { FilterToggle, ShareSearch } from '@/app/components/SearchFilters'
import { NO_FILTERS, applyFilters, filterCount, narrows, readSearch, writeSearch } from '@/app/lib/searchFilters'
import { useT } from '@/app/i18n/LangContext'
import RichText from '@/app/i18n/RichText'

const NO_SOLDIERS: Soldier[] = []

export default function HomePage() {
  const t = useT()
  // Every unit's list, in its short search form; already there when the visitor comes back to the page
  const [lists, setLists] = useState<HomeLists | null>(loadedHomeLists)
  const allSoldiers = lists?.listed ?? NO_SOLDIERS
  const [loadFailed, setLoadFailed] = useState(false)
  const loading = !lists && !loadFailed
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  // The soldier whose full record is being loaded for the dialog
  const opening = useRef<Soldier | null>(null)
  const [filters, setFilters] = useState(NO_FILTERS)
  const [showFilters, setShowFilters] = useState(false)

  const { results, searchTerm, setSearchTerm, isSearching, pending } = useFuseSearch(
    allSoldiers,
    { showAllOnEmpty: false, wholeWords: filters.wholeWords }
  )

  // The search and its filters are in the address, so a search can be sent as a link: read once, then kept up to date
  const [addressRead, setAddressRead] = useState(false)
  useEffect(() => {
    const linked = readSearch(new URLSearchParams(window.location.search))
    if (linked.query) setSearchTerm(linked.query)
    setFilters(linked.filters)
    if (filterCount(linked.filters) > 0) setShowFilters(true)
    setAddressRead(true)
  }, [setSearchTerm])
  useEffect(() => {
    if (!addressRead) return
    const url = new URL(window.location.href)
    writeSearch(url, searchTerm, filters)
    if (url.href !== window.location.href) window.history.replaceState(window.history.state, '', url)
  }, [addressRead, searchTerm, filters])

  useEffect(() => {
    // Load every unit's list in the background; the page is usable meanwhile
    let current = true
    loadHomeLists()
      .then((loaded) => current && setLists(loaded))
      .catch(() => current && setLoadFailed(true))
    return () => { current = false }
  }, [])

  useEffect(() => {
    // The site name and "Početna" start the page over, also when it is already open
    const reset = () => {
      setSearchTerm('')
      setFilters(NO_FILTERS)
      setShowFilters(false)
      opening.current = null
      setSelectedSoldier(null)
      window.scrollTo({ top: 0 })
    }
    window.addEventListener(HOME_RESET, reset)
    return () => window.removeEventListener(HOME_RESET, reset)
  }, [setSearchTerm])

  // The search list has only what search shows; the dialog gets the soldier's full record
  const openSoldier = async (soldier: Soldier) => {
    opening.current = soldier
    const record = await fullRecord(soldier).catch(() => soldier)
    if (opening.current === soldier) setSelectedSoldier(record)
  }

  const hasQuery = searchTerm.trim().length > 0
  // Filters narrow the search; a place, year, unit or fate alone also lists everyone who matches it
  const shownFilters = useDeferredValue(filters)
  const filtering = narrows(filters)
  const listed = useMemo(
    () => (hasQuery ? applyFilters(results, shownFilters) : narrows(shownFilters) ? applyFilters(allSoldiers, shownFilters) : []),
    [hasQuery, results, allSoldiers, shownFilters]
  )
  const filtersSet = filterCount(filters) > 0

  return (
    <div>
      {/* The lists start loading with the page rather than once its scripts have run; at low priority, after
          what the page needs to show */}
      {!lists && SEARCH_INDEX_PARTS.map((_, part) => (
        <link key={part} rel="preload" href={searchIndexPath(part)} as="fetch" crossOrigin="anonymous" fetchPriority="low" />
      ))}
      <section className="masthead" aria-labelledby="finder-title">
        <div className="container finder">
          <h1 id="finder-title">{t.home.title}</h1>
          <div className="finder-field">
            <label htmlFor="search" className="visually-hidden">{t.home.fieldLabel}</label>
            <span className="search-icon"><SearchIcon size={20} /></span>
            <input
              id="search"
              type="search"
              className="search-input"
              placeholder={t.home.fieldLabel}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoComplete="off"
              spellCheck={false}
            />
            <FilterToggle
              open={showFilters}
              count={filterCount(filters)}
              controls="home-filters"
              onClick={() => setShowFilters((open) => !open)}
            />
          </div>
          {showFilters && <SearchFilters id="home-filters" filters={filters} onChange={setFilters} withUnit />}
          <p className="finder-hint">{t.home.total(totalNames)}</p>
          <BandPhoto units={units} />
        </div>
      </section>

      <div className="home-body">
      <div className="container section" id="results">
        {hasQuery || filtering ? (
          // A first search, or one after an empty result, shows the loading rows until its results are in
          loading || (!loadFailed && pending && listed.length === 0) ? (
            <>
              <p className="results-count">{loading ? t.home.loading : t.results.searching}</p>
              <ul className="loading-rows" aria-hidden="true">
                {Array.from({ length: 6 }, (_, i) => <li key={i} />)}
              </ul>
            </>
          ) : loadFailed ? (
            <div className="empty">
              <h2>{t.home.loadFailedTitle}</h2>
              <p>{t.home.loadFailedText}</p>
            </div>
          ) : listed.length === 0 && filtersSet && !(hasQuery && results.length === 0) ? (
            <div className="empty">
              <h2>{t.filters.noneTitle(hasQuery ? searchTerm : '')}</h2>
              <p>
                <RichText
                  text={t.filters.noneText}
                  render={(part) => (
                    <button type="button" className="link-button" onClick={() => setFilters(NO_FILTERS)}>{part}</button>
                  )}
                />
              </p>
            </div>
          ) : isSearching && listed.length === 0 ? (
            <div className="empty">
              <h2>{t.home.noneTitle(searchTerm)}</h2>
              <p>{t.home.noneText}</p>
            </div>
          ) : (
            <SoldierResults
              results={listed}
              showUnit
              onSelect={openSoldier}
              scrollTargetId="results"
              actions={<ShareSearch />}
            />
          )
        ) : (
          <>
            <OnThisDay onSelect={openSoldier} />
            <h2 className="visually-hidden">{t.home.unitsTitle}</h2>
            <UnitsByYear units={units} />
          </>
        )}
      </div>
      <PortraitRails soldiers={allSoldiers} onOpen={openSoldier} />
      </div>

      {selectedSoldier && (
        <SoldierModal
          key={selectedSoldier.soldier_id}
          soldier={selectedSoldier}
          unitSoldiers={lists?.byUnit.get(selectedSoldier.unit ?? '')}
          onOpen={openSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
