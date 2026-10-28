'use client'

import { useEffect, useState } from 'react'
import { normalizeForSearch } from './diacritics'
import { narrows, writeSearch, type SearchFilters } from './searchFilters'
import { PAGE_SIZES, SEARCH_PAGE, UNIT_PARAM, searchOnServer, type SearchResultPage } from './searchIndex'

// A search the server answers (app/api/search/route.ts), a page at a time, so the page loads no soldiers but those
// it shows. A search (the words typed and the filters) is asked for once typing pauses, another page of it at once;
// the last results stay until the new ones are in.

const DEBOUNCE_MS = 250
// A request that fails is asked for once more before the search is given up as failed
const RETRY_MS = 1000

/**
 * A search's parameters for the server, without the page, or null when there is nothing to search for. Spellings
 * that search alike ("Petrović", "petrovic ") ask the same, so Vercel's cache answers them alike.
 */
function searchParams(query: string, filters: SearchFilters, unit?: string): string | null {
  const typed = normalizeForSearch(query.trim()).toLowerCase().replace(/\s+/g, ' ')
  if (!typed && !unit && !narrows(filters)) return null
  const url = new URL('https://search.invalid/')
  writeSearch(url, typed, filters, !unit)
  if (unit) url.searchParams.set(UNIT_PARAM, unit)
  url.searchParams.sort()
  return url.searchParams.toString()
}

function withPage(search: string, page: number, perPage: number): string {
  const params = new URLSearchParams(search)
  if (page > 1) params.set(SEARCH_PAGE.page, String(page))
  if (perPage !== PAGE_SIZES[0]) params.set(SEARCH_PAGE.perPage, String(perPage))
  return params.toString()
}

interface ServerSearchOptions {
  query: string
  filters: SearchFilters
  /** From 1 */
  page: number
  perPage: number
  /** A unit's id: only its soldiers are searched, and with no words typed, all of them are listed */
  unit?: string
  /** False: nothing is asked for (the page shows what it has already) */
  enabled?: boolean
}

interface ServerSearch {
  /** The page of results last in: the search typed, or while its results are on their way, the one before */
  result: SearchResultPage | null
  /** The results shown are not yet those of what is typed now */
  pending: boolean
  /** The server did not answer the search typed, twice */
  failed: boolean
}

export function useServerSearch({ query, filters, page, perPage, unit, enabled = true }: ServerSearchOptions): ServerSearch {
  const search = searchParams(query, filters, unit)
  const [settled, setSettled] = useState(search)
  useEffect(() => {
    const timer = setTimeout(() => setSettled(search), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [search])

  const wanted = search === null ? null : withPage(search, page, perPage)
  // Nothing is asked for while the search is still being typed
  const asked = settled === search ? wanted : null
  const [found, setFound] = useState<{ key: string; result: SearchResultPage } | null>(null)
  const [failed, setFailed] = useState<string | null>(null)

  useEffect(() => {
    if (!enabled || asked === null) return
    const controller = new AbortController()
    const ask = (retry: boolean) => searchOnServer(new URLSearchParams(asked), controller.signal)
      .then((result) => setFound({ key: asked, result }))
      .catch(() => {
        if (controller.signal.aborted) return
        if (retry) setTimeout(() => !controller.signal.aborted && ask(false), RETRY_MS)
        else setFailed(asked)
      })
    ask(true)
    return () => controller.abort()
  }, [asked, enabled])

  return {
    result: wanted === null ? null : found?.result ?? null,
    pending: wanted !== null && found?.key !== wanted,
    failed: wanted !== null && failed === wanted,
  }
}
