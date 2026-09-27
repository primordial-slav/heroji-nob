"""
Parser: 5. Kozaračka Krajiška NOU Brigada (brigade code 12).

Source: Lj. Borojević, D. Samardžija, R. Bašić — "PETA KOZARAČKA BRIGADA"
        znaci.org/00001/163_10.pdf  →  website/public/pdfs/5-kozaracka.pdf
Chapter: "SPISAK POGINULIH, NESTALIH I UMRLIH BORACA I RUKOVODILACA
          5. KRAJIŠKE (KOZARAČKE) NOU BRIGADE" — 53 pages, single column, Latin.

Entry format:
    ACIMOVIC MILORAD, borac, rođen 1921, u Suvom Dolu, Bijeljina, poginuo ...
    ADAMOVIC J. MILAN, borac, rođen u selu Vodičevo, ...
Father's name appears only as an occasional initial.

The OCR dropped most č/ć/ž/š/đ in names (ACIMOVIC, STARCEVIC); restore_diacritics
repairs name fields against the spellings already present in brigades 1-9.
Printer's signature marks ("17 Peta krajiška (kozaračka) brigada 257") are skipped.
"""
import re
from _parser_scaffold import restore_diacritics, run_parser

SIGNATURE_MARK = re.compile(r'^\d{1,2}\s+Peta krajiška \(kozaračka\) brigada\b', re.IGNORECASE)
P1_TITLE_BOTTOM_Y = 110   # chapter title block on p.1 ("SPISAK POGINULIH, NESTALIH ...")


def keep_line(ln: dict) -> bool:
    return not (ln['page'] == 1 and ln['y'] < P1_TITLE_BOTTOM_Y)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/5-kozaracka.pdf',
        brigade_code=12,
        output_path='website/public/5-kozaracka-soldiers.json',
        start_page=1,
        layout='single',
        script='latin',
        skip_re=SIGNATURE_MARK,
        line_filter=keep_line,
        post_fn=restore_diacritics,
    )
