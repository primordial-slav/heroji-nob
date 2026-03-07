export interface Soldier {
  soldier_id: string
  last_name: string
  middle_name: string
  first_name: string
  additional_info: string
  fathers_name: string
  full_name: string
  birth_year: string
  pdf_page?: number
  pdf_y?: number
  pdf_x?: number
  pdf_file?: string
}

export interface SoldierSample {
  soldier: Soldier
  brigadeName: string
  brigadeCode: number
  flags: string[]
}

export interface Review {
  id: number
  soldier_id: string
  brigade_code: number
  status: 'issue' | 'correct' | 'dismissed'
  wrong_name: number
  merged_entries: number
  section_header: number
  wrong_birth_year: number
  fathers_name_wrong: number
  duplicate_record: number
  garbled_text: number
  other_issue: number
  description: string
  detection: 'suspicious' | 'random'
  flags_detail: string
  soldier_data: string
  created_at: string
}

export interface ReviewStats {
  total_soldiers: number
  total_reviewed: number
  issues: number
  correct: number
  dismissed: number
}

export const ISSUE_TYPES = [
  { key: 'wrong_name', label: 'Wrong name' },
  { key: 'merged_entries', label: 'Merged entries' },
  { key: 'section_header', label: 'Section header as soldier' },
  { key: 'wrong_birth_year', label: 'Wrong birth year' },
  { key: 'fathers_name_wrong', label: "Father's name wrong" },
  { key: 'duplicate_record', label: 'Duplicate record' },
  { key: 'garbled_text', label: 'Garbled/unreadable text' },
  { key: 'other_issue', label: 'Other' },
] as const

export type IssueTypeKey = typeof ISSUE_TYPES[number]['key']

export const FLAG_LABELS: Record<string, string> = {
  long_info: 'Long info (>200 chars)',
  mixed_case_lastname: 'Mixed case last name',
  empty_first_name: 'Empty first name',
  birth_year_mismatch: 'Birth year mismatch',
  fullname_mismatch: 'Full name mismatch',
  caps_in_info: 'ALL CAPS in additional_info',
  no_pdf_position: 'No PDF position',
  garbled_diacritics: 'Garbled diacritics',
  possible_header: 'Possible section header',
  duplicate_name: 'Duplicate name in brigade',
}
