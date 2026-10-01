import { units } from '@/app/data/units'

// Every name on the site: the sum of the units' soldierCount, which scripts/apply_corrections.py keeps
// current. Computed at build time, so it changes by itself whenever records or units are added.
export const totalNames = units.reduce((sum, unit) => sum + unit.soldierCount, 0)

// 108150 -> "108.150" (written out rather than toLocaleString, so server and browser always agree)
export function thousands(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

// "Pretražite 108.150 imena", "Pretražite 108.151 ime"
export function searchAllPlaceholder(n: number = totalNames): string {
  const word = n % 10 === 1 && n % 100 !== 11 ? 'ime' : 'imena'
  return `Pretražite ${thousands(n)} ${word}`
}
