'use client'

import { useEffect, useMemo, useState } from 'react'
import type { SearchFilters } from './searchFilters'
import type { SearchResultPage } from './searchIndex'
import type { Soldier } from './types'
import { searchPage } from './useServerSearch'

/** Where an open record stands in the search it was opened from */
export interface RecordWalk {
  previous?: Soldier
  next?: Soldier
  /** From 1 */
  at: number
  /** The search's own results; among the similar ones, all of them */
  total: number
}

/**
 * After a search, "Prethodni" and "Sledeći" in the record go through the search's results, not the unit's list: the next
 * man of the name is what the visitor is looking for. Undefined where the open record isn't among them (a name opened
 * from the trees, or no search), and the dialog goes through the unit's list as before. Another page of the results is
 * asked for only when the walk reaches the edge of one.
 */
export function useRecordWalk({ searching, query, filters, unit, found, soldierId }: {
  searching: boolean
  query: string
  filters: SearchFilters
  unit?: string
  found: SearchResultPage | null
  soldierId?: string
}): RecordWalk | undefined {
  const perPage = found?.perPage ?? 0
  const key = JSON.stringify([query.trim(), filters, unit, perPage])
  const [others, setOthers] = useState<{ key: string; pages: Record<number, Soldier[]> }>({ key, pages: {} })

  const pages = useMemo<Record<number, Soldier[]>>(() => ({
    ...(others.key === key ? others.pages : {}),
    ...(found ? { [found.page]: found.soldiers } : {}),
  }), [others, key, found])

  const where = useMemo(() => {
    if (!searching || !soldierId) return null
    for (const [page, soldiers] of Object.entries(pages)) {
      const index = soldiers.findIndex((s) => s.soldier_id === soldierId)
      if (index >= 0) return { page: Number(page), index, soldiers }
    }
    return null
  }, [searching, soldierId, pages])

  const count = found?.count ?? 0
  const needed = !where ? null
    : where.index === 0 && where.page > 1 ? where.page - 1
    : where.index === where.soldiers.length - 1 && where.page * perPage < count ? where.page + 1
    : null
  const missing = needed !== null && !pages[needed] ? needed : null

  useEffect(() => {
    if (missing === null) return
    let live = true
    searchPage(query, filters, unit, missing, perPage)
      .then((result) => {
        if (live) setOthers((old) => ({ key, pages: { ...(old.key === key ? old.pages : {}), [missing]: result.soldiers } }))
      })
      .catch(() => {})
    return () => { live = false }
    // the search is in the key
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [missing, key])

  if (!where || !found) return undefined
  const { page, index, soldiers } = where
  const before = pages[page - 1]
  const at = (page - 1) * perPage + index + 1
  return {
    previous: index > 0 ? soldiers[index - 1] : before?.[before.length - 1],
    next: index < soldiers.length - 1 ? soldiers[index + 1] : pages[page + 1]?.[0],
    at,
    total: found.firstNear > 0 && at <= found.firstNear ? found.firstNear : count,
  }
}
