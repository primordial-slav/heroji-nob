import fs from 'fs'
import path from 'path'
import type { GalleryItem } from '@/app/views/GalleryClient'

// Server only: what scripts/prepare-data.ts writes to generated/ (in .gitignore) for the pages to read while they are
// built, so they don't read every unit's data file themselves

export const GENERATED_DIR = 'generated'
export const PAGES_FILE = path.join(GENERATED_DIR, 'pages.json')

export interface GeneratedPages {
  /** How many records each unit's data file has, by the unit's id */
  counts: Record<string, number>
  /** The Galerija's portraits */
  gallery: GalleryItem[]
}

const shared = globalThis as unknown as { generatedPages?: { mtime: number; pages: GeneratedPages } }

/** The pages' data, or null if scripts/prepare-data.ts has not run in this checkout */
export function generatedPages(): GeneratedPages | null {
  const file = path.join(process.cwd(), PAGES_FILE)
  if (!fs.existsSync(file)) return null
  const mtime = fs.statSync(file).mtimeMs
  if (shared.generatedPages?.mtime !== mtime) {
    shared.generatedPages = { mtime, pages: JSON.parse(fs.readFileSync(file, 'utf8')) }
  }
  return shared.generatedPages.pages
}

/** A generated public file (lib/dataFiles.ts) as JSON, or null if there is none */
export function generatedFile<T>(urlPath: string): T | null {
  const file = path.join(process.cwd(), 'public', ...urlPath.split('/').filter(Boolean))
  return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null
}
