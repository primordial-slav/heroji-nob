// The light and the season of each step, for the sheet's shading. Only what the book says: the hour it gives, read
// against the sun over Lika that day, or its own words for when ("pre zore", "čim je pao mrak"); a step that goes on
// from the one before ("zatim", "za to vreme") keeps its light, and one the book doesn't place in the day is drawn in
// plain daylight, with no sign by the date. The book names no weather, so none is drawn.

import type { Episode } from './episodes'

export type Phase = 'night' | 'dawn' | 'day' | 'golden' | 'dusk'
export type Season = 'summer' | 'earlyAutumn' | 'autumn' | 'lateAutumn'
export type Light = { phase: Phase; why: string } | null

const MONTHS: Record<string, number> = {
  januara: 1, februara: 2, marta: 3, aprila: 4, maja: 5, juna: 6, jula: 7, avgusta: 8, septembra: 9, oktobra: 10,
  novembra: 11, decembra: 12,
}

/** "6. septembra 1942." -> [1942, 9, 6]; "1–3. septembra", "12. ili 13. avgusta": the first day */
function dayOf(date: string): [number, number, number] | null {
  const m = date.match(/(\d{1,2})\.?(?:\s*(?:–|-|ili)\s*\d{1,2}\.)?\s+([a-zčćžšđ]+)\s+(\d{4})/i)
  if (!m || !MONTHS[m[2].toLowerCase()]) return null
  return [+m[3], MONTHS[m[2].toLowerCase()], +m[1]]
}

export function seasonOf(date: string): Season {
  const m = dayOf(date)?.[1] ?? 7
  return m <= 8 ? 'summer' : m === 9 ? 'earlyAutumn' : m === 10 ? 'autumn' : 'lateAutumn'
}

// Lika, about the middle of the battalion's ground
const LAT = 45.0, LON = 15.4
const rad = Math.PI / 180

/** Sunrise and sunset by the clocks of the day: the NDH kept German time, summer time to 2 November 1942 */
function sun([y, m, d]: [number, number, number]): { rise: number; set: number } {
  const n = Math.round((Date.UTC(y, m - 1, d) - Date.UTC(y, 0, 0)) / 864e5)
  const b = (360 / 365) * (n - 81) * rad
  const decl = 23.44 * rad * Math.sin(b)
  const eot = 9.87 * Math.sin(2 * b) - 7.53 * Math.cos(b) - 1.5 * Math.sin(b)        // minutes
  const h = Math.acos((Math.sin(-0.833 * rad) - Math.sin(LAT * rad) * Math.sin(decl)) / (Math.cos(LAT * rad) * Math.cos(decl))) / rad
  const noon = 12 - LON / 15 - eot / 60                                                  // UTC
  const zone = y === 1942 && (m < 11 || (m === 11 && d < 2)) && m >= 4 ? 2 : 1
  return { rise: noon - h / 15 + zone, set: noon + h / 15 + zone }
}

const clock = (h: number) => {
  const t = Math.round(h * 12) / 12
  return `${Math.floor(t)}.${String(Math.round((t % 1) * 60)).padStart(2, '0')}`
}

export const PHASE_NAME: Record<Phase, string> = {
  night: 'Noć', dawn: 'Svitanje', day: 'Dan', golden: 'Kasno popodne', dusk: 'Sumrak',
}

/** The phase of an hour on a day */
function byHour(h: number, day: [number, number, number]): { phase: Phase; rise: number; set: number } {
  const { rise, set } = sun(day)
  const phase: Phase = h < rise - 0.75 || h > set + 0.75 ? 'night'
    : h < rise + 0.5 ? 'dawn'
      : h >= set - 0.25 ? 'dusk'
        : h >= set - 1.25 ? 'golden' : 'day'
  return { phase, rise, set }
}

// the book's words for when, in the order they are tried ("pre zore" before "zora", "uveče" before "dana")
const WORDS: [RegExp, Phase][] = [
  [/pre zore|pred zoru|do svitanja|\bno[ćc]|ponoć/i, 'night'],
  [/svanu|osvit|svita|\bzor/i, 'dawn'],
  [/mrak|uve[čc]|ve[čc]er/i, 'dusk'],
  [/popodne/i, 'golden'],
  [/ujutr|celog dana|tokom dana|preko dana/i, 'day'],
]
// words that only go on from the step before
const GOES_ON = /^(?:zatim|potom|odmah zatim|posle toga|za to vreme|tokom borbe|u najžešćem okršaju|posle artiljerijske pripreme)$/i

export function lightOf(ep: Episode, si: number): Light {
  const s = ep.steps[si]
  const day = dayOf(s.date)
  const said = (s.time ?? s.when ?? '').trim()
  const hm = said.match(/(\d{1,2})\.(\d{2})/)
  if (hm && day) {
    // "posle 18.30" is a while after it; "do", "oko", "od" the hour itself
    const h = +hm[1] + +hm[2] / 60 + (/posle/i.test(said) ? 0.5 : 0)
    const { phase, rise, set } = byHour(h, day)
    return { phase, why: `${PHASE_NAME[phase]}: knjiga kaže „${said}“; sunce je tog dana izlazilo oko ${clock(rise)}, a zalazilo oko ${clock(set)}.` }
  }
  if (s.when) {
    for (const [re, phase] of WORDS) {
      if (re.test(s.when)) return { phase, why: `${PHASE_NAME[phase]}: knjiga kaže „${s.when}“.` }
    }
    if (GOES_ON.test(s.when) && si > 0 && ep.steps[si - 1].date === s.date) {
      const before = lightOf(ep, si - 1)
      if (before) return { phase: before.phase, why: `${PHASE_NAME[before.phase]}: „${s.when}“, kao u koraku pre ovog.` }
    }
  }
  return null
}
