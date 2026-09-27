"""
Parser stub: 1. Šumadijska Brigada.

Source: Isidor Ðuković — "PRVA ŠUMADIJSKA BRIGADA"
        znaci.org/00001/102_6.pdf  →  website/public/pdfs/1-sumadijska.pdf
Chapter: "SPISAK POGINULIH BORACA I STAREŠINA PRVE ŠUMADIJSKE BRIGADE"

Format observations:
- 58 pages, CYRILLIC. Complex "rich" biographic format.
- Sample entry (multi-line, one soldier per block):
    "АБАФИ Ћирила и Станиславе БРАНИСЛАВ (БРАНКО), политички
     комесар чете. Рођен 20. II 1923. године у Земуну. Матурант.
     Словак. Члан СКОЈ-а од 1939, а КПЈ од 1941. године. Ступио у
     1. шумадијски НОП одред 14. IV 1943 ..."
- BOTH parents' names given: "Ћирила и Станиславе" (of Ćiril and Stanislava).
- Nickname in parens after first name.
- Section headers by first letter: "А", "Б", ...
- After transliteration this becomes:
    "ABAFI Ćirila i Stanislave BRANISLAV (BRANKO), ..."
  → parse_standard_entry probably takes "Ćirila" as father's genitive, which is
    correct. Mother's name "Stanislave" will land in additional_info; add a
    post-processor to promote it into a `mothers_name` field if you want to
    surface it in the modal.

TODO:
  1. Confirm single-column.
  2. Skip section-header "А"/"Б"/... lines with skip_re.
  3. Consider adding `mothers_name` extraction to the parse function.
"""
import re
from _parser_scaffold import run_parser

# Cyrillic single-letter section headers, plus common preface strings
SKIP_RE = re.compile(r'^([A-ZА-Я])\s*$|^СПИСАК|^SPISAK', re.IGNORECASE)

if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/1-sumadijska.pdf',
        brigade_code=15,
        output_path='website/public/1-sumadijska-soldiers.json',
        start_page=2,            # p.1 is title
        end_page=None,
        layout='single',
        script='cyrillic',
        skip_re=SKIP_RE,
    )
