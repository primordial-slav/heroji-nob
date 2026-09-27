"""
Parser stub: 8. Krajiška NOU Brigada.

Source: Izudin Čaušević — "OSMA KRAJIŠKA NOU BRIGADA"
        znaci.org/00001/146_7.pdf  →  website/public/pdfs/8-krajiska.pdf
Chapter: "Spisak poginulih i umrlih u toku NOR-a iz 8. Krajiške brigade"

Format observations:
- 63 pages, Latin.
- Distinctive father-in-parens format:
    "ABDIHODŽIĆ (R) ASIM, rođen 1929, Bihać, umro maja 1943. od pjegavog tifusa."
- The (R) is father's initial, not middle name. parse_standard_entry handles this.
- Some entries have full first name only, no parens: "ADAMOVIĆ SAVO, rođen..."
- Two-word compound first names: "ADAMOVIĆ STEVAN - Stevo, rođen..."

TODO:
  1. Confirm single-column (looks like it).
  2. Handle "STEVAN - Stevo" nickname pattern (dash-separated); may want to
     store nickname separately.
"""
from _parser_scaffold import run_parser

if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/8-krajiska.pdf',
        brigade_code=14,
        output_path='website/public/8-krajiska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
    )
