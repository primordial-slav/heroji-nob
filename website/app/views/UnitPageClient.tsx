'use client'

import { useState, useEffect, useRef, useMemo, useDeferredValue } from 'react'
import Link from 'next/link'
import { Unit } from '@/app/data/units'
import { useFuseSearch } from '@/app/lib/useFuseSearch'
import { fullRecord, listPath, loadUnitList, loadedUnitList } from '@/app/lib/searchIndex'
import type { Soldier } from '@/app/lib/types'
import SoldierModal from '@/app/components/SoldierModal'
import SoldierResults from '@/app/components/SoldierResults'
import { ArrowLeftIcon, SearchIcon } from '@/app/components/Icons'
import { RECORD_PARAM, findRecord } from '@/app/lib/records'
import { photoPosition } from '@/app/data/photoFocus'
import { unitImageProps } from '@/app/lib/unitImage'
import SearchFilters, { FilterToggle, ShareSearch } from '@/app/components/SearchFilters'
import { NO_FILTERS, applyFilters, filterCount, readSearch, writeSearch } from '@/app/lib/searchFilters'
import { useLang, useLocalePath, useT } from '@/app/i18n/LangContext'
import { unitDescription, unitName } from '@/app/i18n/units'
import RichText from '@/app/i18n/RichText'

interface UnitPageClientProps {
  unit: Unit
  /** The list's first page, full records, shown until the list has loaded */
  firstPage: Soldier[]
  /** How many soldiers the list has */
  total: number
}

const NO_SOLDIERS: Soldier[] = []
// The photo runs across the whole window, a little wider than it (.unit-hero-photo)
const HERO_SIZES = '104vw'

