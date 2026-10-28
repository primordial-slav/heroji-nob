import fs from 'fs'
import path from 'path'
import { units } from '@/app/data/units'
import { kinPage, readSearchData, rowsPage, searchPage, type SearchData } from '@/app/lib/searchData'
import { readSearch } from '@/app/lib/searchFilters'
import { IDS_PARAM, KIN_PARAM, MOST_IDS, PAGE_SIZES, SEARCH_PAGE, UNIT_PARAM } from '@/app/lib/searchIndex'

// One page of a search over every unit's soldiers (lib/searchData.ts), asked for with the page's own address
// parameters (?q=Petrović&mesto=Gračac, searchFilters.ts) and ?strana=, ?po=, and ?u=<unit id> on a unit's page.
// With ?u=, also one record's kin (?kin=<soldier id>: kinPage) or some records' rows (?ids=<id>,<id>: rowsPage).
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
// The function runs in Frankfurt, near the site's readers: website/vercel.json ("regions"), which Vercel applies to
// every function, as it does not take this route's own preferredRegion
export const maxDuration = 30

// The search field takes 200 letters; Cyrillic written in Latin letters can be longer ("љ" is "lj")
const LONGEST_QUERY = 400

// Written by scripts/prepare-data.ts (before the build, and under `next dev` whenever a data file changes) and read
// once per instance of the function; under `next dev`, again when it has been written anew
let loaded: { mtime: number; data: SearchData } | null = null

function searchData(): SearchData {
  const dir = path.join(process.cwd(), 'search-data')
  const mtime = process.env.NODE_ENV === 'development' ? fs.statSync(path.join(dir, 'index.bin.gz')).mtimeMs : 0
  if (!loaded || loaded.mtime !== mtime) loaded = { mtime, data: readSearchData(dir) }
  return loaded.data
}

export function GET(request: Request) {
  const params = new URL(request.url).searchParams
  const { query, filters } = readSearch(params)
  if (query.length > LONGEST_QUERY) return new Response('Query too long', { status: 400 })
  const page = Math.min(Math.max(parseInt(params.get(SEARCH_PAGE.page) ?? '', 10) || 1, 1), 100000)
  const perPage = PAGE_SIZES.find((n) => String(n) === params.get(SEARCH_PAGE.perPage)) ?? PAGE_SIZES[0]
  const unitId = params.get(UNIT_PARAM)
  const unit = unitId ? units.findIndex((u) => u.id === unitId) : undefined
  if (unit === -1) return new Response('No such unit', { status: 404 })

  const kin = params.get(KIN_PARAM)
  const ids = params.get(IDS_PARAM)?.split(',').filter(Boolean)
  if ((kin !== null || ids) && unit === undefined) return new Response('No unit', { status: 400 })
  if (ids && ids.length > MOST_IDS) return new Response('Too many ids', { status: 400 })

  let data: SearchData
  try {
    data = searchData()
  } catch (error) {
    console.error('Search data could not be read', error)
    return new Response('Search is not available', { status: 503 })
  }
  const answer = kin !== null ? kinPage(data, unit!, kin)
    : ids ? rowsPage(data, unit!, ids)
    : searchPage(data, { query, filters, page, perPage, unit })
  return new Response(answer ?? 'No such record', {
    status: answer === null ? 404 : 200,
    headers: {
      'Content-Type': answer === null ? 'text/plain; charset=utf-8' : 'application/json; charset=utf-8',
      // The data change only with a deploy, which empties Vercel's cache: each search is answered once per deploy,
      // and a browser asking again within minutes keeps its own copy
      'Cache-Control': process.env.NODE_ENV === 'development' ? 'no-store' : 'public, max-age=300, s-maxage=31536000',
    },
  })
}
