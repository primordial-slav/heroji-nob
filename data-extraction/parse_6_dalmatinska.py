"""
Parser: 6. dalmatinska udarna brigada (brigade code 103).

Source: Danilo Damjanović, "Šesta dalmatinska udarna brigada" (znaci.org 00001/105_7.pdf, its pages 3-15, book pp.
        259-271)  →  website/public/pdfs/6-dalmatinska.pdf. Latin, two columns, every line flush left, by letter:
    Prilog 2, "Spisak poginulih boraca", the name in capitals:
        BABIĆ Đ. RADIŠA, iz Žegara, poginuo u borbi za Knin 30. XI 1944. god.
The scan loses carons and reads I as l, Ž as 2 and J as .T ("DRCA .TANKO"); names are put right from the spellings
the other units print (parse_8_kordunaska_divizija's helpers). The birthplace is the place after "iz" in the
nominative the other units know ("iz Tetova" = Tetovo). The list of the command (Prilog 1) is not read.
"""
import re
from itertools import product

import parse_8_kordunaska_divizija as k8
import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/6-dalmatinska-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*|\d+\*?', t) or re.match(r'^(?:SPISA|POGINULIH|BORACA|Prilog)', t):
        return False                                                         # headings, letters, page numbers
    if ln['page'] == 1 and ln['y'] > 460 and ln['x'] < 150:
        return False                                                         # the editors' note under the first column
    if re.match(rf'^[{U}2.]', t):                                            # the name only: "BAD2A" = BADŽA, ".TANKO" = JANKO
        head, sep, rest = t.partition(',')
        head = re.sub(r'(?<![A-Za-z])\.T(?=[A-Z]{2})', 'J', head).replace('2', 'Ž')
        head = re.sub(r'(?<=[A-ZČĆŽŠĐ])\.T(?=[A-Z])', 'J', head)                   # "MI.TO" = MIJO
        head = re.sub(r'(?<=[A-ZČĆŽŠĐ])\.(?=[A-ZČĆŽŠĐ])', '', head)                # "BRAL.JA" = BRALJA
        head = head.replace('MTL.TENKO', 'MILJENKO').replace('MTLJENKO', 'MILJENKO')   # T read for I
        t = head + sep + rest
    if re.match(rf'^[{U}][{U}lŽ ]+(?:\s[{U}]\.\s*)?\s*[{U}lŽ]{{2,}}\s*[,.]', t) or re.match(rf'^[{U}][{U}lŽ]{{2,}}\s+[{U}][{U}lŽ]{{2,}}\s*[,.]', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "Kule At- lagića"
    head, info = (re.split(r'[,.]\s+(?=(?:iz|sa|od)\s|poginu|umr)', text, 1, flags=re.I) + [''])[:2]
    words = head.split()
    init = [i for i, w in enumerate(words) if re.fullmatch(rf'[{U}]\.', w)]
    father = ''
    if init:
        father = words[init[0]]
        last_parts, given_parts = words[:init[0]], words[init[0] + 1:]
    elif len(words) == 3 and k8.known(words[1], 'middle_name') > k8.known(words[0] + words[1], 'last_name'):
        father, last_parts, given_parts = words[1].title(), words[:1], words[2:]   # "FILIPOVIC ILIJE JANKO"
    else:
        last_parts, given_parts = words[:-1], words[-1:]
    last = k8.join_parts([k8.caps_word(w) for w in last_parts], 'last_name')
    given = k8.join_parts([k8.caps_word(w) for w in given_parts], 'first_name').title()
    given = given.rstrip('.')
    rec = _record(last.rstrip('.'), given, father, info.strip())
    b = re.match(rf'iz\s+([{U}][{L}]+(?:[\s-]+[{U}]?[{L}]+)?)', info.strip())
    if b:
        rec['_birth'] = b.group(1)
    rec['death_type'] = death_type_from_text(info) or 'poginuo'
    d = re.search(rf'(?:poginu\w*|umr\w*|ubijen\w*|strijelj\w*)\s+(?:u\s+borbi\s*,?\s*|na\s+položaju\s+)?(?:za|kod|na|u|pri)\s+'
                  rf'([{U}][{L}]+(?:\s+(?:[{U}][{L}]+|kod|na)){{0,3}})\s*,?\s*(\d{{1,2}}\.\s*[IVX]+\.?\s*19\d\d)', info)
    if d:
        rec['death_date'] = re.sub(r'\s+', ' ', d.group(2))
        rec['_death_at'] = d.group(1)
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
        at = s.pop('_death_at', None)
        if at:                                                               # "za Rijeku", "kod Knina": the nominative where known
            s['death_place'] = nominative(at)
        place = s.pop('_birth', None)
        if place:
            nom = nominative(place)
            if nom != place or not re.search(r'(?:a|e|i|ja|ca|ova|eva)$', place):
                s['birth_place'] = nom                                       # "iz Tetova" = Tetovo; a genitive no unit knows stays out
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/6-dalmatinska.pdf',
        brigade_code=103,
        output_path='website/public/6-dalmatinska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=lambda p, s, e: columns_reader(2)(p, s, e),
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
