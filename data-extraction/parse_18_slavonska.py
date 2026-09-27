"""
Parser stub: 18. Slavonska Udarna Brigada.

Source: Rade Roksandić, Zdravko B. Cvetković — "18. SLAVONSKA BRIGADA"
        znaci.org/00001/101_5.pdf  →  website/public/pdfs/18-slavonska.pdf
Chapter: "SPISAK POGINULIH I UMRLIH BORACA I RUKOVODILACA 18. UDARNE BRIGADE"

Format observations:
- 66 pages, Latin.
- **TABLE FORMAT** (unique among the current batch):
    | Prezime i ime          | Datum i mjesto rođenja | gdje je poginuo    |
    | Aga Baja                | 11. 8. 1921. Toplice   | 26. 10. 1944. Lađevac, Zaječar |
- pdfplumber `extract_words()` will collapse this into single-column reading
  order and lose the column boundaries. Must use `page.extract_tables()` or
  detect column x-boundaries and split manually.
- Firstname may span two rows (surname on row 1, given name on row 2).

TODO:
  1. Do NOT reuse run_parser() as-is — table extraction differs. Consider:
     - Use pdfplumber's table extraction with detect_table settings.
     - Or manually detect the three column x-ranges from the first data page.
  2. Handle multi-row entries (surname / firstname on adjacent rows sharing y).
  3. Map columns:
     - col 1: "Aga Baja" → last_name=Aga, first_name=Baja (or father-first-name)
     - col 2: birth date + place
     - col 3: death date + place

This parser will need a custom function; the run_parser scaffold is left here
as a starting point but likely needs to be replaced with a table-aware version.
"""
from _parser_scaffold import run_parser

if __name__ == '__main__':
    # WARNING: table layout — the default line-based extractor will produce
    # garbled output. Replace this call with a table-extraction routine before
    # trusting the output. Left in as a smoke test to see what current output
    # looks like.
    run_parser(
        pdf_path='website/public/pdfs/18-slavonska.pdf',
        brigade_code=17,
        output_path='website/public/18-slavonska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
    )
