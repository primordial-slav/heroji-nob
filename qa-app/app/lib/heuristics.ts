import type { Soldier } from './types'

export function detectSuspicious(soldier: Soldier): string[] {
  const flags: string[] = []

  // 1. Long additional_info (likely merged entries)
  if (soldier.additional_info && soldier.additional_info.length > 200) {
    flags.push('long_info')
  }

  // 2. Lowercase in last_name (OCR artifact like PERUNlClC)
  if (soldier.last_name && /[a-zčćžšđ]/.test(soldier.last_name) && soldier.last_name.length > 1) {
    // Check it's not just normal title case
    const firstChar = soldier.last_name[0]
    const rest = soldier.last_name.slice(1)
    if (firstChar === firstChar.toUpperCase() && /[A-ZČĆŽŠĐ]/.test(rest)) {
      flags.push('mixed_case_lastname')
    }
  }

  // 3. Empty first_name
  if (!soldier.first_name || soldier.first_name.trim() === '') {
    flags.push('empty_first_name')
  }

  // 4. Birth year mismatch
  if (soldier.birth_year && soldier.additional_info) {
    const yearMatches = soldier.additional_info.match(/\b(18|19)\d{2}\b/g)
    if (yearMatches && yearMatches.length > 0) {
      // The first year in additional_info is usually birth year
      if (yearMatches[0] !== soldier.birth_year) {
        flags.push('birth_year_mismatch')
      }
    }
  }

  // 5. full_name doesn't match last_name + first_name
  if (soldier.full_name) {
    const parts = [soldier.last_name, soldier.middle_name, soldier.first_name].filter(Boolean)
    const expected = parts.join(' ')
    if (soldier.full_name !== expected && soldier.full_name.replace(/\s+/g, ' ').trim() !== expected) {
      flags.push('fullname_mismatch')
    }
  }

  // 6. ALL CAPS words in additional_info (name leaked into info)
  if (soldier.additional_info) {
    const capsWords = soldier.additional_info.match(/\b[A-ZČĆŽŠĐ]{3,}\b/g)
    // Filter out common abbreviations
    const filtered = capsWords?.filter(w => !['NOP', 'NOV', 'SKOJ', 'KPJ', 'SSSR', 'NOB', 'AFŽ'].includes(w))
    if (filtered && filtered.length > 0) {
      flags.push('caps_in_info')
    }
  }

  // 7. Missing PDF position data
  if (!soldier.pdf_page || !soldier.pdf_y) {
    flags.push('no_pdf_position')
  }

  // 8. Garbled diacritics (German-style chars in Serbian text)
  const allText = (soldier.last_name || '') + (soldier.first_name || '') + (soldier.additional_info || '')
  if (/[äöüÄÖÜ]/.test(allText)) {
    flags.push('garbled_diacritics')
  }

  // 9. Last name looks like section header
  if (soldier.last_name && soldier.last_name.length > 15 && !/[a-zčćžšđ]/.test(soldier.last_name)) {
    flags.push('possible_header')
  }

  return flags
}

export function detectDuplicates(soldiers: Soldier[]): Map<string, string[]> {
  // Group by full_name within same brigade prefix
  const nameMap = new Map<string, string[]>()

  for (const s of soldiers) {
    const brigadePrefix = s.soldier_id.substring(0, 4)
    const key = `${brigadePrefix}:${s.full_name?.toLowerCase()}`
    if (!nameMap.has(key)) {
      nameMap.set(key, [])
    }
    nameMap.get(key)!.push(s.soldier_id)
  }

  // Return only entries with duplicates
  const duplicates = new Map<string, string[]>()
  for (const [, ids] of nameMap) {
    if (ids.length > 1) {
      for (const id of ids) {
        duplicates.set(id, ids.filter(x => x !== id))
      }
    }
  }

  return duplicates
}
