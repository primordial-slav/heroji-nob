const SERBIAN_DIACRITICS_MAP: Record<string, string> = {
  'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': 'd',
  'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': 'D',
}

const DIACRITICS_REGEX = /[čćšžđČĆŠŽĐ]/g

export function removeDiacritics(str: string): string {
  return str.replace(DIACRITICS_REGEX, (match) => SERBIAN_DIACRITICS_MAP[match] || match)
}
