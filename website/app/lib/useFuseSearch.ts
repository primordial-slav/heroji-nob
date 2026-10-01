'use client'

import { useState, useEffect, useRef } from 'react'
import { normalizeForSearch } from './diacritics'
import { createSoldierIndex, mergeHits, searchFields, searchSoldiers, type SoldierIndex } from './soldierSearch'
import type { FromSearchWorker, ToSearchWorker } from './search.worker'
import type { Soldier } from './types'

// Searching every unit's soldiers takes a second or more, which held up typing while it ran. So the search runs
// in workers, each on a slice of the list, all at once; their hits are merged into the order a search of the
// whole list gives (soldierSearch.ts).

const MAX_WORKERS = 4
// Fewer soldiers than this per worker would cost more in starting it than it saves
const MIN_SLICE = 10000
// Soldiers per message: copying many more to a worker at once would hold up the page
const PIECE = 5000

class SearchPool {
  private slices: { worker: Worker; start: number; size: number }[] = []
  private ready: Promise<void>
  private failed = false
  private closed = false
  // Without workers, the search runs on the page's thread, as it did before them
  private local: SoldierIndex | null = null
  private busy = false
  private waiting: { query: string; wholeWords: boolean; resolve: (found: Int32Array | null) => void } | null = null

  constructor(private data: Soldier[]) {
    const cores = navigator.hardwareConcurrency || 2
    const count = Math.max(1, Math.min(MAX_WORKERS, cores - 1, Math.floor(data.length / MIN_SLICE)))
    const size = Math.ceil(data.length / count)
    try {
      for (let start = 0; start < data.length; start += size) {
        const worker = new Worker(new URL('./search.worker.ts', import.meta.url))
        worker.onerror = () => { this.failed = true }
        this.slices.push({ worker, start, size: Math.min(size, data.length - start) })
      }
    } catch {
      this.failed = true
    }
    this.ready = this.handOver()
  }

  /** Gives each worker its slice, a piece at a time, letting the page run in between */
  private async handOver() {
    for (const slice of this.slices) {
      for (let at = 0; at < slice.size; at += PIECE) {
        if (this.closed || this.failed) return
        const end = Math.min(at + PIECE, slice.size)
        const message: ToSearchWorker = {
          type: 'data',
          soldiers: this.data.slice(slice.start + at, slice.start + end).map(searchFields),
          last: end === slice.size,
        }
        slice.worker.postMessage(message)
        await new Promise((resolve) => setTimeout(resolve))
      }
    }
  }

  /**
   * Positions in `data` of the soldiers found, best first. One search runs at a time; a search asked for while
   * another runs waits, and gets null if a newer one takes its place before it starts.
   */
  search(query: string, wholeWords: boolean): Promise<Int32Array | null> {
    this.waiting?.resolve(null)
    return new Promise((resolve) => {
      this.waiting = { query, wholeWords, resolve }
      this.next()
    })
  }

  private async next() {
    if (this.busy || this.closed || !this.waiting) return
    const { query, wholeWords, resolve } = this.waiting
    this.waiting = null
    this.busy = true
    try {
      resolve(await this.run(query, wholeWords))
    } catch {
      resolve(new Int32Array(0))
    } finally {
      this.busy = false
      this.next()
    }
  }

  private async run(query: string, wholeWords: boolean): Promise<Int32Array> {
    await this.ready
    if (!this.failed) {
      try {
        const message: ToSearchWorker = { type: 'search', query, wholeWords }
        const hits = await Promise.all(this.slices.map((slice) => this.ask(slice.worker, message)))
        return mergeHits(hits.map((h, i) => ({ hits: h, start: this.slices[i].start })))
      } catch {
        this.failed = true
      }
    }
    this.terminate()
    if (!this.local) {
      console.warn('Search workers did not start; searching on the page, which holds up typing')
      this.local = createSoldierIndex(this.data.map(searchFields))
    }
    return mergeHits([{ hits: searchSoldiers(this.local, query, wholeWords), start: 0 }])
  }

