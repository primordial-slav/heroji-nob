import fs from 'fs'
import path from 'path'

// The last step of `npm run build`, and only on Vercel's build machine: deletes from public/ the files that only the
// build reads, after the pages are built and before Vercel takes public/ into the deployment. They are the unit files
// (776 MB, which scripts/prepare-data.ts turns into public/data/) and the places index (22 MB, cut into
// public/data/places/), about half of what each deploy uploaded. No page or function reads them on the live site;
// middleware.ts already answers them 404, and stays for a deployment made otherwise. Anywhere else it does nothing:
// these are the data themselves in a checkout.

if (process.env.VERCEL !== '1' || !process.env.VERCEL_ENV) process.exit(0)

const pub = path.join(process.cwd(), 'public')
// middleware.ts's matcher: soldiers.json, *-soldiers.json, ostali-borci*.json
const BUILD_ONLY = /^(?:soldiers|.+-soldiers|ostali-borci[^/]*)\.json$/
const files = fs.readdirSync(pub).filter((name) => BUILD_ONLY.test(name)).map((name) => path.join(pub, name))
files.push(path.join(pub, 'relations', 'places.json'))

let bytes = 0
let dropped = 0
for (const file of files) {
  if (!fs.existsSync(file)) continue
  bytes += fs.statSync(file).size
  fs.rmSync(file)
  dropped++
}
console.log(`Not deployed: ${dropped} files only the build reads (${Math.round(bytes / 1048576)} MB)`)
