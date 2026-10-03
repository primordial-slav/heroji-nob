"""
Parser: 6. crnogorska udarna brigada (brigade code 106).

Source: "Šesta crnogorska narodnooslobodilačka udarna brigada — zbornik sjećanja" (znaci.org 00003/537.pdf, its pages
        857-872, book p. 871 on)  →  website/public/pdfs/6-crnogorska.pdf. Cyrillic, one column, a hanging indent:
    "Poginuli borci i starješine brigade" (with those who died of wounds or illness, the editors' note), by letter:
        АГРАМОВИЋ Милосава ВУКАШИН, рођен 1926. у Штедиму — Никшић, борац 1. чете 1. батаљона, заробљен и
        стријељан 29. априла 1944. године у Доњем Загарачу — Даниловград.
The father in the genitive (normalize puts it in the nominative); a few entries added after the letter Š. znaci.org
re-typeset the book from its OCR, so the page shows the text layer's slips: Л as Ј1 ("ВЈ1АГОЈЕВИЋ"), Н as И
("ИИКОЈ1А" = Nikola); names are put right from the spellings the other units print.
"""
import re

from _parser_scaffold import DEFAULT_ENTRY_START, parse_standard_entry, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}', t) or re.match(r'^POGINULI BORCI I STARJEŠINE', t):
        return False                                                         # the title, a stray bracket
    if t.startswith('*)') or (ln['page'] == 1 and re.match(r'^bolesti takođe', t)):
        return False                                                         # the editors' note under the first page
    t = t.replace('J1', 'L').replace('j1', 'l')                             # Л read as Ј1: "VJ1AGOJEVIĆ" = Vlagojević
    t = t.replace('JB', 'LJ')                                                # Љ read as Јб: "DRJBEVIĆ" = Drljević
    t = re.sub(rf'^([{U}-]{{3,}})\s+(\((?:rođena|udata)[^)]*\))\s+([{U}-]{{3,}}),', r'\1 \3, \2,', t)   # "DRLJEVIĆ (rođena Radović) JELA"
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    text = re.sub(rf'^([{U}]+)\s*[—–-]\s*([{U}]+)(?=\s)', r'\1-\2', text)     # "ŠUŠOVIĆ-RADETIĆ"
    return parse_standard_entry(text)


# The text layer's slips that the page shows too, put right from the list's order and the spellings of other units:
# Б read as Г or В, Н as К, a lost И, Ђ as Ћ.
NAMES = {'Agramović': 'Abramović', 'Vlagojević': 'Blagojević', 'Kikolić': 'Nikolić', 'Ajšć': 'Ajšić', 'Đuraškovmć': 'Đurašković'}
FIRST = {'Ćorđije': 'Đorđije', 'Iikola': 'Nikola'}


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_cyrillic_ocr(soldiers)                                 # "PETAR-PERO" stays as printed
    for s in soldiers:
        s['last_name'] = NAMES.get(s['last_name'], s['last_name'])
        s['first_name'] = FIRST.get(s['first_name'], s['first_name'])
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/6-crnogorska.pdf',
        brigade_code=106,
        output_path='website/public/6-crnogorska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=DEFAULT_ENTRY_START,
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
    )
