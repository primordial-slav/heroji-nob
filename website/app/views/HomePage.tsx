'use client'

import { useState, useEffect, useRef, useMemo, useDeferredValue } from 'react'
import { units } from '@/app/data/units'
import { useFuseSearch } from '@/app/lib/useFuseSearch'
import { fullRecord, loadSearchIndex } from '@/app/lib/searchIndex'
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

export default function HomePage() {
  const t = useT()
  const [allSoldiers, setAllSoldiers] = useState<Soldier[]>([])
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  // The soldier whose full record is being loaded for the dialog
  const opening = useRef<Soldier | null>(null)
  const [unitLists, setUnitLists] = useState<Map<string, Soldier[]>>(new Map())
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
    // Load every unit's list in the background, in its short search form; the page is usable meanwhile
    const loadAllSoldiers = async () => {
      try {
        const lists = await loadSearchIndex(units)
        // Each unit's whole list, linked soldiers included, for the comrades tree in the record dialog
        setUnitLists(new Map(units.map((unit, i) => [unit.name, lists[i]])))
        // A soldier linked across units (an entry from another unit's book in other_sources) is listed once,
        // in the first of his units, with the others named
        const linkedAway = new Set<string>()
        const listed: Soldier[] = []
        for (const soldier of lists.flat()) {
          if (linkedAway.has(soldier.soldier_id)) continue
          const links = (soldier.other_sources ?? []).filter((o) => o.unit_file)
          links.forEach((o) => o.soldier_id && linkedAway.add(o.soldier_id))
          const also = links
            .map((o) => units.find((u) => u.dataFile === `/${o.unit_file}`)?.name)
            .filter((u, i, list): u is string => Boolean(u) && u !== soldier.unit && list.indexOf(u) === i)
          listed.push(also.length ? { ...soldier, also_units: also } : soldier)
        }
        setAllSoldiers(listed)
      } catch {
        setLoadFailed(true)
      } finally {
        setLoading(false)
      }
    }

    loadAllSoldiers()
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
              placeholder={t.home.placeholder(totalNames)}
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
          <p className="finder-hint">
            <span>{t.home.examplesLead}</span>
            {t.home.examples.map((example) => (
              <button
                key={example.label}
                type="button"
                onClick={() => {
                  setSearchTerm(example.query)
                  setFilters({ ...NO_FILTERS, place: example.place ?? '' })
                  if (example.place) setShowFilters(true)
                }}
              >
                {example.label}
              </button>
            ))}
          </p>
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
            {!loadFailed && <OnThisDay soldiers={allSoldiers} loading={loading} onSelect={openSoldier} />}
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
          unitSoldiers={unitLists.get(selectedSoldier.unit ?? '')}
          onOpen={openSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