  private ask(worker: Worker, message: ToSearchWorker): Promise<FromSearchWorker> {
    return new Promise((resolve, reject) => {
      worker.onmessage = (event: MessageEvent<FromSearchWorker>) => resolve(event.data)
      worker.onerror = (error) => reject(error)
      worker.postMessage(message)
    })
  }

  private terminate() {
    this.slices.forEach((slice) => slice.worker.terminate())
    this.slices = []
  }

  close() {
    this.closed = true
    this.terminate()
  }
}

// A list's workers stay for the rest of the visit (the lists themselves do, searchIndex.ts), so going back to a
// page searches at once instead of handing the list over and indexing it again. Only the three lists used last
// keep theirs, as each worker holds its slice's index.
const KEPT_POOLS = 3
const pools = new Map<Soldier[], SearchPool>()

function poolFor(data: Soldier[]): SearchPool {
  const pool = pools.get(data) ?? new SearchPool(data)
  // Last used last
  pools.delete(data)
  pools.set(data, pool)
  for (const [list, old] of pools) {
    if (pools.size <= KEPT_POOLS) break
    pools.delete(list)
    old.close()
  }
  return pool
}

const NO_SOLDIERS: Soldier[] = []
const DEBOUNCE_MS = 250

/** Which search a list of results is for: the same for spellings that search alike ("Rolić", "rolic ") */
const searchKey = (term: string, wholeWords: boolean) => `${wholeWords ? 1 : 0}${normalizeForSearch(term.trim())}`

interface UseFuseSearchOptions {
  /** When true, an empty query returns all data. When false, returns empty array. */
  showAllOnEmpty: boolean
  /** Only soldiers whose name or bio has every query word as a whole word */
  wholeWords?: boolean
}

interface UseFuseSearchReturn {
  results: Soldier[]
  searchTerm: string
  setSearchTerm: (term: string) => void
  isSearching: boolean
  /**
   * The results are not yet those of the term typed: the last search's stay until its are in. True from the
   * render in which the term or the list changes; the results of a list the hook had before are not kept.
   */
  pending: boolean
}

export function useFuseSearch(
  data: Soldier[],
  options: UseFuseSearchOptions
): UseFuseSearchReturn {
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedTerm, setDebouncedTerm] = useState('')
  // The last search's results, with the term and the list they are for
  const [found, setFound] = useState({ key: '', data: NO_SOLDIERS, results: NO_SOLDIERS })
  const poolRef = useRef<SearchPool | null>(null)
  const wholeWords = !!options.wholeWords

  // Hand the data to the search workers when it changes, or take up the workers it already has
  useEffect(() => {
    if (data.length === 0) return
    poolRef.current = poolFor(data)
    return () => {
      poolRef.current = null
    }
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
    if (!debouncedTerm.trim()) return
    const pool = poolRef.current
    if (!pool) return
    let current = true
    const key = searchKey(debouncedTerm, wholeWords)
    pool.search(normalizeForSearch(debouncedTerm.trim()), wholeWords).then((positions) => {
      if (current && positions) setFound({ key, data, results: Array.from(positions, (i) => data[i]) })
    })
    return () => { current = false }
  }, [debouncedTerm, data, wholeWords])

  // An empty term lists everyone (or no one), and those results stay while the next search runs. Only when the
  // term typed is empty too: a term from the address is set before the list arrives, while the debounced term is
  // still empty, and its search would otherwise show the whole list first
  useEffect(() => {
    if (searchTerm.trim() || debouncedTerm.trim()) return
    setFound({ key: '', data, results: options.showAllOnEmpty ? data : NO_SOLDIERS })
  }, [searchTerm, debouncedTerm, data, options.showAllOnEmpty])

  // Worked out in the render, not by the effects above, which run only after a render of the old results: the
  // render in which a list arrives would show an empty result ("Nema boraca za „“") before the list
  const isSearching = searchTerm.trim().length > 0
  const ofThisList = found.data === data
  const pending = isSearching && !(ofThisList && found.key === searchKey(searchTerm, wholeWords))
  const results = !isSearching
    ? (options.showAllOnEmpty ? data : NO_SOLDIERS)
    : ofThisList ? found.results : NO_SOLDIERS

  return { results, searchTerm, setSearchTerm, isSearching, pending }
}
