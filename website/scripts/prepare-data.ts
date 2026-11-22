import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { units, type Unit } from '@/app/data/units'
import portraitIndex from '@/app/data/portrait-index.json'
import { WARTIME_PORTRAITS } from '@/app/data/wartimePortraits'
import {
  DATA_DIR, PORTRAIT_PEOPLE_PATH, RECORDS_PER_PART, onThisDayPath, placesChunkPath, placesOfPath, recordsPath, wherePath,
} from '@/app/lib/dataFiles'
import type { WhereShard } from '@/app/lib/recordAddress'
import { wartimeDeath } from '@/app/lib/deathDay'
import { GENERATED_DIR, PAGES_FILE, type GeneratedPages } from '@/app/lib/generated'
import { PLACES_FILE, VEZ_FILE, placeSplit } from '@/app/lib/placeFiles'
import { PLACE_CHUNK_BYTES } from '@/app/lib/relations'
import { buildSearchData, writeSearchData } from '@/app/lib/searchData'
import { dayKey, eachListedOnce, encodeKinRow, encodeRow, listOnce, type PlacedRow } from '@/app/lib/searchIndex'
import type { LifeEvent, Soldier, WarEvent } from '@/app/lib/types'
import type { GalleryItem } from '@/app/views/GalleryClient'
import porekloBooks from './poreklo-books.json'

// Writes, from the unit files, what the site's pages load as data (lib/dataFiles.ts) to public/data/, the search the
// server answers to search-data/ (lib/searchData.ts), and what the pages read while they are built to generated/
// (lib/generated.ts): before `next build` (package.json, "build"), and under `next dev` whenever a data file changes
// (lib/devData.ts), so the dev server reads small files instead of every unit's data. Only what changed is written
// again: a unit's records when its data file or life events change; "Na današnji dan", the portraits' soldiers, the
// gallery and the search when any unit changes, or this script; the places when places.json or vez-sets.json does.
// Run from website/; --force writes everything.

const started = Date.now()
const root = process.cwd()
const force = process.argv.includes('--force')
const MANIFEST = path.join(root, GENERATED_DIR, 'manifest.json')
const LOCK = path.join(root, GENERATED_DIR, 'prepare-data.lock')
const SEARCH_DIR = path.join(root, 'search-data')
// The form of the records' and places' files: a change to it writes them all again (3: the Poreklo library's addresses
// replaced by their books' keys)
const RECORDS_FORM = `${RECORDS_PER_PART}:3`
const PLACES_FORM = `${PLACE_CHUNK_BYTES}:1`

interface Manifest {
  /** Each input file's size and time, and its contents' hash, so a file written again unchanged changes nothing */
  files: Record<string, { stamp: string; hash: string }>
  /** What each output was written from */
  records: Record<string, string>
  globals?: string
  places?: string
}

const sha1 = (...parts: (string | Buffer)[]) => {
  const hash = crypto.createHash('sha1')
  for (const part of parts) hash.update(part)
  return hash.digest('hex')
}

const publicFile = (urlPath: string) => path.join(root, 'public', ...urlPath.split('/').filter(Boolean))

function writeJson(file: string, value: unknown) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value))
}

// ── One run at a time in a checkout: a second waits for the first ──

function alive(pid: number): boolean {
  try {
    process.kill(pid, 0)
    return true
  } catch {
    return false
  }
}

async function takeLock() {
  fs.mkdirSync(path.dirname(LOCK), { recursive: true })
  for (let waited = 0; ; waited += 2) {
    try {
      fs.writeFileSync(LOCK, String(process.pid), { flag: 'wx' })
      return
    } catch {
      const holder = Number(fs.readFileSync(LOCK, 'utf8'))
      if (!holder || !alive(holder)) {
        fs.rmSync(LOCK, { force: true })
        continue
      }
      if (waited === 0) console.log(`Data: waiting for another run (process ${holder})`)
      if (waited > 1800) throw new Error(`Data: process ${holder} has held ${LOCK} for half an hour`)
      await new Promise((resolve) => setTimeout(resolve, 2000))
    }
  }
}

