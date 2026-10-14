"""
Parser: Prva proleterska brigada (brigade code 1), its Rudarska četa (the Trepča miners' company): the company at Rudo.

Source: Branislav Božović, *Rudarska četa* (znaci.org 00003/748, the whole book's PDF pp. 426-430: "Spisak boraca
Rudarske čete Prve proleterske - sastav u Rudom 21. XII 1941") → website/public/pdfs/rudarska-ceta.pdf. Numbered,
one column, a bio each:
    1. SIMOVIĆ MILAN ZEKA komandir čete i zamenik komandanta bataljona, rođen 3. februara 1917, Vitkovac, Kraljevo, ...
The surname and the given name in capitals, a nickname in capitals after them at times, then the duty and the bio
(the book's own text, not separated by a comma). These get 0001600001 on (the brigade's other books: 0001000001- to
0001500001-), and the same man in the brigade's other lists, the line-up at Rudo above all, is merged
(scripts/find_source_duplicates.py --brigade 1).
Usage: python data-extraction/parse_rudarska_ceta.py
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}lI1\-]+'
DUTY = (r'(?:borac|komandir|zamenik|vodnik|desetar|politički|delegat|kurir|bolničar\w*|puškomitraljezac|mitraljezac|'
        r'intendant|ekonom|komesar|sekretar|ordonans|bombaš)')


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}', t) or re.match(r'^(?:SPISAK BORACA|— Sastav u Rudom|-\s*Sastav)', t):
        return False
    if re.match(rf'^\d{{1,2}}\.\s*{CAPS}', t):
        t = '§x§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    t = re.sub(r'^§x§\s*\d{1,2}\.\s*', '', text)
    t = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', t)
    m = re.match(rf'^((?:{CAPS}\s*){{2,4}}?)\s*(?={DUTY}\b)', t)
    head, bio = (m.group(1).strip(), t[m.end():].strip()) if m else (t.split(',')[0], t[len(t.split(',')[0]) + 1:].strip())
    words = [k8.caps_word(w) for w in head.split()]
    last, given = words[0].title(), (words[1].title() if len(words) > 1 else '')
    nick = ' '.join(w.title() for w in words[2:])
    info = (f'zvani {nick}; ' if nick else '') + bio
    rec = _record(last, given, '', info)
    y = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s+\w+\s+)?(1[89]\d\d)', bio)
    rec['birth_year'] = y.group(1) if y else ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/rudarska-ceta.pdf',
        brigade_code=1,
        output_path='website/public/prva-proleterska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=k8.post,
        id_start=600001,
        keep_other_sources=True,
    )
