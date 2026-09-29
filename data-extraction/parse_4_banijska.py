"""
Parser: 4. Banijska NOU Brigada (brigade code 20).

Source: "ČETVRTA BANIJSKA NOU BRIGADA — Zbornik sjećanja", chapter "Spisak boraca"
        znaci.org/00001/188_4.pdf  →  website/public/pdfs/4-banijska.pdf
Single column, Latin. p.1 title, pp. 2-51 one alphabetical list with a capital letter heading per
letter group, pp. 52-53 the book's table of contents.
    ADAMOVIĆ Petra JANKO, rođen 1919. u Segestinu (Dvor na Uni)
    AKIK J. STOJAN, rođen 1922. u Udetinu (Dvor na Uni)
    GRUBOR Gojko, rođen u Primišlju (Slunj).          (given name not in caps)
    VUJIČIĆ Jove MILAN — SNJACO, rođen 1924. ...        (nickname after a dash)
    MIKULIN (ili MIŠKULIN) JAKOV, rođen u Praćnom.
    ANDREJ, rodom iz SSSR                              (one name only: Soviet volunteers, nicknames)
    CA VIĆ Janka STOJAN, ...                           (OCR split the surname: ČAVIĆ)
Continuation lines are indented ~16pt, so entries start at the left margin (_margin_entries).
"""
import json
import re
from collections import Counter

from _margin_entries import MarginEntries, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

U = 'A-ZČĆŽŠĐ'
LETTER_HEADING = re.compile(rf'^[{U}]{{1,2}}$')
TOC_LINE = re.compile(r'(?:—\s*){2,}|_\s*_|^Strana$|^S A D R Ž')
me = MarginEntries()


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if LETTER_HEADING.match(t) or TOC_LINE.search(t) or re.fullmatch(r'[•.\s]*\d{3}', t):
        return False
    return me.mark(ln)


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '6-krajiska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = split_leading_aliases(repair_lj_ocr(restore_diacritics(soldiers)))
    return lone_names_to_given(soldiers, *name_counts())


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-banijska.pdf',
        brigade_code=20,
        output_path='website/public/4-banijska-soldiers.json',
        start_page=2,
        end_page=51,
        layout='single',
        script='latin',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
