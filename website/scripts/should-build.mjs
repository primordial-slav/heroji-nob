import { execFileSync } from 'child_process'

// Vercel's Ignored Build Step (vercel.json's ignoreCommand), run in website/ before each build: exit 0 skips the build
// (the deployment is cancelled and the live site stays as it is), exit 1 builds. A push builds only when something
// under website/ changed since the last deployment that was built, VERCEL_GIT_PREVIOUS_SHA: notes, the data pipeline
// and the parsers outside website/ change nothing the site serves, and each build is billed by the minute
// (2026-11-20). Whenever this cannot tell, it builds.

const git = (...args) => execFileSync('git', args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
const has = (sha) => {
  try {
    git('cat-file', '-e', `${sha}^{commit}`)
    return true
  } catch {
    return false
  }
}
const build = (why) => {
  console.log(`Build: ${why}`)
  process.exit(1)
}

const base = process.env.VERCEL_GIT_PREVIOUS_SHA
if (!base) build('no earlier deployment to compare with')
// Vercel clones only the last few commits: fetch the last deployment's commit when it is older
if (!has(base)) {
  try {
    git('fetch', '--depth=1', 'origin', base)
  } catch {}
}
if (!has(base)) build(`the last deployment's commit ${base.slice(0, 8)} is not in the clone`)

let changed
try {
  changed = git('diff', '--name-only', base, 'HEAD', '--', '.').split('\n').filter(Boolean)
} catch {
  build('git diff failed')
}
if (changed.length) build(`${changed.length} files changed under website/ since ${base.slice(0, 8)}, e.g. ${changed[0]}`)
console.log(`Skip: nothing under website/ changed since ${base.slice(0, 8)}`)
process.exit(0)
