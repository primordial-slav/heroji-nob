import type { Soldier } from '@/app/lib/types'
import { silhouettes } from '@/app/data/silhouettes'
import genders from '@/app/data/name-genders.json'

// The stand-in portrait for a soldier without a photograph: an anonymous outline of a partisan in a cap, a man's
// or a woman's (data/silhouettes.ts, from period portraits). The titovka was everyone's; the šajkača mostly worn
// by Serbs from Serbia and some from Bosnia. The soldier's id picks among the outlines that fit, so each record
// always shows the same one.

export interface Silhouette {
  id: string
  woman: boolean
  cap: 'titovka' | 'sajkaca'
  star: [number, number]   // where the cap's star goes, percent of the frame
  d: string                // the outline, on a 300 x 400 frame
}

type Region = 'srbija' | 'proleterska' | 'bosna'

// Where Serbs wearing the šajkača would mostly be found: units of Serbia, the 1st Proletarian (formed of Serbian
// and Montenegrin battalions) and the Bosnian units
const UNIT_REGION: Record<string, Region> = {
  'uzicki-odred': 'srbija',
  '1-sumadijska-brigada': 'srbija',
  '4-srpska-brigada': 'srbija',
  '14-srpska-brigada': 'srbija',
  '25-srpska-brigada': 'srbija',
  '25-srpska-divizija': 'srbija',
  'druga-proleterska-brigada': 'srbija',
  'prva-proleterska-brigada': 'proleterska',
  '2-krajiska-brigada': 'bosna',
  '3-krajiska-proleterska-brigada': 'bosna',
  '4-krajiska-brigada': 'bosna',
  '5-kozaracka-brigada': 'bosna',
  '6-krajiska-brigada': 'bosna',
  '8-krajiska-brigada': 'bosna',
  '19-bircanska-brigada': 'bosna',
  'tuzlanski-odred': 'bosna',
  '17-majevicka-brigada': 'bosna',
  '21-tuzlanska-brigada': 'bosna',
  '53-srednjobosanska-divizija': 'bosna',
}
// How often a Serb of such a unit gets the šajkača rather than the titovka
const SAJKACA_SHARE: Record<Region, number> = { srbija: 0.35, proleterska: 0.25, bosna: 0.15 }

// The same rule as the pipeline's "zvana" (scripts/feminine_alias.py): a bio's word forms tell a woman from a man
// ("rođena", "padla", "bolničarka"), and a married or maiden name ("por. Ciglar"); a bio that says neither, or
// as much of both, is decided by the given name, as the other bios show it. Words are whole words: \b doesn't
// know č or ž.
const word = (words: string) => new RegExp(`(?<!\\p{L})(?:${words})(?!\\p{L})`, 'giu')
const FEM = word(
  'rođena|rodjena|poginula|umrla|stupila|ranjena|nestala|streljana|ubijena|zarobljena|internirana|' +
  'demobilisana|demobilizirana|penzionisana|umirovljena|bila|živjela|živela|radila|padla|ubita|obešena|' +
  'obješena|borkinja|bolničarka|srpkinja|hrvatica|crnogorka|slovenka|muslimanka|jevrejka|židovka|makedonka|' +
  'ruskinja|italijanka|mađarica|slovakinja|učenica|domaćica|radnica|krojačica|studentkinja|kuharica|kuvarica|' +
  'sekretarka|komesarka|referentkinja|delegatkinja|desetarka|službenica|učiteljica|seljanka|zemljoradnica|' +
  'tkalja|švalja|partizanka|omladinka|skojevka|članica')
const MASC = word(
  'rođen|rodjen|poginuo|umro|stupio|nestao|streljan|ubijen|zarobljen|interniran|demobilisan|bio|živio|' +
  'živeo|radio|padel|umrl|ubit|srbin|hrvat|crnogorac|slovenac|musliman|jevrej|židov|makedonac|rus|italijan|' +
  'mađar|slovak|učenik|zemljoradnik|radnik|krojač|kuhar|kuvar|službenik|učitelj|seljak|tkač|kovač|stolar|' +
  'obućar|pekar|zidar|mesar|bravar|mehaničar|trgovac|omladinac|skojevac')
const MAIDEN = /(?:^|;)\s*(?:(?:por|ud)\. [A-ZČĆŽŠĐ]|roj\. [A-ZČĆŽŠĐ][^\s;,\d]*;)/g
// nicknames and parents say nothing of the soldier
const ASIDE = /(^|; )(?:majka|otac|zvan[ai]|ili) [^;]*;/g
const MEN_A = new Set(genders.menA)          // men's names that end in -a
const WOMEN = new Set(genders.women)         // women's names that don't

function count(text: string, re: RegExp): number {
  return (text.match(re) ?? []).length
}

export function isWoman(soldier: Soldier): boolean {
  if (genders.womenIds.includes(soldier.soldier_id)) return true
  if (genders.menIds.includes(soldier.soldier_id)) return false
  const text = [soldier.additional_info, ...(soldier.other_sources ?? []).map((o) => o.additional_info)]
    .join(' ').replace(ASIDE, ' ')
  const f = count(text, FEM) + count(text, MAIDEN)
  const m = count(text, MASC)
  if (f !== m) return f > m
  const name = soldier.first_name ?? ''
  if (MEN_A.has(name)) return false
  return WOMEN.has(name) || name.endsWith('a')
}

function isSerb(soldier: Soldier): boolean | undefined {
  const e = soldier.ethnicity || (soldier.additional_info ?? '').match(/\b(Srbin|Srpkinja|Crnogor\w+|Hrvat\w*|Muslim\w+|Sloven\w+)\b/)?.[1]
  return e ? /^Sr[bp]/.test(e) : undefined
}

// The same numbers in [0, 1) for the same soldier, every time
function shares(id: string): [number, number] {
  let h = 2166136261
  for (const c of id) h = Math.imul(h ^ c.charCodeAt(0), 16777619)
  const a = (h >>> 0) / 4294967296
  h = Math.imul(h ^ (h >>> 13), 2246822507)
  return [a, (h >>> 0) / 4294967296]
}

export function standInFor(soldier: Soldier, unitId?: string): Silhouette {
  const woman = isWoman(soldier)
  const [a, b] = shares(soldier.soldier_id)
  const region = unitId ? UNIT_REGION[unitId] : undefined
  const serb = isSerb(soldier)
  const cap = !woman && region && serb !== false && (serb || region === 'srbija') && a < SAJKACA_SHARE[region]
    ? 'sajkaca' : 'titovka'
  let pool = silhouettes.filter((s) => s.woman === woman && s.cap === cap)
  if (!pool.length) pool = silhouettes.filter((s) => s.woman === woman)
  return pool[Math.floor(b * pool.length)]
}
