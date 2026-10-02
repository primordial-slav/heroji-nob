// The same soldier's entry in another book of the unit (or another list in the same book): the name and text as
// printed there, and where it is (scripts/apply_corrections.py, action "merge")
export interface SoldierSource {
  soldier_id?: string     // the id the entry had before it was merged
  name?: string
  additional_info: string
  pdf_file?: string
  pdf_page?: number
  pdf_x?: number
  pdf_y?: number
  pdf_x_end?: number
  pdf_y_end?: number
  pdf_x_left?: number
  pdf_rects?: number[][]
  source_url?: string
  unit_file?: string      // set when the entry is another unit's: that unit's data file (the soldier served in both)
}

// A dated step of a soldier's life, read from his entries (scripts/extract_life_events.py): born, joined SKOJ or the
// KPJ, joined the NOB, came to the unit, a duty from a date, sent or transferred, wounded, ill, captured, exchanged,
// discharged, the death
export type LifeEventKind =
  | 'born' | 'skoj' | 'kpj' | 'nob' | 'unit' | 'duty' | 'moved' | 'wounded' | 'ill' | 'captured' | 'exchanged' | 'left'
  | 'death'

export interface LifeEvent {
  k: LifeEventKind
  d: string               // when: "1941", "1941-12" or "1941-12-22"
  e?: string              // the end of a period, in the same form
  at?: [number, number]   // where the entry prints it: start and end in its additional_info
  x?: string              // what it is about, as printed: a duty, a place, the unit he joined
  s?: number              // which entry (entriesOf): 0, left out, is the soldier's own
}

export interface Soldier {
  soldier_id: string
  last_name: string
  middle_name: string
  first_name: string
  additional_info: string
  fathers_name: string
  full_name: string
  birth_year: string
  unit?: string
  // Structured fields extracted from additional_info (optional - not all records have these)
  birth_place?: string
  ethnicity?: string
  occupation?: string
  rank?: string
  unit_detail?: string    // sub-unit info: battalion, company, platoon, etc.
  death_date?: string
  death_place?: string
  death_type?: string     // e.g. "poginuo", "umro"
  // PDF source position metadata (optional - may not be available for all records)
  pdf_page?: number       // 1-indexed page number in the source PDF
  pdf_y?: number          // Y of the entry's first line, in PDF points from page top
  pdf_x?: number          // X of the entry's first line, in PDF points from left edge
  // The entry's box on its page (data-extraction/entry_boxes.py), for the viewer's highlight
  pdf_y_end?: number      // bottom of the entry's last line on the page
  pdf_x_end?: number      // right edge of the entry's text
  pdf_x_left?: number     // left edge, only where it isn't pdf_x (e.g. only the first line is indented)
  pdf_rects?: number[][]  // a name in a run-on list that takes two lines: [left, top, right, bottom] of each
  pdf_file?: string       // Which PDF file (e.g., "prva-proleterska-2.pdf")
  // A source without a scan (a list published as a web page): where the entry can be read
  source_url?: string
  // The soldier's entries in the unit's other books (or lists); fields above that this entry leaves empty were
  // filled in from them
  other_sources?: SoldierSource[]
  // Set on the home page for a soldier linked across units: the other units he is listed in
  also_units?: string[]
  // The dated steps of his life, in order, where there are three or more (website/data/life-events/, merged in by
  // the records route)
  life_events?: LifeEvent[]
}