// ── What changed ──

function readManifest(): Manifest {
  try {
    return JSON.parse(fs.readFileSync(MANIFEST, 'utf8'))
  } catch {
    return { files: {}, records: {} }
  }
}

/** A file's contents' hash ('' if there is no such file), read only when its size or time has changed */
function fileHash(manifest: Manifest, seen: Manifest['files'], relative: string): string {
  const file = path.join(root, relative)
  if (!fs.existsSync(file)) return ''
  const stat = fs.statSync(file)
  const stamp = `${stat.size}:${stat.mtimeMs}`
  const known = manifest.files[relative]
  const hash = known && known.stamp === stamp ? known.hash : sha1(fs.readFileSync(file))
  seen[relative] = { stamp, hash }
  return hash
}

const unitFile = (unit: Unit) => path.join('public', unit.dataFile)
// the men Borci drugih jedinica gave to their units (data-extraction/build_ostali_borci.py, 2026-11-20), and the census
// records that left their part for another record (2026-11-22): their old id -> their record's id, so an old link still
// finds him; read with the shards of the part that had the old id (writeWhere)
const OSTALI_UNIT = 'ostali-borci'
const isOstali = (unit: Unit) => unit.id === OSTALI_UNIT || unit.id.startsWith(`${OSTALI_UNIT}-`)
const MOVED_FILE = path.join('data', 'moved-ids.json')
const movedIds = (): Record<string, string> =>
  fs.existsSync(path.join(root, MOVED_FILE)) ? JSON.parse(fs.readFileSync(path.join(root, MOVED_FILE), 'utf8')) : {}
const eventsFile = (unit: Unit) => path.join('data', 'life-events', unit.dataFile)
// the war's events his unit was part of (scripts/make_igman_list.py), for the units that have them
const warEventsFile = (unit: Unit) => path.join('data', 'events', unit.dataFile)
const partsOf = (count: number) => Math.ceil(count / RECORDS_PER_PART)

// The Poreklo library's books are named on the site and never linked, and their addresses are not published at all
// (the user, 2026-11-19): an entry's source_url in the library becomes its book's key, "poreklo:<source id>", which
// data/sources.ts lists (lib/recordSources.ts finds the book by it). The addresses are in scripts/poreklo-books.json,
// which only this script reads; the longest first, so a book is never taken for one whose address is a prefix of its.
const LIBRARY = 'https://biblioteka.poreklo.rs/'
const POREKLO_BOOKS = [...porekloBooks].sort((a, b) => b.url.length - a.url.length)
let unknownLibraryPages = 0

function hideLibrary(value: unknown): void {
  if (Array.isArray(value)) {
    value.forEach(hideLibrary)
  } else if (value && typeof value === 'object') {
    const entry = value as Record<string, unknown>
    for (const key of Object.keys(entry)) {
      const field = entry[key]
      if (key === 'source_url' && typeof field === 'string' && field.startsWith(LIBRARY)) {
        const book = POREKLO_BOOKS.find((b) => field.startsWith(b.url))
        if (!book) unknownLibraryPages++
        entry[key] = book ? `poreklo:${book.id}` : 'poreklo:'
      } else if (field && typeof field === 'object') {
        hideLibrary(field)
      }
    }
  }
}

function readUnit(unit: Unit): Soldier[] {
  const soldiers: Soldier[] = JSON.parse(fs.readFileSync(path.join(root, unitFile(unit)), 'utf8'))
  hideLibrary(soldiers)
  return soldiers
}

// ── The outputs ──

