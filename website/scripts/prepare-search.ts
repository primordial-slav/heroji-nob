import path from 'path'
import { readUnitFile } from '@/app/lib/unitFiles'
import { buildSearchData, writeSearchData } from '@/app/lib/searchData'

// Builds the search the server answers (app/lib/searchData.ts) from the data files and writes it to search-data/,
// before `next build` (package.json, "build"). Run from website/.

const started = Date.now()
const data = buildSearchData((unit) => readUnitFile(unit.dataFile))
const dir = path.join(process.cwd(), 'search-data')
writeSearchData(dir, data)
console.log(`Search data: ${data.index.size} soldiers, ${data.index.words.length} words, in ${((Date.now() - started) / 1000).toFixed(1)} s`)
