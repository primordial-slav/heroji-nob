import type { Soldier } from '@/app/lib/types'
import { silhouettes } from '@/app/data/silhouettes'

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

// A bio's word forms tell a woman from a man ("rođena", "poginula", "bolničarka")
const FEM = /\b(rođena|rodjena|poginula|umrla|nestala|ranjena|streljana|ubijena|zarobljena|stupila|bila|radila|borkinja|bolničarka|srpkinja|hrvatica|crnogorka|slovenka|muslimanka|jevrejka|učenica|domaćica|radnica|zemljoradnica|partizanka|omladinka|skojevka|zvana)\b/gi
const MASC = /\b(rođen|rodjen|poginuo|umro|nestao|ranjen|streljan|ubijen|zarobljen|stupio|bio|radio|srbin|hrvat|crnogorac|slovenac|musliman|jevrejin|učenik|zemljoradnik|radnik|zvani)\b/gi
// Men's names that end in -a
const MALE_A = new Set([
  'Nikola', 'Luka', 'Ilija', 'Andrija', 'Sava', 'Toma', 'Kosta', 'Mića', 'Pera', 'Jova', 'Đura', 'Raša', 'Laza',
  'Vasa', 'Uča', 'Mika', 'Saša', 'Ljuba', 'Joca', 'Boža', 'Sima', 'Vlada', 'Jura', 'Krsta', 'Mileta', 'Steva',
  'Gaja', 'Jakša', 'Zarija', 'Jeremija', 'Zaharija', 'Avdija', 'Alija', 'Hamza', 'Musa', 'Isa', 'Mustafa', 'Mija',
  'Jovica', 'Perica', 'Nikica', 'Ivica', 'Đoka', 'Paja', 'Neđa', 'Baća', 'Slaviša', 'Miša', 'Joviša', 'Periša',
  'Ljubiša', 'Dragiša', 'Rajica', 'Radojica', 'Milija',
])

function count(text: string, re: RegExp): number {
  return (text.match(re) ?? []).length
}

export function isWoman(soldier: Soldier): boolean {
  const ethnicity = soldier.ethnicity ?? ''
  if (/kinja$|ica$|ka$/.test(ethnicity)) return true          // Srpkinja, Hrvatica, Crnogorka
  if (ethnicity) return false
  const text = [soldier.additional_info, ...(soldier.other_sources ?? []).map((o) => o.additional_info)].join(' ')
  const f = count(text, FEM)
  const m = count(text, MASC)
  if (f !== m) return f > m
  const name = soldier.first_name ?? ''
  return name.endsWith('a') && !MALE_A.has(name)
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
