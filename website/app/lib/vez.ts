import type { CSSProperties } from 'react'
import manifest from '@/app/data/vez.json'
import { normalizeForSearch } from './diacritics'

// The embroidered frames round a soldier's portrait (public/vez/, scripts/make_vez_frames.py). His set of frames is
// chosen in our data, never shown: by the nationality his record prints where it is a minority's or a foreigner's,
// else by the part of the land he was born in (scripts/build_vez.py), else the neutral set. The frame within the set
// comes from his name, so he wears the same one on the home page's margins and in his record.

const INK: Record<string, string> = {
  red: 'var(--red-ink)', blue: 'var(--vez-blue)', gold: 'var(--vez-gold)', green: 'var(--vez-green)', ink: 'var(--ink)',
}

/** The sets whose faces the home page shows one of at most (Italians, Germans and Austrians, Hungarians) */
export const CAPPED_SETS = new Set<number>(manifest.capped)

// FNV-1a over the folded name: the same name gives the same frame wherever it is shown
function hash(text: string): number {
  let h = 0x811c9dc5
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i)
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return h
}

/** The frame a soldier wears: his set's (or the neutral set's, where we have none) by his name */
export function frameFor(set: number | null | undefined, name: string): number {
  const frames = manifest.sets[set ?? manifest.neutral] ?? manifest.sets[manifest.neutral]
  return frames[hash(normalizeForSearch(name).toLowerCase()) % frames.length]
}

/** The props that put a frame round an element with the class "vez" */
export function vezProps(frame: number): { 'data-vez-two'?: ''; style: CSSProperties } {
  const [first, second] = manifest.frames[frame]
  const style: Record<string, string> = { '--vez': `url("/vez/${frame}.svg")`, '--vez-ink': INK[first] }
  if (!second) return { style }
  style['--vez-2'] = `url("/vez/${frame}-2.svg")`
  style['--vez-ink-2'] = INK[second]
  return { 'data-vez-two': '', style }
}
