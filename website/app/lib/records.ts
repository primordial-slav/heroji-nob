import type { Soldier, SoldierSource } from './types'
import type { Unit } from '@/app/data/units'
import { units } from '@/app/data/units'
import { localePath, type Lang } from '@/app/i18n/config'
import { isWoman } from './standIn'

// The older address of a record, /units/<unit>?borac=<soldier id>, which old links still use, and the memorial card's
export const RECORD_PARAM = 'borac'

// The name the soldier's own entry gives him as "zvani Tonko" / "zvana Mica" (the user, 2026-11-23: shown by the name,
// in quotes, on the card, the memorial card and in the search's results: Krstulović Ante „Tonko“). The first such name
// in his own entry; not a place's ("mesto zvano Pređel"), nor one a sentence about a relative gives ("brat mu zvani
// ..."), nor his first name again.
const NICKNAME = /(^|[^\p{L}])zvan[ai]\s+[„"»]?([A-ZČĆŽŠĐ][a-zčćžšđ'-]+)/u
const NOT_HIS = /(?:^|[^\p{L}])(?:brat\p{L}*|sestr\p{L}*|otac|oca|sin|sina|majk\p{L}*|muž\p{L}*|supru\p{L}*|stric\p{L}*|ujak\p{L}*)(?:\s+(?:mu|joj|je))?\s*$/iu

export function nicknameOf(soldier: Pick<Soldier, 'additional_info' | 'first_name'>): string | undefined {
  const text = soldier.additional_info ?? ''
  const m = NICKNAME.exec(text)
  if (!m) return undefined
  if (NOT_HIS.test(text.slice(Math.max(0, m.index - 24), m.index + m[1].length))) return undefined
  return m[2] === soldier.first_name ? undefined : m[2]
}

export function unitByName(name?: string): Unit | undefined {
  return name ? units.find((u) => u.name === name) : undefined
}

/** A record's own address, /borac/<soldier id>, in a language /en/borac/<soldier id> (lib/recordAnswer.ts answers it). Link
 * to it with a plain <a>, never next/link, whose prefetching would run that route for every record in sight. */
export function recordPath(soldierId: string, lang: Lang): string {
  return localePath(lang, `/borac/${encodeURIComponent(soldierId)}`)
}

export function cardPath(unit: Unit, soldierId: string, lang: Lang): string {
  return localePath(lang, `/kartica?jedinica=${encodeURIComponent(unit.id)}&${RECORD_PARAM}=${encodeURIComponent(soldierId)}`)
}

// The soldier's own entry, then the same soldier's entries in the unit's other books
export function entriesOf(soldier: Soldier): SoldierSource[] {
  return [soldier, ...(soldier.other_sources ?? [])]
}

export const hasPage = (e: SoldierSource) => e.pdf_page != null && e.pdf_file != null

/** A book in the Poreklo digital library (biblioteka.poreklo.rs): scanned there, open to its members only. The site
 * names it and never links it: its key is "poreklo:<source id>" (data/sources.ts), and the published data carry that
 * key instead of the library's address (scripts/prepare-data.ts, the user's wish of 2026-11-19). The address itself is
 * still recognised, so a record that kept one is never shown as a link either. */
export const isPoreklo = (url?: string) => !!url && (url.startsWith('poreklo:') || url.startsWith('https://biblioteka.poreklo.rs/'))

/** What a soldier's family sent from its papers (a military booklet, a decision, a photograph), for a man no book prints:
 * the source "Porodična arhiva", named and never linked; and so what a visitor who is not of the family sent ("Poruke
 * posetilaca", posetioci:<entry>) */
export const isFamily = (url?: string) => !!url && (url.startsWith('porodica:') || url.startsWith('posetioci:'))

/** The 1964 census of the war's dead, a PDF per republic on the Museum of Genocide Victims' site */
export const isMuseum = (url?: string) => !!url?.startsWith('https://www.muzejgenocida.rs/')

/** "1924 – 1945" when the record has both years; a capture or a wound is no death (lib/deathDay.ts) */
export function lifeYears(soldier: Soldier): string | null {
  if (soldier.death_type === 'zarobljen' || soldier.death_type === 'ranjen') return null
  const born = soldier.birth_year?.match(/\d{4}/)?.[0]
  const died = soldier.death_date?.match(/\d{4}/)?.[0]
  return born && died ? `${born} – ${died}` : null
}

// "narodni heroj", "proglašen za narodnog heroja", "Nosilac Ordena narodnog heroja"; not "predložen za narodnog heroja",
// and not the plural ("NARODNI HEROJI JUGOSLAVIJE ...", a page heading glued to an entry)
const HERO = /narodn(?:i|og|im)\s*heroj(?!i)/i      // the OCR can lose the space ("Narodniheroj")
const PROPOSED = /predložen\w*\s+za\s+narodnog\s+heroja/gi
const SPOMENICA = /spomenic/i
// Spomenice that are no Partizanska spomenica 1941 (2026-11-22): the title of the Spomenica crnogorskim antifašistima
// 1941-1945, the roll of Montenegro's fallen, which had given the medal to its 17,369 records, men who joined in 1944
// among them; the Albanska spomenica of the 1915 retreat ("nosilac Albanske spomenice", OCR'd "Albaiske", "Albaneke":
// 22 records); a book's page footer glued to an entry ("11. I 1943. godine. 4 — Spomenica", Trebinjci)
const NOT_THE_MEDAL = /spomenic\w*\s+crnogorsk\w*\s+antifa\w*|alba\w*\s+spomenic\w*|\d+\s*[—–]\s*spomenica(?!\s*(?:19|'?41))/gi
const HER_OWN = /proglašena\s+(?:je\s+)?(?:za\s+)?narodn\w*\s*heroj|narodn\w*\s*heroj\w*\s+(?:je\s+)?proglašena|narodn\w*\s+heroin/i
// A sentence about someone else: a relative, or a man ("koji je proglašen", "poginuo kao komandant")
const RELATIVE = /(?:^|[^\p{L}])(?:brat\p{L}*|bra-t|braća|sin|sina|sinov\p{L}*|otac|oca|ocem|majk\p{L}*|sestr\p{L}*|muž\p{L}*|supru\p{L}*|kći|kćer\p{L}*|njen\p{L}*|njihov\p{L}*|njegov\p{L}*|njih|stric\p{L}*|ujak\p{L}*|djed\p{L}*|deda)(?![\p{L}])/iu
const A_MAN = /(?:^|[^\p{L}])(?:koji|proglašen|poginuo|odlikovan)(?![\p{L}])/iu
const SENTENCE = /;|\.\s+(?=[A-ZČĆŽŠĐ(])/
const HERO_BOOK = /^(?:zbornik-heroja-1957|narodni-heroji-1982|pali-za-lepsa-svitanja|niksicki-odred-narodni-heroji)$/

/** The soldier's memberships of SKOJ and the party, with the year each began where the entries say: "SKOJ 1941, KPJ
 * 1944" (the field `party`, scripts/extract_structured_fields.py read_party) is [['SKOJ', '1941'], ['KPJ', '1944']] */
export function partyOf(soldier: Soldier): [string, string][] {
  return (soldier.party ?? '').split(', ').filter(Boolean).map((p) => {
    const [org, year = ''] = p.split(' ')
    return [org, year]
  })
}

/** The decorations any of the soldier's entries names */
export function decorationsOf(soldier: Soldier): { heroj: boolean; spomenica: boolean } {
  const entries = entriesOf(soldier)
  const text = entries.map((e) => e.additional_info ?? '').join(' ')
  let heroj = HERO.test(text.replace(PROPOSED, ''))
  // A hero a woman is the sister, mother or wife of is not her own title ("njen brat Miloš ... proglašen za narodnog
  // heroja", "Otac, narodni heroj Jugoslavije", "sestra Ljubica proglašena narodnim herojem": the 5. proleterska's
  // and 12. slavonska's women, 2026-10-28): hers is an entry of a hero book, the feminine in a sentence that names no
  // relative, or a sentence that names no relative and no man, nor does the one before it ("Narodni heroj.",
  // "Odlikovana Ordenom narodnog heroja"; not "Sva tri brata ... su poginula. Stevo je Narodni heroj")
  if (heroj && isWoman(soldier)) {
    const sentences = text.replace(PROPOSED, '').split(SENTENCE)
    const other = (s = '') => RELATIVE.test(s) || A_MAN.test(s)
    heroj = entries.some((e) => HERO_BOOK.test(e.ref_book ?? '')) || sentences.some((s, i) =>
      (HER_OWN.test(s) && !RELATIVE.test(s)) || (HERO.test(s) && !other(s) && !other(sentences[i - 1])))
  }
  return { heroj, spomenica: SPOMENICA.test(text.replace(NOT_THE_MEDAL, '')) }
}
