import { units } from '@/app/data/units'

// Every name on the site: the sum of the units' soldierCount, which scripts/apply_corrections.py keeps
// current. Computed at build time, so it changes by itself whenever records or units are added.
// The home page says it in the search field: "Pretražite 108.150 imena" (t.home.placeholder).
export const totalNames = units.reduce((sum, unit) => sum + unit.soldierCount, 0)