// Where each of a unit's records is, for its own address (lib/recordAddress.ts): its own id, and an id merged into it,
// which old links may still use
function writeWhere(unit: Unit, soldiers: Soldier[]) {
  const shards = new Map<string, WhereShard>()
  const put = (id: string, at: number | [number, string]) => {
    const key = id.slice(0, 7)
    let shard = shards.get(key)
    if (!shard) shards.set(key, (shard = { u: unit.id, p: {} }))
    if (shard.p[id.slice(7)] === undefined) shard.p[id.slice(7)] = at
  }
  soldiers.forEach((s, i) => put(s.soldier_id, Math.floor(i / RECORDS_PER_PART)))
  soldiers.forEach((s, i) => {
    for (const o of s.other_sources ?? []) {
      if (o.soldier_id && !o.unit_file && !o.ref_book && o.soldier_id.slice(0, 4) === s.soldier_id.slice(0, 4)) {
        put(o.soldier_id, [Math.floor(i / RECORDS_PER_PART), s.soldier_id])
      }
    }
  })
  // a man of Borci drugih jedinica or of a census part now on another record (his unit's, or one of 122 his entry
  // joined): his old id gives the new one, in the where-files of the part that had it (the address answers only with
  // it, a 308, so no slice of the other unit is named here)
  const codes = new Set(soldiers.map((s) => s.soldier_id.slice(0, 4)))
  if (isOstali(unit)) for (const [old, now] of Object.entries(movedIds())) if (codes.has(old.slice(0, 4))) put(old, [0, now])
  // a thousand ids of which none is left leave no file behind
  const dir = path.dirname(publicFile(wherePath('0000000')))
  fs.mkdirSync(dir, { recursive: true })
  for (const name of fs.readdirSync(dir)) {
    if (codes.has(name.slice(0, 4)) && !shards.has(name.slice(0, 7))) fs.rmSync(path.join(dir, name))
  }
  for (const [key, shard] of shards) writeJson(publicFile(wherePath(key)), shard)
}

function writeRecords(unit: Unit, soldiers: Soldier[]) {
  const file = path.join(root, eventsFile(unit))
  const events: Record<string, LifeEvent[]> = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {}
  const warFile = path.join(root, warEventsFile(unit))
  const war: Record<string, WarEvent[]> = fs.existsSync(warFile) ? JSON.parse(fs.readFileSync(warFile, 'utf8')) : {}
  const parts = partsOf(soldiers.length)
  for (let part = 0; part < parts; part++) {
    const records = soldiers.slice(part * RECORDS_PER_PART, (part + 1) * RECORDS_PER_PART)
    writeJson(publicFile(recordsPath(unit.id, part)), records.map((r) => ({
      ...r,
      ...(events[r.soldier_id] ? { life_events: events[r.soldier_id] } : {}),
      ...(war[r.soldier_id] ? { events: war[r.soldier_id] } : {}),
    })))
  }
  // a list grown shorter leaves no parts behind
  const dir = path.dirname(publicFile(recordsPath(unit.id, 0)))
  for (const name of fs.readdirSync(dir)) {
    const part = parseInt(name, 10)
    if (!(part < parts)) fs.rmSync(path.join(dir, name))
  }
  writeWhere(unit, soldiers)
}

const DAYS_IN_MONTH = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

// "Na današnji dan": those who fell, died or went missing on each day of the year during the war, each soldier
// once, as the home page lists them (listOnce)
function writeOnThisDay(files: Soldier[][]) {
  const where = new Map<string, { unit: string; position: number }>()
  const lists = units.map((unit, u) => files[u].map((soldier, position) => {
    where.set(soldier.soldier_id, { unit: unit.id, position })
    return { ...soldier, unit: unit.name }
  }))
  const days = new Map<string, PlacedRow[]>()
  for (const soldier of listOnce(lists)) {
    const death = wartimeDeath(soldier)
    if (!death) continue
    const entry: PlacedRow = { ...where.get(soldier.soldier_id)!, row: encodeRow(soldier) }
    if (soldier.also_units) entry.also = soldier.also_units
    const key = dayKey(death.month, death.day)
    const day = days.get(key)
    if (day) day.push(entry)
    else days.set(key, [entry])
  }
  DAYS_IN_MONTH.forEach((count, m) => {
    for (let d = 1; d <= count; d++) {
      const key = dayKey(m + 1, d)
      writeJson(publicFile(onThisDayPath(key)), days.get(key) ?? [])
    }
  })
}

