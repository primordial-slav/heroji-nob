const SERBIAN_DIACRITICS_MAP: Record<string, string> = {
  'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': 'd',
  'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': 'D',
}

const DIACRITICS_REGEX = /[čćšžđČĆŠŽĐ]/g

export function removeDiacritics(str: string): string {
  return str.replace(DIACRITICS_REGEX, (match) => SERBIAN_DIACRITICS_MAP[match] || match)
}

// Serbian and Macedonian Cyrillic in Latin letters, so "Петровић" finds the books' "Petrović"
const CYRILLIC: Record<string, string> = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', ђ: 'đ', е: 'e', ж: 'ž', з: 'z', и: 'i', ј: 'j', к: 'k', л: 'l',
  љ: 'lj', м: 'm', н: 'n', њ: 'nj', о: 'o', п: 'p', р: 'r', с: 's', т: 't', ћ: 'ć', у: 'u', ф: 'f',
  х: 'h', ц: 'c', ч: 'č', џ: 'dž', ш: 'š', ѓ: 'đ', ќ: 'ć', ѕ: 'dz',
}
const CYRILLIC_REGEX = /[Ѐ-џ]/g

export function cyrillicToLatin(str: string): string {
  return str.replace(CYRILLIC_REGEX, (ch) => {
    const lower = ch.toLowerCase()
    const latin = CYRILLIC[lower]
    if (latin === undefined) return ch
    return ch === lower ? latin : latin.charAt(0).toUpperCase() + latin.slice(1)
  })
}

// Without diacritics đ is usually typed as "dj" ("Djurić", "Djordje"). Since
// removeDiacritics folds đ into d, folding "dj" into d as well gives "Đurić",
// "Djurić" and "Durić" the same search key. Real d+j names ("Podjed",
// "Nedjeljko") fold the same way in the index and the query, so they still
// match themselves.
const DJ_REGEX = /([dD])[jJ]/g

// -ić as English and German spell it abroad: "Petrovich", "Petrovitch", "Petrowitsch"
const ICH_REGEX = /(w?)(?:itsch|itch|ich)(?![a-zÀ-ɏ])/gi

export function normalizeForSearch(str: string): string {
  return removeDiacritics(cyrillicToLatin(str))
    .replace(DJ_REGEX, '$1')
    .replace(ICH_REGEX, (_, w: string) => (w ? 'vic' : 'ic'))
}
