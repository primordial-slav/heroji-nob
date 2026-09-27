"""
Parser stub: 4. Krajiška NOU Brigada.

Source: Rade Zorić — "ČETVRTA KRAJIŠKA NOU BRIGADA"
        znaci.org/00001/94_5.pdf  →  website/public/pdfs/4-krajiska.pdf
Chapter: "SPISAK POGINULIH BORACA"

Format observations:
- 131 pages, CYRILLIC. Data starts on p.2 (p.1 = title page).
- Sample entry (raw):
    "АБАЏИЋ Етхема НАСИХ, борац 2. батаљона, рођен 1926, Паланка,
     Брчко, Муслиман, трговац, у НОБ од 13. IV 1945, погинуо
     27. IV 1945. код села Херцеговца, Грубишно Поље."
- Very rich bio: unit → year → mesto → nationality → occupation → NOB date → fate.
- Likely single-column but confirm — VII-series is often two-column even in Cyrillic.

TODO:
  1. Confirm single- vs two-column.
  2. Confirm the Cyrillic→Latin transliteration handles all diacritics correctly
     (`Ђ→Đ`, `Ћ→Ć`, `Џ→Dž` — Џ is uppercase-double so parse_standard_entry may
     misread it as two words).
  3. If layout='two_column', measure col_split_x.
"""
from _parser_scaffold import run_parser

if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-krajiska.pdf',
        brigade_code=11,
        output_path='website/public/4-krajiska-soldiers.json',
        start_page=2,
        end_page=None,
        layout='single',         # TUNE: possibly 'two_column'
        script='cyrillic',
    )
