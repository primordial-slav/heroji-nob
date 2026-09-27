"""
Parser stub: 6. Krajiška NOU Brigada.

Source: Branko Damjanović, Savo Popović — "ŠESTA KRAJIŠKA NOU BRIGADA"
        znaci.org/00003/711_2.pdf  →  website/public/pdfs/6-krajiska.pdf
Chapter: "Spisak poginulih i umrlih boraca i starješina Šeste krajiške NOU brigade"

Format observations:
- 69 pages, Latin.
- p.1-2 = title + preface, actual list starts p.3 or so.
- Dense two-column body typical for VII-series krajiške brigade monographs.

TODO:
  1. Confirm data range (start ~3, end ~end).
  2. Measure column split x.
  3. Watch for section headers grouping by battalion or by fate ("Poginuli",
     "Umrli", "Nestali") that need skip_re.
"""
from _parser_scaffold import run_parser

if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/6-krajiska.pdf',
        brigade_code=13,
        output_path='website/public/6-krajiska-soldiers.json',
        start_page=3,
        end_page=None,
        layout='two_column',     # TUNE
        col_split_x=300,         # TUNE
        script='latin',
    )
