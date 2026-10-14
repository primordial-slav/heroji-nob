"""
Parser: 7. crnogorska omladinska brigada "Budo Tomović" (brigade code 28), second book — the zbornik's list of the
fallen.

Source: *Sedma crnogorska omladinska brigada "Budo Tomović" - zbornik sjećanja* (znaci.org 00003/471), "Poginuli borci
        i starješine brigade", PDF pp. 696-718 → website/public/pdfs/7-crnogorska-zbornik-poginuli.pdf
One column, Cyrillic, each entry hanging:
    "АВДИЋ Хајрудинов ЋАЗИМ, рођ. 1926. у Бишеву, Рожаје, 1. чета 4. батаљона, погинуо 24. јануара 1945. на
     Сјенокосу код Горажда."
(the father as a possessive; some without one, "БАБИЋ ДАНИЈЛО"; a few with "родом из ..." for the birth). The unit's
first book (Đurišić's table of 439) prints the same men: the records are merged by find_source_duplicates.
Usage: python data-extraction/parse_7_crnogorska_zbornik.py [--dry]
"""
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _parser_scaffold import run_parser  # noqa: E402

PDF = HERE.parent / 'website' / 'public' / 'pdfs' / '7-crnogorska-zbornik-poginuli.pdf'
# names the page itself prints garbled (znaci re-typeset it from its OCR: Л as "J1", Љ as "JБ", И as "Р1"), read
# back from the unit's first book, which has the same men ("Golubović Ljubo, 1924, Buče", "Pajković Milija, 1927, Lužac")
NAMES = {('Goj1ubović', 'Jbubo'): ('Golubović', 'Ljubo'), ('Pajkovr1ć', 'Milija'): ('Pajković', 'Milija')}


def fix_names(soldiers: list[dict]) -> list[dict]:
    """The names the page garbles (NAMES); the father the book gives as a possessive ("Antov", "Milijin") also in the
    nominative the site's given names know (Anto, Milija), as fathers_name, so that it agrees with the first book's
    genitive ("Anta", "Milije") and normalization keeps it"""
    import build_ostali_borci as bob
    if not bob._given:
        bob.given_names()
    for s in soldiers:
        fixed = NAMES.get((s['last_name'], s['first_name']))
        if fixed:
            s['last_name'], s['first_name'] = fixed
            s['full_name'] = f'{fixed[0]} {fixed[1]}'
        father = bob.from_possessive(s.get('middle_name') or '')
        if father:
            s['fathers_name'] = father
        born = re.search(r'\bro[dđ]\.?\s*(1[89]\d\d)', s.get('additional_info') or '')       # "rođ. 1926."
        if born and not s.get('birth_year'):
            s['birth_year'] = born.group(1)
    return soldiers
SOURCE = HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_471.pdf'          # znaci.org/00003/471.pdf
OUTPUT = HERE.parent / 'website' / 'public' / '7-crnogorska-soldiers.json'


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(SOURCE), fitz.open()
        out.insert_pdf(src, from_page=695, to_page=717)
        out.save(PDF, garbage=4, deflate=True)


if __name__ == '__main__':
    build_pdf()
    dry = '--dry' in sys.argv
    run_parser(
        pdf_path=str(PDF),
        brigade_code=28,
        output_path=str(Path(sys.argv[sys.argv.index('--dry') + 1]) if dry else OUTPUT),
        script='cyrillic',
        post_fn=fix_names,
        id_start=10001,
        keep_other_sources=not dry,
    )
