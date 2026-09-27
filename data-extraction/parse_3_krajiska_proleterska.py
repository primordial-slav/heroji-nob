"""
Parser stub: 3. Krajiška Proleterska Brigada.

Source: Savo Trikić — "TREĆA KRAJIŠKA PROLETERSKA BRIGADA"
        znaci.org/00001/224_18.pdf  →  website/public/pdfs/3-krajiska-proleterska.pdf
Chapter: "Spisak palih boraca 3. proleterske krajiške brigade s osnovnim
         matičnim podacima poginulih od 22. 8. 1942. do 15. 5. 1945."

Format observations (verify before running):
- 130 pages total, list starts on p.3 (p.1-2 = title + intro).
- Two-column Latin layout, entries flow alphabetically down each column.
- Standard "LASTNAME Fathers-genitive FIRSTNAME, rođen YEAR, ..." with rich
  bio: mesto, zanimanje, nacionalnost, u NOB od DATE, ulazak u Brigadu,
  fate (poginuo DATE mesto). Multi-line continuations common.
- Column split appears near x≈300 based on similar VII-series layouts;
  measure before wiring the real parser.

TODO:
  1. Confirm start/end pages + column split X.
  2. Add city/section-header skip patterns if present.
  3. Test parse_standard_entry against samples; adapt if needed.
"""
from _parser_scaffold import run_parser

if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/3-krajiska-proleterska.pdf',
        brigade_code=10,
        output_path='website/public/3-krajiska-proleterska-soldiers.json',
        start_page=3,
        end_page=None,           # auto-detect end
        layout='two_column',
        col_split_x=300,         # TUNE: verify with a peek
        script='latin',
    )
