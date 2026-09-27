"""
Parser stub: 17. Slavonska Udarna Brigada.

Source: Zdravko B. Cvetković — "SEDAMNAESTA SLAVONSKA BRIGADA"
        Two PDFs concatenated in output:
          znaci.org/00001/131_9.pdf   →  17-slavonska-poginuli.pdf   (SPISAK POGINULIH)
          znaci.org/00001/131_10.pdf  →  17-slavonska-prezivjeli.pdf (SPISAK PREŽIVJELIH)

Format observations:
- Two-column, city/village grouped. Section headers are place names in ALL CAPS
  at the top of a column block: "BIJELJINA", "BELIŠĆE", ...
- Entries are terse:
    "BOSANAC M. BOŠKO, rođen 1914, Babinac —- poginuo 1943, Koprivnica"
- Middle initial with dot: "M." is father's initial.
- Some cities appear to split entries across columns awkwardly (peek shows
  "BIJELJINA BOSANAC M. BOŠKO..." on the left with "LEGINOVIĆ U. BRANKO"
  entry-start bleeding in from the right column).
- Preživjeli list has partial data (city + year only for many).

TODO:
  1. Detect and capture the current "city" as a `birth_place` field prefix
     attached to subsequent entries.
  2. Measure the column split — likely around x=310 given the peek.
  3. Combine poginuli and prezivjeli into one soldier list, tagging fate.
  4. Handle the "—-" or "—" separator between rođen and poginuo/preživio.
"""
import re
from _parser_scaffold import run_parser

# City headers are all-caps single tokens; sometimes "V.", "SI.", "M." are abbreviated prefixes.
# TODO: Distinguish city header (short, standalone) from entry-start (has surname+initial+firstname).

if __name__ == '__main__':
    # Pass poginuli, then prezivjeli.
    run_parser(
        pdf_path='website/public/pdfs/17-slavonska-poginuli.pdf',
        brigade_code=16,
        output_path='website/public/17-slavonska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        col_split_x=310,          # TUNE
        script='latin',
        additional_pdfs=[
            {'pdf_path': 'website/public/pdfs/17-slavonska-prezivjeli.pdf', 'start_page': 1, 'end_page': None},
        ],
    )
