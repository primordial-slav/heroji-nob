import { NextResponse } from 'next/server'

// The unit files (public/*.json: "<unit>-soldiers.json", "soldiers.json", "ostali-borci*.json") are read only while the
// site is built (next.config.js): no page loads them, they load the files scripts/prepare-data.ts writes (public/data/).
// Served, they would hand anyone every unit's records at once, 776 MB in all and 53 MB the largest, on the site's
// bandwidth; they answer 404 instead. The matcher keeps every other address away from this function.
export function middleware() {
  return new NextResponse('Not found', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8' } })
}

export const config = {
  matcher: ['/soldiers.json', '/:file([^/]+-soldiers\\.json)', '/:file(ostali-borci[^/]*\\.json)'],
}
