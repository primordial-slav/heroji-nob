import { spawn } from 'child_process'
import fs from 'fs'
import path from 'path'

// Under `next dev` only (instrumentation.ts): keeps what scripts/prepare-data.ts writes from the data files up to
// date while the dev server runs. It runs the script when the server starts and again a few seconds after a unit's
// data file, its life events, the places index or the frames change; the script writes only what changed, in a
// process of its own, so the dev server never holds every unit's data. A change while it runs runs it once more.

const QUIET_MS = 4000
// package.json's "prepare-data", run with this server's own node, which needs no npm on the path (the main
// checkout's server is started by autostart.vbs with node.exe alone)
const BUNDLE = path.join('.next', 'cache', 'prepare-data.cjs')
const STEPS = [
  [path.join('node_modules', 'esbuild', 'bin', 'esbuild'), 'scripts/prepare-data.ts', '--bundle', '--platform=node',
    '--format=cjs', `--outfile=${BUNDLE}`, '--log-level=warning'],
  ['--max-old-space-size=6144', BUNDLE],
]

export function watchData() {
  const shared = globalThis as unknown as { dataWatch?: boolean }
  if (shared.dataWatch) return
  shared.dataWatch = true

  const root = process.cwd()
  let running = false
  let again = false
  let timer: ReturnType<typeof setTimeout> | undefined

  const run = () => {
    if (running) {
      again = true
      return
    }
    running = true
    const step = (k: number) => {
      const child = spawn(process.execPath, STEPS[k], { cwd: root, stdio: 'inherit' })
      child.on('error', (error) => done(error.message))
      child.on('exit', (code) => (code ? done(`code ${code}`) : k + 1 < STEPS.length ? step(k + 1) : done()))
    }
    const done = (failed?: string) => {
      running = false
      if (failed) console.error(`prepare-data stopped: ${failed}`)
      if (again) {
        again = false
        run()
      }
    }
    step(0)
  }
  const soon = () => {
    clearTimeout(timer)
    timer = setTimeout(run, QUIET_MS)
  }

  // public/ holds the unit files (and public/data/, which the script writes and nothing here watches)
  const watch = (dir: string, wanted: (name: string) => boolean) => {
    if (!fs.existsSync(dir)) return
    fs.watch(dir, (_event, name) => {
      if (name && wanted(name.toString())) soon()
    })
  }
  watch(path.join(root, 'public'), (name) => name.endsWith('.json'))
  watch(path.join(root, 'public', 'relations'), (name) => name === 'places.json')
  watch(path.join(root, 'data'), (name) => name === 'vez-sets.json')
  watch(path.join(root, 'data', 'life-events'), (name) => name.endsWith('.json'))
  watch(path.join(root, 'data', 'events'), (name) => name.endsWith('.json'))
  run()
}

// Next restarts a dev server only when its JavaScript heap nears its limit, half the machine's memory, and what grew
// over days of code changes was largely outside that heap (the search data's buffers): the main checkout's server
// reached 6 GB on a 16 GB machine (2026-11-19). Past this much of both it exits with the code Next's `next dev` takes as
// "restart" (RESTART_EXIT_CODE in next/dist/server/lib/utils), and comes back in a few seconds with nothing held. Not
// `rss`, which on Windows is the working set: under memory pressure it showed 182 MB of the 6 GB the server held.
const MOST_MB = Number(process.env.DEV_MEMORY_LIMIT_MB) || 2500
const RESTART_EXIT_CODE = 77

export function watchMemory() {
  const shared = globalThis as unknown as { memoryWatch?: boolean }
  if (shared.memoryWatch) return
  shared.memoryWatch = true
  setInterval(() => {
    const { heapUsed, external } = process.memoryUsage()
    const mb = Math.round((heapUsed + external) / 1048576)
    if (mb < MOST_MB) return
    console.warn(`The dev server holds ${mb} MB (more than ${MOST_MB}); restarting it`)
    process.exit(RESTART_EXIT_CODE)
  }, 60_000).unref()
}
