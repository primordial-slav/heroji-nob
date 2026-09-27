"""
Parser: 2. Vojvođanska NOU Brigada (brigade code 18).

Source: Žarko Atanacković — "DRUGA VOJVOĐANSKA NOU BRIGADA"
        znaci.org/00001/72_14.pdf  →  website/public/pdfs/2-vojvodjanska.pdf
Chapter: "4. Spisak boraca 2. vojvođanske brigade" — book pp. 396-530,
         PDF pages 1-135 (136-137 are "Beleška o piscu"). Single column, Cyrillic.

Entry format (after transliteration):
    AVAKUMOVIĆ. STEVANA VUKAŠIN,* rođen 1919, Divoš, Sremska Mitrovica, ...
    AVRAMOVIĆ. B. BOGOLJUB, rođen 1919, Jarak, ...
    ARBANOVSKI (ĆOSIĆ) PAJE DANICA, rođena 1923, ...     ← maiden name
Footnote on p.1: "* Oznaka poginulih i umrlih." → for starred entries, death_type is
taken from the entry text (poginuo / umro / ...).
"""
import re
from _parser_scaffold import run_parser

SIGNATURE_MARK = re.compile(r'^\d{1,2}\s+Druga vojvođanska NOU brigada\b', re.IGNORECASE)
P1_FOOTNOTE_Y = 455   # p.1 footnote block ("1 Ovo je spisak boraca ...") starts here


def keep_line(ln: dict) -> bool:
    return not (ln['page'] == 1 and ln['y'] >= P1_FOOTNOTE_Y)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/2-vojvodjanska.pdf',
        brigade_code=18,
        output_path='website/public/2-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=135,
        layout='single',
        script='cyrillic',
        skip_re=SIGNATURE_MARK,
        line_filter=keep_line,
        asterisk_marks_death=True,
    )
