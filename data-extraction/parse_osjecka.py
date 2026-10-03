"""
Parser: Osječka udarna brigada (brigade code 104).

Source: Zdravko B. Cvetković, "Osječka udarna brigada" (znaci.org 00003/450.pdf, its pages 202-249, book pp. 207-254)
        →  website/public/pdfs/osjecka.pdf. Latin, one column, a hanging indent, under the names of municipalities:
    pp. 1-12    VI, "Spisak poginulih i umrlih boraca Osječke brigade", by the municipality they came from:
                    DARUVAR
                    CUCA Rade MILAN, rođen u s. Potočani, Daruvar, poginuo 1944.
    pp. 13-48   VII, "Spisak preživjelih boraca Osječke brigade", by the municipality they were born in (the
                author's note), often the name alone:
                    BARI Franje STJEPAN, rođen 1904. u s. Rajno Polje (umro poslije rata).
A municipality's name stands alone in capitals, a gap above and below it; a name alone in capitals ("KUČAN DRAGO") is
an entry. Of the survivors, "umro poslije rata" marks one who has died since. The list of the brigade's leaders
before them (V, book pp. 203-206) is not read. Names are put right from the spellings the other units print
(parse_8_kordunaska_divizija's helpers).
"""
import re
from itertools import product

import parse_8_kordunaska_divizija as k8
import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SURVIVORS_FROM = 13
_ys: dict = {}
_muni = {'name': ''}
_note: dict = {}


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/osjecka-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _ys.setdefault(ln['page'], []).append(ln['y'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|V|VI|VII', t) or re.match(r'^(?:SPISAK|OSJEČKE BRIGADE)', t):
        return False
    if re.match(r'^32[12]\s+[A-Z]', t) or _note.get(ln['page']):
        _note[ln['page']] = True                                             # the author's footnotes at the foot of the page
        return False
    ys = sorted(_ys[ln['page']])
    i = ys.index(ln['y'])
    above = ln['y'] - ys[i - 1] if i else 99
    below = ys[i + 1] - ln['y'] if i + 1 < len(ys) else 99
    if re.fullmatch(rf'[{U}]+(?:[ -][{U}]+)*\.?', t) and above > 12 and below > 12:
        _muni['name'] = t.rstrip('.').title()                                # "NOVI SAD": the municipality
        return False
    lst = 'r' if ln['page'] >= SURVIVORS_FROM else 'p'
    t = t.replace('2', 'Ž') if re.match(r'^2[A-Z]', t) else t                # "2DERIĆ MILENKO"
    if re.match(rf'^[{U}][{U}l]+(?:\s+[{U}][{U}l]+)?\s+(?:[{U}][{L}]+\s+|[{U}]\.\s*)?[{U}][{U}l]+\b', t):
        t = f'§{lst}§{_muni["name"]}§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    lst = text[1]
    muni = text[3:text.index('§', 3)]
    text = text[text.index('§', 3) + 1:].strip()
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "pogi- nuo"
    head, info = (re.split(r',|\.\s+(?=[Rr]o[đd]en)', text, 1) + [''])[:2]   # "GOIĆ Vase MILE. Rođen"
    info = info.strip()
    words = head.split()
    caps = []
    while words and re.fullmatch(rf'[{U}][{U}l]+', words[0]):
        caps.append(words.pop(0))
    father = words.pop(0) if words and re.fullmatch(rf'(?:[{U}][{L}]+|[{U}]\.)', words[0]) and \
        any(re.fullmatch(rf'[{U}][{U}l]+', w) for w in words[1:]) else ''
    given = [w for w in words if re.fullmatch(rf'[{U}][{U}l]+', w)]
    nick = [w for w in words if not re.fullmatch(rf'[{U}][{U}l]+', w)]
    if father and given:
        pass
    elif len(caps) >= 2 and not given:
        given = caps[-1:]                                                    # "BOROŠ ĐURO": no father
        caps = caps[:-1]
    if len(given) > 1:
        nick = given[1:] + nick                                              # "SERTIĆ FRANJO BIJELI"
        given = given[:1]
    last = k8.join_parts([k8.caps_word(c) for c in caps], 'last_name')
    notes = ['zvani ' + ' '.join(w.title() for w in nick)] if nick else []
    rec = _record(last, k8.caps_word(given[0]).title() if given else '', father, '; '.join(notes + [info] * bool(info)))
    y = re.search(r'\bro[đd]en[a]?\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)', info)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.search(rf'\bro[đd]en[a]?\s+(?:[\d.\s]*1[89]\d\d[.,]?\s*)?(?:u\s+)?(?:s\.\s*)?((?:[{U}]\.\s*)?[{U}][{L}]+(?:\s+[{U}]?[{L}]+)?)'
                  rf'(?:\s*,\s*((?:[{U}][{L}]*\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)?))?', info)
    if b:
        rec['_birth'] = (b.group(1), b.group(2) or muni, bool(re.search(r'\bu\s+s\.', info)))   # both lists go by birthplace
    if lst == 'p':
        rec['death_type'] = death_type_from_text(info) or 'poginuo'
    elif re.search(r'\b(?:umr[lo]a?|poginuo)\b[^)]*\b(?:poslije|posle)\s+rata|\bpoginuo u saobraćajnom', info):
        rec['death_type'] = 'umro'                                           # a survivor who has died since
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
            place, muni, village = birth
            nom = place if village else nominative(place)                    # "u s. Uljanik" as printed, "u Daruvaru" = Daruvar
            if nom == place and not village and re.search(r'(?:u|ju|i)$', place):
                continue
            s['birth_place'] = nom + (', ' + muni if muni and muni != nom else '')
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/osjecka.pdf',
        brigade_code=104,
        output_path='website/public/osjecka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§[pr]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
