// Serbo-Croatian in Cyrillic: the site's own Latin text (messages/sr.ts, the unit cards in data/units.ts, the
// book descriptions in data/sources.ts) written letter for letter in Cyrillic, so the two scripts always say the
// same thing. What the books print (entries, names, book titles) and what a visitor types stay as they are.

const LETTERS: Record<string, string> = {
  a: 'а', b: 'б', c: 'ц', č: 'ч', ć: 'ћ', d: 'д', đ: 'ђ', e: 'е', f: 'ф', g: 'г', h: 'х', i: 'и', j: 'ј',
  k: 'к', l: 'л', m: 'м', n: 'н', o: 'о', p: 'п', r: 'р', s: 'с', š: 'ш', t: 'т', u: 'у', v: 'в', z: 'з', ž: 'ж',
}
const DIGRAPHS: Record<string, string> = { lj: 'љ', nj: 'њ', dž: 'џ' }

// Kept in Latin: addresses, names of sites and licences, file formats, and words of other languages (q, w, x, y)
const KEEP = /https?:\/\/\S+|[\w-]+\.(?:org|com|net)\b|Wikimedia Commons|Pinki|CC BY-SA[\d. ]*|WIPO|PDF|JPG|PNG|MB\b|\b\w*[qwxyQWXY]\w*\b/g

// Words not written letter for letter
const WORDS: [RegExp, string][] = [[/\bEmail\b/g, 'Имејл']]

function letter(ch: string): string {
  const lower = ch.toLowerCase()
  const cyr = LETTERS[lower]
  if (!cyr) return ch
  return ch === lower ? cyr : cyr.toUpperCase()
}

function plainToCyrillic(text: string): string {
  let out = ''
  for (let i = 0; i < text.length; i++) {
    const pair = text.slice(i, i + 2)
    const digraph = DIGRAPHS[pair.toLowerCase()]
    if (digraph) {
      // "Lj" and "LJ" both start a capital: Љубљана, ЉУБЉАНА
      out += pair[0] === pair[0].toLowerCase() ? digraph : digraph.toUpperCase()
      i++
    } else {
      out += letter(text[i])
    }
  }
  return out
}

// Text a message function was given (a query, a name, a book's title) is marked while the message is built, so
// only the message's own words change script
const OPEN = ''
const CLOSE = ''
const MARKED = new RegExp(`${OPEN}[^${CLOSE}]*${CLOSE}`, 'g')

/** "Pretraga boraca" -> "Претрага бораца"; addresses, "znaci.org", "PDF" and marked text stay as they are */
export function toCyrillic(text: string): string {
  const kept: string[] = []
  const hold = (s: string) => `${OPEN}${kept.push(s) - 1}${CLOSE}`
  let s = text.replace(MARKED, hold)
  s = s.replace(KEEP, hold)
  for (const [from, to] of WORDS) s = s.replace(from, to)
  s = s.split(new RegExp(`(${OPEN}\\d+${CLOSE})`)).map((part, i) => (i % 2 ? part : plainToCyrillic(part))).join('')
  return s.replace(new RegExp(`${OPEN}(\\d+)${CLOSE}`, 'g'), (_, n) => unmark(kept[Number(n)]))
}

// An empty string stays empty, so a message that checks for one ("q ? … : …") still sees it
function mark(value: unknown): unknown {
  return typeof value === 'string' && value !== '' ? `${OPEN}${value}${CLOSE}` : value
}

function unmark(text: string): string {
  return text.replace(new RegExp(`[${OPEN}${CLOSE}]`, 'g'), '')
}

type Overrides<T> = { [K in keyof T]?: T[K] extends (...args: never[]) => unknown ? T[K] : T[K] extends object ? Overrides<T[K]> : T[K] }

/**
 * A messages object in Cyrillic: every string, and every string a message function returns, with the strings the
 * function was given left as they came. `overrides` replaces what letter-for-letter can't do.
 */
export function cyrillicMessages<T>(messages: T, overrides: Overrides<T> = {}): T {
  const convert = (value: unknown, override: unknown): unknown => {
    if (override !== undefined && (typeof override !== 'object' || override === null)) return override
    if (typeof value === 'string') return toCyrillic(value)
    if (typeof value === 'function') {
      return (...args: unknown[]) => {
        const result = value(...args.map(mark))
        return typeof result === 'string' ? toCyrillic(result) : result
      }
    }
    if (Array.isArray(value)) return value.map((v) => convert(v, undefined))
    if (value && typeof value === 'object') {
      const o = (override ?? {}) as Record<string, unknown>
      return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, convert(v, o[k])]))
    }
    return value
  }
  return convert(messages, overrides) as T
}
