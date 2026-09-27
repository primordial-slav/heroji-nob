"""
Parser stub: 25. Srpska NOU Divizija.

Source: Milojica Pantelić — "25. SRPSKA NOU DIVIZIJA"
        znaci.org/00001/123_10.pdf  →  website/public/pdfs/25-srpska-divizija.pdf
Chapter: "Spisak poginulih boraca i rukovodilaca 25. Srpske divizije"

Format observations:
- 96 pages, CYRILLIC.
- NUMBERED entries — "1.", "2.", ... prefix each soldier:
    "1. ИВАНОВИЋ АЛЕКСАНДАР, борац 3. чете 2. батаљона 16. српске
     бригаде, рођен у селу Црквини код Крушевца, рањен 12. јула 1944.
     год. на Кривој букви у Топлици ..."
- Very narrative, one soldier per numbered paragraph, multi-line.
- No father's name. Includes: unit, rođen, ranjen date, poginuo date, mesto.
- This is a DIVISION book, so entries span multiple brigades within the
  division — capture `unit_detail` (which brigade / bataljon).

TODO:
  1. Use numbered entry-start regex, not the ALL-CAPS default:
       ENTRY_RE = r'^\d+\.\s+[A-ZČĆŽŠĐА-Я]{2,}\s+[A-ZČĆŽŠĐА-Я]+'
  2. Split "БОРАЦ N. ЧЕТЕ M. БАТАЉОНА K. СРПСКЕ БРИГАДЕ" out into unit_detail
     (rank + battalion + brigade) — this is where the division-level data adds
     value beyond a brigade-level list.
  3. Confirm single-column.
"""
import re
from _parser_scaffold import U, run_parser

# Numbered entry pattern (matched after Cyrillic → Latin): "1. LASTNAME FIRSTNAME"
NUMBERED_ENTRY = re.compile(rf'^\d+\.\s+[{U}]{{2,}}\s+[{U}][{U}\-]+')

if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/25-srpska-divizija.pdf',
        brigade_code=19,
        output_path='website/public/25-srpska-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=NUMBERED_ENTRY,
    )
