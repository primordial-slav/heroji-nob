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
  pdf_y?: number          // Y coordinate in PDF points from page top
  pdf_x?: number          // X coordinate in PDF points from left edge
  pdf_y_end?: number      // Y coordinate of the next entry (for highlight height)
  pdf_file?: string       // Which PDF file (e.g., "prva-proleterska-2.pdf")
}
