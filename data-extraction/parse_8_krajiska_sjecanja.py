"""
Parser: 8. krajiška brigada (brigade code 14), second book — the fallen and dead from *Osma krajiška brigada -
sjećanja boraca*.

Source: znaci.org/00001/68 (the eighth part, 68_9.pdf), "Spisak poginulih i umrlih u toku NOR-a iz 8. krajiške
        brigade", PDF pp. 1-24 (book pp. 689-739) → website/public/pdfs/8-krajiska-sjecanja-poginuli.pdf
Two columns on landscape pages, each entry hanging, the father's initial in brackets:
    "ALAGIĆ (D) MUHAREM, rođen 1920, Bihać, poginuo marta 1943. na planini Šator."
The book's "Spisak ispravki za monografiju" after it (corrections to Čaušević's monograph, the unit's first book) is
not read. The monograph lists the same men: the records are merged by find_source_duplicates.
Usage: python data-extraction/parse_8_krajiska_sjecanja.py [--dry out.json]
"""
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
from _parser_scaffold import run_parser  # noqa: E402

U = 'A-ZČĆŽŠĐ'


def prepare(lines: list[dict]) -> None:
    """The OCR's 2 for Ž and a small letter inside a name in capitals ("KRD2ALIČ", "POPR2ENOVIĆ", "STEvKOVIČ"): read
    back, else the name starts no entry and is glued to the one before"""
    for ln in lines:
        ln['text'] = re.sub(rf'(?<=[{U}])2(?=[{U}])', 'Ž', ln['text'])
        ln['text'] = re.sub(rf'(?<=[{U}]{{2}})v(?=[{U}]{{2}})', 'V', ln['text'])


def carons(soldiers: list[dict]) -> list[dict]:
    """Surnames that lost their caron ("Abdic", "Adamovic"): the spelling the site's records know (Abdić, Adamović)"""
    import _karlovac_lists as kl
    import parse_ofanziva_1942 as ofz
    if not ofz._spell['last']:
        ofz.corpus()
    for s in soldiers:
        if re.search(r'[cC]$|[cszCSZ][a-z]', s['last_name']):
            fixed = '-'.join(kl.spelled(p.upper(), 'last') for p in s['last_name'].split('-'))
            if fixed.lower().replace('ć', 'c').replace('č', 'c').replace('š', 's').replace('ž', 'z').replace('đ', 'd') == \
                    s['last_name'].lower().replace('ć', 'c').replace('č', 'c').replace('š', 's').replace('ž', 'z').replace('đ', 'd'):
                s['last_name'] = fixed
                s['full_name'] = f"{fixed} {s['first_name']}".strip()
    return soldiers

PDF = HERE.parent / 'website' / 'public' / 'pdfs' / '8-krajiska-sjecanja-poginuli.pdf'
SOURCE = HERE / '.cache' / '8-krajiska' / '68_9.pdf'                  # znaci.org/00001/68_9.pdf
OUTPUT = HERE.parent / 'website' / 'public' / '8-krajiska-soldiers.json'


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(SOURCE), fitz.open()
        out.insert_pdf(src, from_page=0, to_page=23)
        out.save(PDF, garbage=4, deflate=True)


if __name__ == '__main__':
    build_pdf()
    dry = '--dry' in sys.argv
    run_parser(
        pdf_path=str(PDF),
        brigade_code=14,
        output_path=str(Path(sys.argv[sys.argv.index('--dry') + 1]) if dry else OUTPUT),
        layout='two_column',
        col_split_x=455,               # landscape pages: the left column ends by x 412, the right begins at 500
        prepare_fn=prepare,
        post_fn=carons,
        id_start=10001,
        keep_other_sources=not dry,
    )
