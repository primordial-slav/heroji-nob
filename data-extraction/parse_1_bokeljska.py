"""
Parser: 1. bokeljska NOU brigada (brigade code 102).

Source: Dušan Živković, "Prva bokeljska NOU brigada" (znaci.org 00003/384.pdf, its pages 310-316, book pp. 315-321)
        →  website/public/pdfs/1-bokeljska.pdf. Latin, one column, numbered entries:
    "Spisak poginulih i umrlih boraca I bokeljske NOU brigade" (196), then "Nestali su u toku borbe" (5):
        21. Brehner N. Zvonimir, 1. bataljon, rođen u Dobroti — Kotor, poginuo na Ledenicama 15. 11. 1944. godine.
The book's roster of the brigade by unit before it ("Jedinični spisak", book pp. 291-314) is a scan without a text
layer and is not read. The text layer drops the carons of capitals at a word's start ("Sabović", "Curie" = Šabović,
Ćurić, which the list's Cyrillic order tells): put right from the spellings the other units print
(parse_8_kordunaska_divizija's helpers). The birthplace is the place after "rođen u" in the nominative the other
units know, with the municipality after the dash.
"""
import re
from itertools import product

import parse_8_kordunaska_divizija as k8
import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_section = {'missing': False}
# The list follows the Cyrillic order, so its last entries (after Ф and Ц) start with Ћ, Ч and Ш the text layer lost
CARONS = {'Curie': 'Ćurić', 'Ceprnjić': 'Čeprnjić', 'Sabović': 'Šabović', 'Serović': 'Šerović', 'Siljegović': 'Šiljegović',
          'Skero': 'Škero', 'Suberić': 'Šuberić'}


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/1-bokeljska-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if t.startswith('Nestali su'):
        _section['missing'] = True
        return False
    if re.fullmatch(r'[\d\W]{1,6}', t) or re.match(r'^(?:SPISAK|POGINULIH|I BOKELJSKE)', t):
        return False
    t = re.sub(r'^[a-z](?=\d{1,3}\.\s)', '', t)                                # "r97. Malavrazić"
    if re.match(rf'^\d{{1,3}}\.\s+[{U}][{L}]', t):
        t = ('§n§ ' if _section['missing'] else '§p§ ') + re.sub(r'^\d{1,3}\.\s+', '', t)
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    lst = text[1]
    text = re.sub(r'^§.§\s*', '', text)
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "Dreni- ci"
    head, _, info = text.partition(',')
    info = info.strip()
    if '(' in head and not info:                                             # "Grgurević (Vicka) Mato, rođen ..."
        head, _, info = text.partition(', ')
    father = ''
    paren = re.search(rf'\(([{U}][{L}]+)\)', head)
    if paren:
        father = paren.group(1)
        head = head[:paren.start()] + head[paren.end():]
    words = head.split()
    last = words.pop(0) if words else ''
    last = CARONS.get(last, last)
    if words and re.fullmatch(rf'[{U}][{L}]?\.', words[0]):
        father = words.pop(0)
    notes = ['zvani ' + ' '.join(words[1:])] if len(words) > 1 else []
    rec = _record(last, words[0] if words else '', father, '; '.join(notes + [info]))
    b = re.search(rf'\bro[đd]e?n[a]?\s+(?:u|na)\s+(?:selu\s+|mjestu\s+)?([{U}][{L}]+(?:\s+[{U}]?[{L}]+)?)(?:\s*—\s*([{U}][{L}]+(?:[\s-]+[{U}][{L}]+)?))?', info)
    if b:
        rec['_birth'] = (b.group(1), b.group(2) or '')
    rec['death_type'] = 'nestao' if lst == 'n' else (death_type_from_text(info) or 'poginuo')
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    soldiers = k8.post(soldiers)
    known = top._corpus()[0]

    def nominative(place: str) -> str:
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in place.split()))]
        forms = [f for f in forms if f != place and known[f] > known[place]]
        return max(forms, key=lambda f: known[f]) if forms else place

    for s in soldiers:
        birth = s.pop('_birth', None)
        if birth:
            place, muni = birth
            nom = nominative(place)
            muni = 'Herceg-Novi' if muni in ('Hercg-Novi', 'Herceg Novi') else muni
            if nom == place and re.search(r'(?:[^ć]i|u|ju|ama|ima)$', place):
                if muni and muni != 'Italija':
                    s['birth_place'] = muni                                  # "u Bijelićima — Herceg-Novi": the municipality
                continue
            s['birth_place'] = nom + (', ' + muni if muni and muni != nom else '')
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/1-bokeljska.pdf',
        brigade_code=102,
        output_path='website/public/1-bokeljska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§[pn]§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
