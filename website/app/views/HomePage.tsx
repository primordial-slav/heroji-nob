'use client'

import { useState, useEffect, useRef } from 'react'
import { units } from '@/app/data/units'
import { useServerSearch } from '@/app/lib/useServerSearch'
import { useBackClosesRecord } from '@/app/lib/useBackClosesRecord'
import { useRecordWalk } from '@/app/lib/useRecordWalk'
import { PAGE_SIZES, fullRecord, loadPortraitPeople, loadedPortraitPeople } from '@/app/lib/searchIndex'
import type { Soldier } from '@/app/lib/types'
import SoldierModal, { usePreloadSoldierModal } from '@/app/components/LazySoldierModal'
import SoldierResults from '@/app/components/SoldierResults'
import MissingSoldierForm, { MissingSoldierAsk } from '@/app/components/MissingSoldierForm'
import { MISSING_FORM_HASH } from '@/app/lib/missingForm'
import { SearchIcon } from '@/app/components/Icons'
import { totalNames } from '@/app/lib/totals'
import BandPhoto from '@/app/components/BandPhoto'
import OnThisDay from '@/app/components/OnThisDay'
import HomeDoors from '@/app/components/HomeDoors'
import HomeNews from '@/app/components/HomeNews'
import PortraitRails from '@/app/components/PortraitRails'
import type { HomePictures } from '@/app/lib/homePictures'
import { HOME_RESET } from '@/app/components/HomeLink'
import SearchFilters, { FilterToggle, ShareSearch } from '@/app/components/SearchFilters'
import { birthYear, NO_FILTERS, filterCount, narrows, readSearch, writeSearch } from '@/app/lib/searchFilters'
import { useT } from '@/app/i18n/LangContext'
import RichText from '@/app/i18n/RichText'

const NO_SOLDIERS: Soldier[] = []

export default function HomePage({ pictures }: { pictures: HomePictures }) {
  usePreloadSoldierModal()
  const t = useT()
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState(NO_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  // The form for a fighter who is not on the site, opened from the line under the search field: it stands right
  // under the band, and the copies at the end of a search wait until it is closed (one form, one set of field ids)
  const [askOpen, setAskOpen] = useState(false)
  // The soldier whose full record is being loaded for the dialog
  const opening = useRef<Soldier | null>(null)
  useBackClosesRecord(selectedSoldier?.soldier_id, () => setSelectedSoldier(null))

  // Which page of the results is shown: a new search starts on its first
  const searchKey = JSON.stringify([searchTerm.trim(), filters])
  const [paging, setPaging] = useState({ search: '', page: 1 })
  const [perPage, setPerPage] = useState(PAGE_SIZES[0])
  const page = paging.search === searchKey ? paging.page : 1

  // The server searches every unit's soldiers and sends one page of them (useServerSearch)
  const server = useServerSearch({ query: searchTerm, filters, page, perPage })

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

  // The footer's "pošaljite nam šta znate o njemu" (/#prijava) opens the form under the band: on arriving here, or on
  // this page itself, where the link only changes the hash. The hash is taken off again, so a reload doesn't reopen it.
  useEffect(() => {
    const openFromAddress = () => {
      if (window.location.hash !== `#${MISSING_FORM_HASH}`) return
      setAskOpen(true)
      // already open, the form takes the focus (and comes into view) again; a newly opened one takes it itself
      window.setTimeout(() => document.getElementById('missing-soldier')?.focus(), 50)
      const url = new URL(window.location.href)
      url.hash = ''
      window.history.replaceState(window.history.state, '', url)
    }
    openFromAddress()
    window.addEventListener('hashchange', openFromAddress)
    return () => window.removeEventListener('hashchange', openFromAddress)
  }, [])

  useEffect(() => {
    // The site name and "Početna" start the page over, also when it is already open
    const reset = () => {
      setSearchTerm('')
      setFilters(NO_FILTERS)
      setShowFilters(false)
      setAskOpen(false)
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
    let current = true
    loadPortraitPeople().then((people) => current && setPortraitPeople(people)).catch(() => {})
    return () => { current = false }
  }, [])

  // The search list has only what search shows; the dialog gets the soldier's full record
  const openSoldier = async (soldier: Soldier) => {
    opening.current = soldier
    const record = await fullRecord(soldier).catch(() => soldier)
    if (opening.current === soldier) setSelectedSoldier(record)
  }

  const hasQuery = searchTerm.trim().length > 0
  // Filters narrow the search; a place, year, unit or fate alone also lists everyone who matches it
  const filtering = narrows(filters)
  const filtersSet = filterCount(filters) > 0
  const walk = useRecordWalk({ searching: hasQuery || filtering, query: searchTerm, filters, found: server.result, soldierId: selectedSoldier?.soldier_id })

  // What the results say
  const found = server.result
  const count = found?.count ?? 0
  const unfiltered = found?.unfiltered ?? 0
  const waiting = server.pending && count === 0 && !server.failed
  const missingForm = !askOpen && <MissingSoldierForm query={searchTerm} />

  return (
    <div>
      <section className="masthead" aria-labelledby="finder-title">
        <div className={hasQuery || filtering ? 'container finder is-searching' : 'container finder'}>
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
          <p className="finder-hint">
            {t.home.total(totalNames)}
            <MissingSoldierAsk open={askOpen} onOpen={() => setAskOpen(true)} />
          </p>
          <BandPhoto units={units} />
        </div>
      </section>

      <div className="home-body">
      <div className="container section" id="results">
        {askOpen && <MissingSoldierForm query={searchTerm} startOpen onClose={() => setAskOpen(false)} />}
        {hasQuery || filtering ? (
          // A first search, or one after an empty result, shows the loading rows until its results are in
          waiting ? (
            <>
              <p className="results-count">{t.results.searching}</p>
              <ul className="loading-rows" aria-hidden="true">
                {Array.from({ length: 6 }, (_, i) => <li key={i} />)}
              </ul>
            </>
          ) : server.failed ? (
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
              {!filters.withoutYear && (found?.undated ?? 0) > 0 && (
                <p>
                  <button type="button" className="link-button" onClick={() => setFilters({ ...filters, withoutYear: true })}>
                    {t.results.undatedShow(found?.undated ?? 0)}
                  </button>
                </p>
              )}
              {missingForm}
            </div>
          ) : hasQuery && count === 0 ? (
            <div className="empty">
              <h2>{t.home.noneTitle(searchTerm)}</h2>
              <p>{t.home.noneText}</p>
              {missingForm}
            </div>
          ) : (
            <>
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
              undated={birthYear(filters.year) !== null ? {
                count: found?.undated ?? 0,
                included: filters.withoutYear,
                onToggle: () => setFilters({ ...filters, withoutYear: !filters.withoutYear }),
              } : undefined}
              showUnit
              onSelect={openSoldier}
              scrollTargetId="results"
              actions={<ShareSearch />}
            />
            {/* he may not be among them */}
            {hasQuery && missingForm}
            </>
          )
        ) : (
          <>
            <OnThisDay onSelect={openSoldier} />
            <HomeDoors pictures={pictures} />
            <HomeNews />
          </>
        )}
      </div>
      <PortraitRails pictures={pictures} soldiers={portraitPeople} onOpen={openSoldier} />
      </div>

      {selectedSoldier && (
        <SoldierModal
          key={selectedSoldier.soldier_id}
          soldier={selectedSoldier}
          walk={walk}
          onOpen={openSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
