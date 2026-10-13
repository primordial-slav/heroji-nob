'use client'

import { useState, useEffect, useRef, useMemo, useDeferredValue } from 'react'
import { units } from '@/app/data/units'
import { useFuseSearch } from '@/app/lib/useFuseSearch'
import { useServerSearch } from '@/app/lib/useServerSearch'
import {
  PAGE_SIZES, fullRecord, loadHomeLists, loadPortraitPeople, loadUnitList, loadedHomeLists, loadedPortraitPeople,
  type HomeLists,
} from '@/app/lib/searchIndex'
import { unitByName } from '@/app/lib/records'
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
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState(NO_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  // The soldier whose full record is being loaded for the dialog
  const opening = useRef<Soldier | null>(null)

  // Which page of the results is shown: a new search starts on its first
  const searchKey = JSON.stringify([searchTerm.trim(), filters])
  const [paging, setPaging] = useState({ search: '', page: 1 })
  const [perPage, setPerPage] = useState(PAGE_SIZES[0])
  const page = paging.search === searchKey ? paging.page : 1

  // The server searches every unit's soldiers and sends one page of them (useServerSearch). If it doesn't answer, the
  // page loads every unit's list and searches them itself, as it did before
  const [local, setLocal] = useState(false)
  const server = useServerSearch({ query: searchTerm, filters, page, perPage, enabled: !local })
  useEffect(() => { if (server.failed) setLocal(true) }, [server.failed])

  // The lists the page searches itself; already there when the visitor comes back to the page
  const [lists, setLists] = useState<HomeLists | null>(loadedHomeLists)
  const allSoldiers = lists?.listed ?? NO_SOLDIERS
  const [loadFailed, setLoadFailed] = useState(false)
  const loading = local && !lists && !loadFailed
  const localSearch = useFuseSearch(allSoldiers, { showAllOnEmpty: false, wholeWords: filters.wholeWords, term: searchTerm })
  useEffect(() => {
    if (!local) return
    let current = true
    loadHomeLists()
      .then((loaded) => current && setLists(loaded))
      .catch(() => current && setLoadFailed(true))
    return () => { current = false }
  }, [local])

  // The search and its filters are in the address, so a search can be sent as a link: read once, then kept up to date
  const [addressRead, setAddressRead] = useState(false)
  useEffect(() => {
    const linked = readSearch(new URLSearchParams(window.location.search))
    if (linked.query) setSearchTerm(linked.query)
    setFilters(linked.filters)
    if (filterCount(linked.filters) > 0) setShowFilters(true)
    setAddressRead(true)
  }, [])
  useEffect(() => {
    if (!addressRead) return
    const url = new URL(window.location.href)
    writeSearch(url, searchTerm, filters)
    if (url.href !== window.location.href) window.history.replaceState(window.history.state, '', url)
  }, [addressRead, searchTerm, filters])

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
  }, [])

  // The soldiers of the portraits in the margins, as the lists give them
  const [portraitPeople, setPortraitPeople] = useState<Soldier[]>(() => loadedPortraitPeople() ?? NO_SOLDIERS)
  useEffect(() => {
    if (local) return
    let current = true
    loadPortraitPeople().then((people) => current && setPortraitPeople(people)).catch(() => {})
    return () => { current = false }
  }, [local])

  // The search list has only what search shows; the dialog gets the soldier's full record
  const openSoldier = async (soldier: Soldier) => {
    opening.current = soldier
    const record = await fullRecord(soldier).catch(() => soldier)
    if (opening.current === soldier) setSelectedSoldier(record)
  }

  // The open soldier's unit list, for the dialog's previous and next and its comrades tree: loaded when he is opened
  const dialogUnit = selectedSoldier?.unit
  const [dialogList, setDialogList] = useState<{ unit: string; list: Soldier[] } | null>(null)
  useEffect(() => {
    const unit = unitByName(dialogUnit)
    if (local || !unit) return
    let current = true
    loadUnitList(unit).then((list) => current && setDialogList({ unit: unit.name, list })).catch(() => {})
    return () => { current = false }
  }, [dialogUnit, local])
  const unitSoldiers = local
    ? lists?.byUnit.get(dialogUnit ?? '')
    : dialogList && dialogList.unit === dialogUnit ? dialogList.list : undefined

  const hasQuery = searchTerm.trim().length > 0
  // Filters narrow the search; a place, year, unit or fate alone also lists everyone who matches it
  const shownFilters = useDeferredValue(filters)
  const filtering = narrows(filters)
  const filtersSet = filterCount(filters) > 0
  const localListed = useMemo(
    () => (!local ? NO_SOLDIERS
      : hasQuery ? applyFilters(localSearch.results, shownFilters)
      : narrows(shownFilters) ? applyFilters(allSoldiers, shownFilters) : NO_SOLDIERS),
    [local, hasQuery, localSearch.results, allSoldiers, shownFilters]
  )

  // What the results say, whoever searched
  const found = server.result
  const count = local ? localListed.length : found?.count ?? 0
  const unfiltered = local ? localSearch.results.length : found?.unfiltered ?? 0
  const waiting = local
    ? loading || (!loadFailed && localSearch.pending && localListed.length === 0)
    : server.pending && count === 0

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
              placeholder={t.home.fieldLabel}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              maxLength={200}
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
          waiting ? (
            <>
              <p className="results-count">{loading ? t.home.loading : t.results.searching}</p>
              <ul className="loading-rows" aria-hidden="true">
                {Array.from({ length: 6 }, (_, i) => <li key={i} />)}
              </ul>
            </>
          ) : local && loadFailed ? (
            <div className="empty">
              <h2>{t.home.loadFailedTitle}</h2>
              <p>{t.home.loadFailedText}</p>
            </div>
          ) : count === 0 && filtersSet && !(hasQuery && unfiltered === 0) ? (
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
          ) : hasQuery && count === 0 ? (
            <div className="empty">
              <h2>{t.home.noneTitle(searchTerm)}</h2>
              <p>{t.home.noneText}</p>
            </div>
          ) : local ? (
            <SoldierResults
              results={localListed}
              near={localSearch.near}
              showUnit
              onSelect={openSoldier}
              scrollTargetId="results"
              actions={<ShareSearch />}
            />
          ) : (
            <SoldierResults
              results={found?.soldiers ?? NO_SOLDIERS}
              paged={{
                count,
                firstNear: found?.firstNear ?? -1,
                page: found?.page ?? page,
                perPage: found?.perPage ?? perPage,
                onPage: (to, size) => {
                  setPaging({ search: searchKey, page: to })
                  setPerPage(size)
                },
              }}
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
      <PortraitRails soldiers={local ? allSoldiers : portraitPeople} onOpen={openSoldier} />
      </div>

      {selectedSoldier && (
        <SoldierModal
          key={selectedSoldier.soldier_id}
          soldier={selectedSoldier}
          unitSoldiers={unitSoldiers}
          onOpen={openSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
