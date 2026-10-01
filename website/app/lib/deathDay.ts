// Day, month and year of a death date as the books write it: "17. 10. 1944", "26. II. 1943", "16. VII 1944",
// "25. januara 1943", "14 avgusta 1942", "7 travnja 1943", "20.4.1944", "9.11944" (= 9. 1. 1944).
// Dates without a day ("novembra 1944", "krajem aprila 1945") give null, and so do ranges of days ("26—31. maja 1943").

export interface DeathDay {
  day: number
  month: number
  year: number
}

const ROMAN: Record<string, number> = {
  i: 1, ii: 2, iii: 3, iv: 4, v: 5, vi: 6, vii: 7, viii: 8, ix: 9, x: 10, xi: 11, xii: 12,
}

// Serbian, Croatian and Slovenian month names in any case form, by their start
const MONTH_STEMS: [string, number][] = [
  ['jan', 1], ['sij', 1],
  ['feb', 2], ['velj', 2],
  ['mar', 3], ['ožu', 3], ['ozu', 3],
  ['apr', 4], ['trav', 4],
  ['maj', 5], ['svib', 5],
  ['jun', 6], ['lip', 6],
  ['jul', 7], ['srp', 7],
  ['avg', 8], ['aug', 8], ['kolov', 8],
  ['sep', 9], ['ruj', 9],
  ['okt', 10], ['oct', 10], ['listop', 10],
  ['nov', 11], ['stud', 11],
  ['dec', 12], ['pros', 12],
]

const NUMERIC = /(?<!\d)(\d{1,2})\s*\.\s*(\d{1,2})\s*\.?\s*(\d{4})/
const ROMAN_MONTH = /(?<!\d)(\d{1,2})\s*\.?\s*(xii|xi|ix|x|viii|vii|vi|iv|v|iii|ii|i)\s*\.?\s*(\d{4})/
const NAMED_MONTH = /(?<![\d—–-])(\d{1,2})\s*\.?\s+([a-zčćžšđ]+)\s*\.?\s*(\d{4})/

function monthFromName(word: string): number | null {
  const hit = MONTH_STEMS.find(([stem]) => word.startsWith(stem))
  return hit ? hit[1] : null
}

export function parseDeathDay(text: string): DeathDay | null {
  const s = text.toLowerCase()
  let day: number, month: number | null, year: number
  let m = s.match(NUMERIC)
  if (m) {
    ;[day, month, year] = [Number(m[1]), Number(m[2]), Number(m[3])]
  } else if ((m = s.match(ROMAN_MONTH))) {
    ;[day, month, year] = [Number(m[1]), ROMAN[m[2]], Number(m[3])]
  } else if ((m = s.match(NAMED_MONTH))) {
    ;[day, month, year] = [Number(m[1]), monthFromName(m[2]), Number(m[3])]
  } else {
    return null
  }
  if (!month || month < 1 || month > 12 || day < 1) return null
  // "00. 03. 1944" means the day isn't known; "31. 4." is a misprint
  if (day > new Date(Date.UTC(year || 2000, month, 0)).getUTCDate()) return null
  return { day, month, year }
}

export const MONTHS_GENITIVE = [
  'januara', 'februara', 'marta', 'aprila', 'maja', 'juna',
  'jula', 'avgusta', 'septembra', 'oktobra', 'novembra', 'decembra',
]
