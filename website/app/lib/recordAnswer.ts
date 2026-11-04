import type { NextRequest } from 'next/server'
import { units, type Unit } from '@/app/data/units'
import { portraitFor } from '@/app/data/portraits'
import { messagesFor } from '@/app/i18n'
import { FINISHED_LANGS, HTML_LANG, OG_LOCALE, localePath, type Lang } from '@/app/i18n/config'
import { unitName } from '@/app/i18n/units'
import { recordsPath, wherePath } from './dataFiles'
import { isRecordId, placeIn, type WhereShard } from './recordAddress'
import { recordFacts } from './recordFacts'
import { sourceOf } from './recordSources'
import { RECORD_PARAM, decorationsOf, entriesOf, recordPath } from './records'
import type { Soldier } from './types'

// The answer to a record's own address, /borac/<id>. There are half a million of them, so none is built with the site.
// This puts the record's name and text into one prerendered page (app/(sr)/borac/page.tsx), so a shared link's preview
// and a reader without scripts have them, and the page then opens the record as any other does. To stay cheap at any
// number of visitors or crawlers it renders nothing: three small static files, read from the site's own CDN, and a few
// string replacements, and the CDN keeps each answer until the next deploy, so an address runs this once per deploy.
// It must never wake the search's data or render a book's page. If anything fails, it sends the reader to the record's
// older address, a page that needs none of this.

/** The record's slot in that page (views/RecordPage.tsx) */
const SLOT = /<div id="record-plain"[^>]*><\/div>/
const LANGUAGE_LINK = /(href="(?:\/(?:sr-cyrl|sl|mk|en))?\/borac)"/g

const DEV = process.env.NODE_ENV === 'development'
const KEPT = DEV ? 'no-store' : 'public, max-age=300, s-maxage=31536000'
const KEPT_MISSING = DEV ? 'no-store' : 'public, max-age=300, s-maxage=86400'
const LONGEST_DESCRIPTION = 300

// Not for search engines yet: names are found from Google only when that is decided (public/robots.txt keeps the
// polite ones away, and this the rest out of the results)
const NOT_INDEXED = { 'X-Robots-Tag': 'noindex' }

const esc = (text: string) => text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)

/** The production domain on Vercel, never the request's host: this reads from that address */
function siteOrigin(request: NextRequest): string {
  const domain = process.env.VERCEL_PROJECT_PRODUCTION_URL
  // the local server listens on 127.0.0.1, and to Node's fetch "localhost" is first the address it doesn't
  return domain ? `https://${domain}` : request.nextUrl.origin.replace('//localhost', '//127.0.0.1')
}

// What an instance has read lately: a crawler goes through a unit's ids in order, and one slice holds 250 of them
const shells = new Map<string, Promise<string>>()
const shards = new Map<string, Promise<WhereShard | null>>()
const slices = new Map<string, Promise<Soldier[]>>()

function keep<T>(cache: Map<string, Promise<T>>, key: string, most: number, load: () => Promise<T>): Promise<T> {
  let known = cache.get(key)
  if (!known) {
    known = load()
    known.catch(() => cache.delete(key))
    cache.set(key, known)
    if (cache.size > (DEV ? 0 : most)) cache.delete(cache.keys().next().value!)
  }
  return known
}

async function read(url: string): Promise<Response> {
  const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(8000) })
  if (!response.ok && response.status !== 404) throw new Error(`${url}: ${response.status}`)
  return response
}

const shellOf = (origin: string, lang: Lang) => keep(shells, lang, 5, async () => {
  const response = await read(`${origin}${localePath(lang, '/borac')}`)
  if (!response.ok) throw new Error(`no page for ${lang}`)
  return response.text()
})

const shardOf = (origin: string, id: string) => keep(shards, id.slice(0, 7), 256, async () => {
  const response = await read(`${origin}${wherePath(id)}`)
  return response.ok ? response.json() as Promise<WhereShard> : null
})

const sliceOf = (origin: string, unit: string, part: number) => keep(slices, `${unit}/${part}`, 8, async () => {
  const response = await read(`${origin}${recordsPath(unit, part)}`)
  if (!response.ok) throw new Error(`no slice ${unit}/${part}`)
  return response.json() as Promise<Soldier[]>
})

function headTags(soldier: Soldier, unit: Unit, lang: Lang, origin: string, description: string): string {
  const t = messagesFor(lang)
  const address = (l: Lang) => `${origin}${recordPath(soldier.soldier_id, l)}`
  const portrait = portraitFor(soldier)
  return [
    `<title>${esc(`${soldier.full_name} · ${t.site.name}`)}</title>`,
    `<meta name="description" content="${esc(description)}"/>`,
    `<link rel="canonical" href="${address(lang)}"/>`,
    ...FINISHED_LANGS.map((l) => `<link rel="alternate" hreflang="${HTML_LANG[l]}" href="${address(l)}"/>`),
    `<meta property="og:title" content="${esc(soldier.full_name)}"/>`,
    `<meta property="og:description" content="${esc(description)}"/>`,
    `<meta property="og:url" content="${address(lang)}"/>`,
    `<meta property="og:site_name" content="${esc(t.site.name)}"/>`,
    `<meta property="og:locale" content="${OG_LOCALE[lang]}"/>`,
    `<meta property="og:type" content="website"/>`,
    // his photograph where the site has one, else the site's own picture; never cut from a book here, which would mean
    // rendering a PDF for every preview
    `<meta property="og:image" content="${origin}${portrait?.src ?? '/og.jpg'}"/>`,
    `<meta name="twitter:card" content="${portrait ? 'summary' : 'summary_large_image'}"/>`,
  ].join('')
}