export default function UnitPageClient({ unit, firstPage, total }: UnitPageClientProps) {
  const lang = useLang()
  const t = useT()
  const to = useLocalePath()
  // The unit's list in its short search form (lib/searchIndex.ts); already there when the visitor comes back
  const [list, setList] = useState<Soldier[] | null>(() => loadedUnitList(unit) ?? null)
  const soldiers = list ?? NO_SOLDIERS
  const [loadFailed, setLoadFailed] = useState(false)
  const loading = !list && !loadFailed
  const [selectedSoldier, setSelectedSoldier] = useState<Soldier | null>(null)
  // The soldier whose full record is being loaded for the dialog
  const opening = useRef<Soldier | null>(null)
  const [filters, setFilters] = useState(NO_FILTERS)
  const [showFilters, setShowFilters] = useState(false)

  const { results, searchTerm, setSearchTerm, pending } = useFuseSearch(
    soldiers,
    { showAllOnEmpty: true, wholeWords: filters.wholeWords }
  )
  const shownFilters = useDeferredValue(filters)
  const listed = useMemo(() => applyFilters(results, shownFilters, false), [results, shownFilters])
  const filtersSet = filterCount(filters, false) > 0

  // The search and its filters are in the address (next to an open record's ?borac=), so a search can be sent as a link
  const [addressRead, setAddressRead] = useState(false)
  useEffect(() => {
    const linked = readSearch(new URLSearchParams(window.location.search))
    if (linked.query) setSearchTerm(linked.query)
    setFilters({ ...linked.filters, unit: '' })
    if (filterCount(linked.filters, false) > 0) setShowFilters(true)
    setAddressRead(true)
  }, [setSearchTerm])
  useEffect(() => {
    if (!addressRead) return
    const url = new URL(window.location.href)
    writeSearch(url, searchTerm, filters, false)
    if (url.href !== window.location.href) window.history.replaceState(window.history.state, '', url)
  }, [addressRead, searchTerm, filters])

  useEffect(() => {
    let current = true
    loadUnitList(unit)
      .then((loaded) => current && setList(loaded))
      .catch(() => current && setLoadFailed(true))
    return () => { current = false }
  }, [unit])

  // A link to one record (?borac=<id>) opens it once the list has loaded, unless the visitor has opened one by then
  const linkHandled = useRef(false)

  // The list has only what search shows; the dialog gets the soldier's full record
  const openSoldier = async (soldier: Soldier) => {
    linkHandled.current = true
    opening.current = soldier
    const record = await fullRecord(soldier).catch(() => soldier)
    if (opening.current === soldier) setSelectedSoldier(record)
  }

  useEffect(() => {
    if (linkHandled.current || soldiers.length === 0) return
    linkHandled.current = true
    const id = new URLSearchParams(window.location.search).get(RECORD_PARAM)
    const linked = id ? findRecord(soldiers, id) : undefined
    if (linked) openSoldier(linked)
  }, [soldiers])

  // The address bar follows the open record, so copying it gives that record's link
  useEffect(() => {
    if (!linkHandled.current) return
    const url = new URL(window.location.href)
    if (selectedSoldier) url.searchParams.set(RECORD_PARAM, selectedSoldier.soldier_id)
    else url.searchParams.delete(RECORD_PARAM)
    window.history.replaceState(window.history.state, '', url)
  }, [selectedSoldier])

  // Before the list has loaded, the page's own first page shows, unless the address asks for a search
  const early = loading && !searchTerm.trim() && !filtersSet

  return (
    <div>
      {/* The list starts loading with the page rather than once its scripts have run, after what the page shows */}
      {!list && <link rel="preload" href={listPath(unit)} as="fetch" crossOrigin="anonymous" fetchPriority="low" />}
      <section className="container unit-hero">
        <Link href={to('/')} className="back-link"><ArrowLeftIcon size={16} /> {t.unit.allUnits}</Link>
        <div className="unit-hero-body">
          <img {...unitImageProps(unit.image, HERO_SIZES)} alt={unitName(unit, lang)} className="unit-hero-photo" style={{ objectPosition: photoPosition(unit.id) }} />
          <div>
            <h1>{unitName(unit, lang)}</h1>
            <p className="unit-hero-desc">{unitDescription(unit, lang)}</p>
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
            <SoldierResults results={firstPage} total={total} onSelect={openSoldier} scrollTargetId="results" />
          ) : loading || (!loadFailed && pending && listed.length === 0) ? (
            <ul className="loading-rows" aria-label={loading ? t.unit.loading : t.results.searching}>
              {Array.from({ length: 8 }, (_, i) => <li key={i} />)}
            </ul>
          ) : loadFailed ? (
            <div className="empty">
              <h2>{t.unit.loadFailedTitle}</h2>
              <p>{t.unit.loadFailedText}</p>
            </div>
          ) : listed.length === 0 && filtersSet && results.length > 0 ? (
            <div className="empty">
              <h2>{t.filters.noneTitle(searchTerm.trim() ? searchTerm : '')}</h2>
              <p>
                <RichText
                  text={t.filters.noneText}
                  render={(part) => (
                    <button type="button" className="link-button" onClick={() => setFilters(NO_FILTERS)}>{part}</button>
                  )}
                />
              </p>
            </div>
          ) : listed.length === 0 ? (
            <div className="empty">
              <h2>{t.unit.noneTitle(searchTerm)}</h2>
              <p>
                <RichText text={t.unit.noneText} render={(part) => <Link href={to('/')}>{part}</Link>} />
              </p>
            </div>
          ) : (
            <SoldierResults
              results={listed}
              onSelect={openSoldier}
              scrollTargetId="results"
              actions={(searchTerm.trim() || filtersSet) && <ShareSearch />}
            />
          )}
        </div>
      </div>

      {selectedSoldier && (
        <SoldierModal
          key={selectedSoldier.soldier_id}
          soldier={selectedSoldier}
          unitName={unit.name}
          unitSoldiers={list ?? undefined}
          onOpen={openSoldier}
          onClose={() => setSelectedSoldier(null)}
        />
      )}
    </div>
  )
}
