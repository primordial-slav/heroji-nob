import path from 'path'
import { units } from '@/app/data/units'
import { buildSearchData, readSearchData, searchPage, type SearchData } from '@/app/lib/searchData'
import { readSearch } from '@/app/lib/searchFilters'
import { PAGE_SIZES, SEARCH_PAGE, UNIT_PARAM } from '@/app/lib/searchIndex'
import { readUnitFile } from '@/app/lib/unitFiles'
import type { Soldier } from '@/app/lib/types'

// One page of a search over every unit's soldiers (lib/searchData.ts), asked for with the page's own address
// parameters (?q=Petrović&mesto=Gračac, searchFilters.ts) and ?strana=, ?po=, and ?u=<unit id> on a unit's page
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
// The function runs in Frankfurt, near the site's readers: website/vercel.json ("regions"), which Vercel applies to
// every function, as it does not take this route's own preferredRegion
export const maxDuration = 30

// The search field takes 200 letters; Cyrillic written in Latin letters can be longer ("љ" is "lj")
const LONGEST_QUERY = 400

// Read once per instance of the function; under `next dev`, built from the data files, again when one changes
let loaded: SearchData | null = null
let built: { files: Soldier[][]; data: SearchData } | null = null

function searchData(): SearchData {
  if (process.env.NODE_ENV === 'development') {
    const files = units.map((unit) => readUnitFile(unit.dataFile))
    if (!built || built.files.some((file, u) => file !== files[u])) {
      built = { files, data: buildSearchData((unit) => files[units.indexOf(unit)]) }
    }
    return built.data
  }
  return (loaded ??= readSearchData(path.join(process.cwd(), 'search-data')))
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

  let data: SearchData
  try {
    data = searchData()
  } catch (error) {
    console.error('Search data could not be read', error)
    return new Response('Search is not available', { status: 503 })
  }
  return new Response(searchPage(data, { query, filters, page, perPage, unit }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      // The data change only with a deploy, which empties Vercel's cache: each search is answered once per deploy,
      // and a browser asking again within minutes keeps its own copy
      'Cache-Control': process.env.NODE_ENV === 'development' ? 'no-store' : 'public, max-age=300, s-maxage=31536000',
    },
  })
}
