import { PROJ } from './map1941'

// The sheet's projection, a Lambert conformal conic, the same as scripts/make_map_1941.py's: a place's longitude
// and latitude (degrees) to the map's units, for whatever the page puts on the map
const RAD = Math.PI / 180
const t = (phi: number) => Math.tan(Math.PI / 4 + phi / 2)
const F1 = PROJ.lat1 * RAD
const F2 = PROJ.lat2 * RAD
const N = Math.log(Math.cos(F1) / Math.cos(F2)) / Math.log(t(F2) / t(F1))
const F = (Math.cos(F1) * t(F1) ** N) / N
const RHO0 = (PROJ.radius * F) / t(PROJ.lat0 * RAD) ** N

export function project(lon: number, lat: number): [number, number] {
  const rho = (PROJ.radius * F) / t(lat * RAD) ** N
  const theta = N * (lon - PROJ.lon0) * RAD
  const x = rho * Math.sin(theta)
  const y = RHO0 - rho * Math.cos(theta)
  return [(x - PROJ.x0) * PROJ.k, (PROJ.y0 - y) * PROJ.k]
}