// The soldiers whose portraits drift up the home page's margins (components/PortraitRails.tsx), as the home page
// lists them, so the faces get their names without the page loading every soldier: without their entries' text
// (encodeKinRow), which the margins don't show and a click loads with the full record
function writePortraitPeople(files: Soldier[][]) {
  const lists = units.map((unit, u) => files[u].map((soldier) => ({ ...soldier, unit: unit.name })))
  const starts = lists.reduce<number[]>((at, list) => [...at, at[at.length - 1] + list.length], [0])
  const listed: { soldier: Soldier; also: string[]; at: number }[] = []
  eachListedOnce(lists, (soldier, also, at) => listed.push({ soldier, also, at }))

  // As PortraitRails finds them: a portrait is filed under the soldier's own id, or under one his entry had before
  const byId = new Map<string, number>()
  listed.forEach(({ soldier }, k) => {
    byId.set(soldier.soldier_id, k)
    for (const o of soldier.other_sources ?? []) if (o.soldier_id && !byId.has(o.soldier_id)) byId.set(o.soldier_id, k)
  })
  // In the order of the list, so the page's own lookup among them finds each as it would among everyone
  const wanted = [...new Set(WARTIME_PORTRAITS.map((id) => byId.get(id)).filter((k): k is number => k !== undefined))]
    .sort((a, b) => a - b)
  writeJson(publicFile(PORTRAIT_PEOPLE_PATH), wanted.map((k) => {
    const { soldier, also, at } = listed[k]
    const u = starts.findIndex((start, i) => at >= start && at < starts[i + 1])
    const entry: PlacedRow = { unit: units[u].id, position: at - starts[u], row: encodeKinRow(soldier) }
    if (also.length) entry.also = also
    return entry
  }))
}

// What the pages read while they are built: each unit's count and its list's first records (views/unitPage.tsx), and
// the Galerija's portraits, each knowing which slice of its unit's records holds the soldier (views/GalleryPage.tsx).
// A man with a portrait under several records (one in each unit or book that prints him) is shown once, by the record
// `same` names.
function writePages(files: Soldier[][]) {
  const portraits = portraitIndex as Record<string, { f: string; same?: string }>
  const gallery: GalleryItem[] = []
  units.forEach((unit, u) => files[u].forEach((s, i) => {
    const portrait = portraits[s.soldier_id]
    if (portrait && !portrait.same) {
      gallery.push({ id: s.soldier_id, name: s.full_name, unit: unit.id, part: Math.floor(i / RECORDS_PER_PART), file: portrait.f })
    }
  }))
  const pages: GeneratedPages = { counts: Object.fromEntries(units.map((unit, u) => [unit.id, files[u].length])), gallery }
  writeJson(path.join(root, PAGES_FILE), pages)
}

// The search, written beside the one the server reads and put in its place at once, so a dev server never reads
// half of it
function writeSearch(files: Soldier[][]) {
  const data = buildSearchData((unit) => files[units.indexOf(unit)])
  const fresh = `${SEARCH_DIR}-new`
  const old = `${SEARCH_DIR}-old`
  fs.rmSync(fresh, { recursive: true, force: true })
  fs.rmSync(old, { recursive: true, force: true })
  writeSearchData(fresh, data)
  if (fs.existsSync(SEARCH_DIR)) fs.renameSync(SEARCH_DIR, old)
  fs.renameSync(fresh, SEARCH_DIR)
  fs.rmSync(old, { recursive: true, force: true })
  return data.index.size
}

function writePlaces() {
  const { chunks, where, vez } = placeSplit()
  const dir = path.dirname(path.dirname(publicFile(placesOfPath('x'))))
  fs.rmSync(dir, { recursive: true, force: true })
  chunks.forEach((chunk, n) => writeJson(publicFile(placesChunkPath(n)), chunk))
  for (const shard of new Set([...where.keys(), ...vez.keys()])) {
    writeJson(publicFile(placesOfPath(shard)), { w: where.get(shard) ?? {}, v: vez.get(shard) ?? {} })
  }
  return chunks.length
}

// ── The run ──

