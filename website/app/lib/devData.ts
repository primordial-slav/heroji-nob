import { spawn } from 'child_process'
import fs from 'fs'
import path from 'path'

// Under `next dev` only (instrumentation.ts): keeps what scripts/prepare-data.ts writes from the data files up to
// date while the dev server runs. It runs the script when the server starts and again a few seconds after a unit's
// data file, its life events, the places index or the frames change; the script writes only what changed, in a
// process of its own, so the dev server never holds every unit's data. A change while it runs runs it once more.

const QUIET_MS = 4000

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
    const child = spawn('npm run --silent prepare-data', { cwd: root, shell: true, stdio: 'inherit' })
    child.on('exit', (code) => {
      running = false
      if (code) console.error(`prepare-data stopped with code ${code}`)
      if (again) {
        again = false
        run()
      }
    })
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
  run()
}
