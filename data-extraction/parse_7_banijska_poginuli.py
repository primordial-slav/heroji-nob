"""
Parser: 7. banijska brigada "Vasilj Gaćeša" (brigade code 44), second book: its fallen and dead of the whole war.

Source: Ljuban Đurić, *Sedma banijska brigada* (znaci.org 00001/63, the chapter 63_23.pdf, book pp. 394-462) →
website/public/pdfs/7-banijska-poginuli.pdf. "Nepotpuni spisak poginulih u ratu i umrlih pripadnika 7. banijske
brigade »Vasilj Gaćeša«", one column, alphabetical:
    ADAMOVIĆ Vase JOVO, rođen 1912, G. Mlinoga — Petrinja, Srbin, zemljoradnik, u NOVJ od 1942. (2. bataljon).
    Poginuo 1943. u bici na Sutjesci.
The surname in capitals, the father in small letters (or an initial), the given name in capitals, at times a
nickname after it ("ALUGA Koje BRANKO CICVARA"); the scan loses carons ("ADAMOVIC"), which the corpus gives back
(parse_8_kordunaska_divizija.post). The list's footnote on its first page is not read.

The unit's first book is its Borci Sutjeske chapter (parse_borci_sutjeske.py); these get 0044010001 on, and the same
man in both is merged (scripts/find_source_duplicates.py --brigade 44).
Usage: python data-extraction/parse_7_banijska_poginuli.py
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import run_parser

U = 'A-ZČĆŽŠĐ'


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}|[A-Za-z]', t) or re.match(r'^(?:\d\.\s*)?NEPOTPUNI SPISAK|^PRIPADNIKA 7\.', t):
        return False                                     # page numbers, specks, the list's title
    if ln['page'] == 1 and re.match(r'^1\s+[A-ZČĆŽŠĐ]', t) and ln['y'] > 600:
        return False                                     # the title's footnote
    head = t.split(',')[0]
    if (re.match(rf'^[{U}][{U}l1\-]{{1,}}(?=[\s,(])', t) and len(head.split()) >= 2
            and not re.match(r'^(?:NOVJ|NOV|NOB|KPJ|SKOJ|[IVX]{1,4})\b', t)):          # "IV ofanzive u Bosni"
        t = '§x§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    head, sep, rest = re.sub(r'^§x§\s*', '', text).partition(',')
    m = re.search(r'\s*—\s*([^—]+)$', head)
    if m and len(head[:m.start()].split()) >= 2:          # "GRUBOROVIĆ Đure STEVO — RADIĆ": the nickname
        head = f'{head[:m.start()]} »{m.group(1).strip()}«'
    rec = k8.parse_entry(head + sep + rest)
    rec.pop('unit_detail', None)                         # the 8. division's brigades: not this list's
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/7-banijska-poginuli.pdf',
        brigade_code=44,
        output_path='website/public/7-banijska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=k8.post,
        id_start=10001,
        keep_other_sources=True,
    )