async function main() {
  await takeLock()
  try {
    const manifest = readManifest()
    const seen: Manifest['files'] = {}
    const unitHash = (unit: Unit) => {
      const war = fileHash(manifest, seen, warEventsFile(unit))
      const moved = isOstali(unit) ? fileHash(manifest, seen, MOVED_FILE) : ''
      return sha1(fileHash(manifest, seen, unitFile(unit)), ':', fileHash(manifest, seen, eventsFile(unit)), ...(war ? [':', war] : []),
        ...(moved ? [':', moved] : []))
    }
    const hashes = new Map(units.map((unit) => [unit.id, unitHash(unit)]))
    const recordsKey = (unit: Unit) => `${hashes.get(unit.id)}:${RECORDS_FORM}`
    // this script's own code (its bundle), with the libraries and data modules it carries, writes the globals
    const code = sha1(fs.readFileSync(process.argv[1]))
    const globalsKey = sha1(code, ...units.map((unit) => `${unit.id}:${hashes.get(unit.id)}`))
    const placesKey = sha1(PLACES_FORM, fileHash(manifest, seen, PLACES_FILE), fileHash(manifest, seen, VEZ_FILE))
    const exists = (file: string) => fs.existsSync(file)

    const counts = (() => {
      try {
        return (JSON.parse(fs.readFileSync(path.join(root, PAGES_FILE), 'utf8')) as GeneratedPages).counts
      } catch {
        return {} as Record<string, number>
      }
    })()
    const staleRecords = units.filter((unit) => force || manifest.records[unit.id] !== recordsKey(unit)
      || counts[unit.id] === undefined || !exists(publicFile(recordsPath(unit.id, Math.max(partsOf(counts[unit.id]) - 1, 0)))))
    const staleGlobals = force || manifest.globals !== globalsKey || !exists(path.join(SEARCH_DIR, 'index.bin.gz'))
      || !exists(path.join(root, PAGES_FILE)) || !exists(publicFile(PORTRAIT_PEOPLE_PATH)) || !exists(publicFile(onThisDayPath('12-31')))
    const stalePlaces = force || manifest.places !== placesKey || !exists(path.dirname(publicFile(placesChunkPath(0))))

    const done: string[] = []
    if (staleRecords.length || staleGlobals) {
      // every unit's list only for what is made of all of them
      const files = staleGlobals ? units.map(readUnit) : null
      for (const unit of staleRecords) writeRecords(unit, files ? files[units.indexOf(unit)] : readUnit(unit))
      if (staleRecords.length) done.push(`records of ${staleRecords.length} units`)
      // the records of units no longer on the site go
      const recordsDir = path.dirname(path.dirname(publicFile(recordsPath('x', 0))))
      for (const name of fs.existsSync(recordsDir) ? fs.readdirSync(recordsDir) : []) {
        if (!units.some((unit) => unit.id === name)) fs.rmSync(path.join(recordsDir, name), { recursive: true })
      }
      if (files) {
        writeOnThisDay(files)
        writePortraitPeople(files)
        writePages(files)
        done.push(`on this day, the portraits' soldiers, the gallery, the search (${writeSearch(files)} soldiers)`)
      }
    }
    if (stalePlaces) done.push(`places (${writePlaces()} chunks)`)

    const next: Manifest = {
      files: seen,
      records: Object.fromEntries(units.map((unit) => [unit.id, recordsKey(unit)])),
      globals: globalsKey,
      places: placesKey,
    }
    fs.mkdirSync(path.dirname(MANIFEST), { recursive: true })
    fs.writeFileSync(MANIFEST, JSON.stringify(next))
    // a page of the library whose book data/sources.ts doesn't list: published as "poreklo:", named as no book
    if (unknownLibraryPages) console.warn(`Poreklo library pages of no listed book: ${unknownLibraryPages} (add the book to data/sources.ts and scripts/poreklo-books.json)`)
    const seconds = ((Date.now() - started) / 1000).toFixed(1)
    console.log(done.length ? `Data (public/${DATA_DIR}): ${done.join('; ')}, in ${seconds} s` : `Data (public/${DATA_DIR}): up to date`)
  } finally {
    fs.rmSync(LOCK, { force: true })
  }
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
