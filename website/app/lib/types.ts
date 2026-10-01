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
  source_url?: string
  unit_file?: string      // set when the entry is another unit's: that unit's data file (the soldier served in both)
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
  pdf_file?: string       // Which PDF file (e.g., "prva-proleterska-2.pdf")
  // A source without a scan (a list published as a web page): where the entry can be read
  source_url?: string
  // The soldier's entries in the unit's other books (or lists); fields above that this entry leaves empty were
  // filled in from them
  other_sources?: SoldierSource[]
  // Set on the home page for a soldier linked across units: the other units he is listed in
  also_units?: string[]
}
