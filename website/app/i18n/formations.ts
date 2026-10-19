import type { Lang } from './config'
import { toCyrillic } from './cyrillic'
import type { Formation } from '@/app/data/unitFormations'

// The names of the divisions and corps a unit belonged to (data/unitFormations.ts), in each language: "6. lička
// divizija", "6th Lika Division", "1. proleterski korpus". By the number, with the name's word for the region or kind
// as the NOVJ tables give it; the Slovene divisions are plain "14. divizija" in Slovene, as Slovenes say it.

const DIVISION: Record<number, string> = {
  1: 'proleterska', 2: 'proleterska', 3: 'udarna', 4: 'krajiška', 5: 'krajiška', 6: 'lička', 7: 'banijska',
  8: 'kordunaška', 9: 'dalmatinska', 10: 'krajiška', 11: 'krajiška', 12: 'slavonska', 13: 'primorsko-goranska',
  14: 'slovenačka', 15: 'slovenačka', 16: 'vojvođanska', 17: 'istočnobosanska', 18: 'slovenačka',
  19: 'sjevernodalmatinska', 21: 'srpska', 22: 'srpska', 23: 'srpska', 24: 'srpska', 25: 'srpska', 26: 'dalmatinska',
  27: 'istočnobosanska', 28: 'slavonska', 29: 'hercegovačka', 30: 'slovenačka', 31: 'slovenačka', 32: 'zagorska',
  34: 'hrvatska', 35: 'lička', 36: 'vojvođanska', 37: 'sandžačka', 38: 'istočnobosanska', 39: 'krajiška',
  40: 'slavonska', 42: 'makedonska', 45: 'srpska', 46: 'srpska', 47: 'srpska', 51: 'vojvođanska',
  52: 'kosovsko-metohijska', 53: 'srednjobosanska',
}

// the corps without a word of their own (the 3., 4., 5., 7. and 9.) are named by their number alone
const CORPS: Record<number, string> = {
  1: 'proleterski', 2: 'udarni', 8: 'dalmatinski', 10: 'zagrebački', 12: 'vojvođanski', 13: 'srpski', 14: 'srpski',
}

type Other = 'sl' | 'mk' | 'en'
const WORDS: Record<string, Record<Other, string>> = {
  proleterska: { sl: 'proletarska', mk: 'пролетерска', en: 'Proletarian' },
  udarna: { sl: 'udarna', mk: 'ударна', en: 'Assault' },
  krajiška: { sl: 'krajiška', mk: 'краишка', en: 'Krajina' },
  lička: { sl: 'liška', mk: 'личка', en: 'Lika' },
  banijska: { sl: 'banijska', mk: 'банијска', en: 'Banija' },
  kordunaška: { sl: 'kordunska', mk: 'кордунска', en: 'Kordun' },
  dalmatinska: { sl: 'dalmatinska', mk: 'далматинска', en: 'Dalmatian' },
  slavonska: { sl: 'slavonska', mk: 'славонска', en: 'Slavonian' },
  'primorsko-goranska': { sl: 'primorsko-goranska', mk: 'приморско-горанска', en: 'Primorje-Gorski Kotar' },
  slovenačka: { sl: '', mk: 'словенечка', en: 'Slovene' },
  vojvođanska: { sl: 'vojvodinska', mk: 'војводинска', en: 'Vojvodina' },
  istočnobosanska: { sl: 'vzhodnobosanska', mk: 'источнобосанска', en: 'East Bosnian' },
  sjevernodalmatinska: { sl: 'severnodalmatinska', mk: 'севернодалматинска', en: 'North Dalmatian' },
  srpska: { sl: 'srbska', mk: 'српска', en: 'Serbian' },
  hercegovačka: { sl: 'hercegovska', mk: 'херцеговска', en: 'Herzegovina' },
  zagorska: { sl: 'zagorska', mk: 'загорска', en: 'Zagorje' },
  hrvatska: { sl: 'hrvaška', mk: 'хрватска', en: 'Croatian' },
  sandžačka: { sl: 'sandžaška', mk: 'санџачка', en: 'Sandžak' },
  makedonska: { sl: 'makedonska', mk: 'македонска', en: 'Macedonian' },
  'kosovsko-metohijska': { sl: 'kosovsko-metohijska', mk: 'косовско-метохиска', en: 'Kosovo-Metohija' },
  srednjobosanska: { sl: 'srednjebosanska', mk: 'среднобосанска', en: 'Central Bosnian' },
  proleterski: { sl: 'proletarski', mk: 'пролетерски', en: 'Proletarian' },
  udarni: { sl: 'udarni', mk: 'ударен', en: 'Assault' },
  dalmatinski: { sl: 'dalmatinski', mk: 'далматински', en: 'Dalmatian' },
  zagrebački: { sl: 'zagrebški', mk: 'загрепски', en: 'Zagreb' },
  vojvođanski: { sl: 'vojvodinski', mk: 'војводински', en: 'Vojvodina' },
  srpski: { sl: 'srbski', mk: 'српски', en: 'Serbian' },
}

const NOUN: Record<'d' | 'k', Record<'sr' | Other, string>> = {
  d: { sr: 'divizija', sl: 'divizija', mk: 'дивизија', en: 'Division' },
  k: { sr: 'korpus', sl: 'korpus', mk: 'корпус', en: 'Corps' },
}

function ordinal(n: number): string {
  const tens = n % 100
  if (tens >= 11 && tens <= 13) return `${n}th`
  return `${n}${({ 1: 'st', 2: 'nd', 3: 'rd' } as Record<number, string>)[n % 10] ?? 'th'}`
}

/** "6. lička divizija" in the page's language */
export function formationName(level: 'd' | 'k', n: number, lang: Lang): string {
  const word = (level === 'd' ? DIVISION : CORPS)[n] ?? ''
  if (lang === 'sr' || lang === 'sr-cyrl') {
    const name = [`${n}.`, word, NOUN[level].sr].filter(Boolean).join(' ')
    return lang === 'sr-cyrl' ? toCyrillic(name) : name
  }
  const local = word ? WORDS[word]?.[lang] ?? word : ''
  if (lang === 'en') return [ordinal(n), local, NOUN[level].en].filter(Boolean).join(' ')
  return [`${n}.`, local, NOUN[level][lang]].filter(Boolean).join(' ')
}

/** The years it was there: "1942–1945", or one year */
export function formationYears([, , from, to]: Formation): string {
  return to && to !== from ? `${from}–${to}` : String(from)
}
