import { units } from '@/app/data/units'

// Every name on the site: the sum of the units' soldierCount, which scripts/apply_corrections.py keeps
// current. Computed at build time, so it changes by itself whenever records or units are added.
// The home page says it under the search field: "110.430 imena" (t.home.total).
export const totalNames = units.reduce((sum, unit) => sum + unit.soldierCount, 0)
