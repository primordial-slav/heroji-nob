'use client'

import { useState, useEffect, useRef } from 'react'
import Fuse, { IFuseOptions, FuseResult } from 'fuse.js'
import { normalizeForSearch } from './diacritics'
import type { Soldier } from './types'

// Custom getFn that normalizes diacritics (and dj → d) during indexing
function normalizingGetFn(
  obj: Record<string, unknown>,
  path: string | string[]
): string | string[] {
  const value = Fuse.config.getFn(obj, path)
  if (Array.isArray(value)) {
    return value.map((v) => normalizeForSearch(String(v)))
  }
  if (typeof value === 'string') {
    return normalizeForSearch(value)
  }
  return value != null ? String(value) : ''
}

// full_name puts the father's name between surname and first name ("Kokalj Anrejev Rudolf"),
// so "Kokalj Rudolf" or "Rudolf Kokalj" would miss it. Index both two-name orders as well.
function nameVariants(soldier: Soldier): string[] {
  const last = soldier.last_name?.trim()
  const first = soldier.first_name?.trim()
  if (!last || !first) return []
  return [`${last} ${first}`, `${first} ${last}`].map(normalizeForSearch)
}

const FUSE_OPTIONS: IFuseOptions<Soldier> = {
  keys: [
    { name: 'full_name', weight: 0.6 },
    { name: 'name_variants', weight: 0.6, getFn: nameVariants },
    { name: 'additional_info', weight: 0.2 },
    { name: 'birth_year', weight: 0.1 },
    { name: 'unit', weight: 0.1 },
  ],
  threshold: 0.35,
  ignoreLocation: true,
  includeScore: true,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getFn: normalizingGetFn as any,
  fieldNormWeight: 1,
}

const DEBOUNCE_MS = 250

interface UseFuseSearchOptions {
  /** When true, an empty query returns all data. When false, returns empty array. */
  showAllOnEmpty: boolean
}

interface UseFuseSearchReturn {
  results: Soldier[]
  searchTerm: string
  setSearchTerm: (term: string) => void
  isSearching: boolean
}

export function useFuseSearch(
  data: Soldier[],
  options: UseFuseSearchOptions
): UseFuseSearchReturn {
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedTerm, setDebouncedTerm] = useState('')
  const [results, setResults] = useState<Soldier[]>([])
  const fuseRef = useRef<Fuse<Soldier> | null>(null)

  // Build Fuse index when data changes
  useEffect(() => {
    if (data.length === 0) {
      fuseRef.current = null
      return
    }
    fuseRef.current = new Fuse(data, FUSE_OPTIONS)
  }, [data])

  // Debounce the search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedTerm(searchTerm)
    }, DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // Execute search when debounced term changes
  useEffect(() => {
    if (!debouncedTerm.trim()) {
      setResults(options.showAllOnEmpty ? data : [])
      return
    }

    if (!fuseRef.current) {
      setResults([])
      return
    }

    const normalizedQuery = normalizeForSearch(debouncedTerm.trim())
    const fuseResults: FuseResult<Soldier>[] =
      fuseRef.current.search(normalizedQuery)
    setResults(fuseResults.map((r) => r.item))
  }, [debouncedTerm, data, options.showAllOnEmpty])

  const isSearching = searchTerm.trim().length > 0

  return { results, searchTerm, setSearchTerm, isSearching }
}
