const SERBIAN_DIACRITICS_MAP: Record<string, string> = {
  'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': 'd',
  'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': 'D',
}

const DIACRITICS_REGEX = /[čćšžđČĆŠŽĐ]/g

export function removeDiacritics(str: string): string {
  return str.replace(DIACRITICS_REGEX, (match) => SERBIAN_DIACRITICS_MAP[match] || match)
}

// Without diacritics đ is usually typed as "dj" ("Djurić", "Djordje"). Since
// removeDiacritics folds đ into d, folding "dj" into d as well gives "Đurić",
// "Djurić" and "Durić" the same search key. Real d+j names ("Podjed",
// "Nedjeljko") fold the same way in the index and the query, so they still
// match themselves.
const DJ_REGEX = /([dD])[jJ]/g

export function normalizeForSearch(str: string): string {
  return removeDiacritics(str).replace(DJ_REGEX, '$1')
}
