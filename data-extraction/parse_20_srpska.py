"""
Parser: 20. srpska NOU brigada (brigade code 91).

Source: Dragoljub Ž. Mirčetić Duško, "20. srpska brigada" (znaci.org 00003/840.pdf, its pages 339-403, book
        pp. 321-385)  →  website/public/pdfs/20-srpska.pdf. Cyrillic, one column, a hanging indent:
    "Pregled poginulih i umrlih boraca i rukovodilaca", by letter:
        AGUŠEVIĆ Mladena VLADIMIR, 1906, Hum, Niš, kovač. ...
The same author and form as the 23. and 12. srpska's lists, read by parse_23_srpska. An entry that only refers to
another ("STAMENKOVIĆ Dragoljuba KOSTA — videti MARKOVIĆ-STAMENKOVIĆ Dragoljuba KOSTA") is left out.
"""
import re

import parse_23_srpska as p23
from _parser_scaffold import run_parser


U = p23.U


def keep(ln: dict) -> bool:
    """This book sets the first line of an entry in, not the rest (a first-line indent)."""
    t = ln['text'].strip()
    if ln['page'] == 1 or re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*', t):
        return False                                                         # the author's note; page numbers, letters
    t = re.sub(r'J1|JT(?=[A-ZČĆŽŠĐ])', 'L', t).replace('j1', 'l').replace('G1', 'P')  # Л read as J1 or JT, П as G1
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])0|0(?=[A-ZČĆŽŠĐ])', 'O', t)                  # "MIL0RAD"
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])JB(?=[A-ZČĆŽŠĐ])|^JB(?=[A-ZČĆŽŠĐ])', 'LJ', t).replace('JBO', 'ljo')   # Љ read as JB
    if ln['x'] >= p23.margin(ln) + 10 and re.match(rf'^[{U}A-Z0-9>]{{3,}}', t) and not re.match(r'^(?:NOVJ|NOP|SS\b|JNA)', t):
        t = '§p§ ' + p23.decode_head(t)
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    if re.search(r'(?i)\bvide(?:ti|gi)\b', text):
        return {'last_name': ''}                                             # a cross-reference, not a soldier
    return p23.parse(text)


def post(soldiers: list[dict]) -> list[dict]:
    """parse_23_srpska's repairs; here Ћ is also read as К or П at a surname's end ("JASKOVIK", "MILINOVIP")."""
    from _parser_scaffold import repair_cyrillic_ocr, restore_diacritics
    for s in soldiers:
        if re.search(r'[oe]vi[pk]$|i[pk]$', s['last_name']) and not s['last_name'].endswith(('nik', 'čik')):
            s['last_name'] = s['last_name'][:-1] + 'ć'
    soldiers = restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True))
    for s in soldiers:
        if s['last_name'].endswith('ii'):
            s['last_name'] = s['last_name'][:-1] + 'ć'
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/20-srpska.pdf',
        brigade_code=91,
        output_path='website/public/20-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=p23.prepare,
        line_filter=keep,
        post_fn=post,
    )