/** The record as text, under the dialog that opens over it: what a preview, a crawler or a reader without scripts gets */
function plainRecord(soldier: Soldier, unit: Unit, lang: Lang): { html: string; description: string } {
  const t = messagesFor(lang)
  const name = unitName(unit, lang)
  const facts = recordFacts(soldier, t, unit.name)
  const { heroj, spomenica } = decorationsOf(soldier)
  const honours = [heroj && t.medals.heroj, spomenica && t.medals.spomenica].filter(Boolean) as string[]
  const told = facts.filter((f) => f.key === 'born' || f.key === 'duty' || f.key === 'death').map((f) => `${f.label}: ${f.value}`)
  const description = [name, ...honours, ...told].join(' · ').slice(0, LONGEST_DESCRIPTION)
  const entries = entriesOf(soldier).filter((e) => e.additional_info)
  const html = [
    `<div id="record-plain" class="record-plain container">`,
    `<h1>${esc(soldier.full_name)}</h1>`,
    `<p><a href="${localePath(lang, `/units/${unit.id}`)}">${esc(name)}</a></p>`,
    honours.length ? `<p>${esc(honours.join(' · '))}</p>` : '',
    facts.length ? `<dl>${facts.map((f) => `<dt>${esc(f.label)}</dt><dd>${esc(f.value)}</dd>`).join('')}</dl>` : '',
    entries.length ? `<h2>${esc(t.record.references)}</h2>` : '',
    ...entries.map((e) => {
      const book = sourceOf(e)?.title
      return `<blockquote><p>${esc(e.additional_info!)}</p>${book ? `<footer>${esc(book)}</footer>` : ''}</blockquote>`
    }),
    `</div>`,
  ].join('')
  return { html, description }
}

// The language menu's links, which the page was built with as "/en/borac", go to this record in each language
const withLanguageLinks = (shell: string, id: string) => shell.replace(LANGUAGE_LINK, (_, start) => `${start}/${encodeURIComponent(id)}"`)

function page(shell: string, soldier: Soldier, unit: Unit, lang: Lang, origin: string): string {
  const { html, description } = plainRecord(soldier, unit, lang)
  return withLanguageLinks(shell, soldier.soldier_id)
    .replace('</head>', () => `${headTags(soldier, unit, lang, origin, description)}</head>`)
    .replace(SLOT, () => html)
}

const htmlHeaders = (cache: string) => ({ 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': cache, ...NOT_INDEXED })

async function noSuchRecord(origin: string, lang: Lang, id: string): Promise<Response> {
  const html = withLanguageLinks(await shellOf(origin, lang), id)
    .replace('</head>', () => `<title>${esc(messagesFor(lang).site.name)}</title></head>`)
  return new Response(html, { status: 404, headers: htmlHeaders(KEPT_MISSING) })
}

export async function recordAnswer(request: NextRequest, lang: Lang, id: string): Promise<Response> {
  // Only for a next/link pointed at a record, which would run this for every record in sight: links to a record are
  // plain ones (components/RecordLink.tsx), and this keeps a new next/link from costing anything
  if (request.headers.get('next-router-prefetch')) {
    return new Response(null, { status: 204, headers: { 'Cache-Control': 'no-store' } })
  }
  const origin = siteOrigin(request)
  let unit: Unit | undefined
  try {
    const shard = isRecordId(id) ? await shardOf(origin, id) : null
    const place = shard && placeIn(shard, id)
    if (!place) return await noSuchRecord(origin, lang, id)
    if (place.id !== id) {
      return new Response(null, { status: 308, headers: { Location: recordPath(place.id, lang), 'Cache-Control': KEPT } })
    }
    unit = units.find((u) => u.id === place.unit)
    const soldier = unit && (await sliceOf(origin, unit.id, place.part)).find((r) => r.soldier_id === id)
    if (!unit || !soldier) return await noSuchRecord(origin, lang, id)
    return new Response(page(await shellOf(origin, lang), soldier, unit, lang, origin), { headers: htmlHeaders(KEPT) })
  } catch (error) {
    console.error(`/borac/${id}:`, error)
    const older = unit ? `/units/${unit.id}?${RECORD_PARAM}=${id}` : '/'
    return new Response(null, { status: 307, headers: { Location: localePath(lang, older), 'Cache-Control': 'no-store' } })
  }
}
