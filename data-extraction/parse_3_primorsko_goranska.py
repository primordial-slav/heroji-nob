"""
Parser: 3. primorsko-goranska udarna brigada (brigade code 99).

Source: Bogdan Mamula, "Treća primorsko-goranska udarna brigada (Druga brigada 35. divizije)" (znaci.org 00001/122_5.pdf,
        its pages 15-40, book pp. 234-259)  →  website/public/pdfs/3-primorsko-goranska.pdf. Latin, two columns:
    pp. 1-7     Prilog 3, "Spisak starješina brigade i četnih bolničara", a hanging indent, the father as an initial:
                    BARETIC I. Zvonko, zamjenik političkog komesara bataljona
    pp. 8-26    Prilog 4, "Spisak poginulih pripadnika brigade", entries set apart by a gap, the father's name in the
                genitive:
                    ABRAMOVIĆ Jure Cvjetko, bolničar, rođen u Kuželju - Delnice, poginuo 12. novembra 1944. godine na
                    Brotnji kod Srba
In the first list a second name after the given name is a nickname ("ČUBRILO Dušan Duja"). Surnames the text spaced
apart ("AB RAMO VIĆ", "Z A N O V I Ć") are joined; lost carons and I read as l are put right from the spellings
the other units print (parse_8_kordunaska_divizija's helpers). The parser sets the birthplace in the nominative the
other units know ("u Kuželju - Delnice" = Kuželj, Delnice).
"""
import re
from itertools import product

import parse_8_kordunaska_divizija as k8
import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_FROM = 8
_prev: dict = {}
_starts: dict = {}


def corpus() -> None:
    """Every spelling of a name the other units print (k8.known, k8.respell read it)."""
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/3-primorsko-goranska-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault((ln['page'], ln['x'] > 150), []).append(ln['x'])


def keep(ln: dict) -> bool:
    t = re.sub(rf'\b(?:[{U}] ){{2,}}[{U}]\b', lambda m: m.group(0).replace(' ', ''), ln['text'].strip())   # "Z A N O V I Ć"
    col = (ln['page'], ln['x'] > 150)
    gap = ln['y'] - _prev.get(col, -99)
    _prev[col] = ln['y']
    if re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*', t) or ln['page'] in (1, FALLEN_FROM) and ln['y'] < 125 or re.match(r'^(?:Prilog|Spisak|broj|i četnih|ripadnika)', t):
        return False                                                         # headings, page numbers
    head = re.match(rf'^[{U}][{U}l]+(?:\s+[{U}][{U}l]*)*\s+(?:[{U}]\.\s+)?[{U}][{L}]', t)
    if ln['page'] < FALLEN_FROM:
        left = min(_starts[col])
        start = ln['x'] <= left + 6 and head
    else:
        start = gap > 14 and head
    if start:
        t = ('§o§ ' if ln['page'] < FALLEN_FROM else '§p§ ') + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    lst = text[1]
    text = re.sub(r'^§.§\s*', '', text)
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "pogi- nuo"
    head, _, info = text.partition(',')
    info = info.strip()
    words = head.split()
    caps = []
    while words and re.fullmatch(rf'[{U}][{U}l]*', words[0]) and not re.fullmatch(rf'[{U}]', words[0]):
        caps.append(k8.caps_word(words.pop(0)))
    father = words.pop(0) if words and re.fullmatch(rf'[{U}]\.|Lj\.|Nj\.', words[0]) else ''
    rest = [w for w in words if re.fullmatch(rf'[{U}][{L}]+', w)]
    notes = []
    if lst == 'p' and not father and len(rest) >= 2:
        if (k8.known(rest[0], 'first_name') > 20 and k8.known(rest[1], 'first_name') < 3
                and not k8.known(rest[0], 'middle_name') > k8.known(rest[0], 'first_name')):
            notes.append('zvani ' + ' '.join(rest[1:]))                      # "BRUSIĆ Anton Jurić": Krk's by-names
            rest = rest[:1]
        else:
            father, rest = rest[0], rest[1:]                                 # "ABRAMOVIĆ Jure Cvjetko"
    if lst == 'p' and father and len(rest) >= 2:
        notes.append('zvani ' + ' '.join(rest[1:]))                          # "KRPAN Petra Ivan Juranko"
        rest = rest[:1]
    if lst == 'o' and len(rest) >= 2:
        notes.append('zvani ' + ' '.join(rest[1:]))                          # "ČUBRILO Dušan Duja"
        rest = rest[:1]
    last = k8.join_parts(caps, 'last_name')
    rec = _record(last, ' '.join(rest), father, '; '.join(notes + [info]))
    b = re.search(rf'\bro[đd]en[a]?\s+(?:u|na|kod)\s+((?:Sv\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)?)'
                  rf'(?:\s*(?:-|kod|na)\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?))?', info)
    if b and b.group(1) not in ('Istri', 'Italiji', 'Krku'):
        rec['_birth'] = (b.group(1), b.group(2) or '')
    rec['death_type'] = death_type_from_text(info) or ('poginuo' if lst == 'p' else '')
    if lst == 'p' and re.search(r'\bstradao\b', info):
        rec['death_type'] = 'poginuo'
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
            place, muni = (nominative(p) if p else '' for p in birth)
            if place == birth[0] and re.search(r'(?:[^iě]u|ju|oj \S+|om \S+|[^ć]i)$', place):
                continue                                                     # "u Omišlju": no nominative known; the text keeps it
            if muni in ('Istra', 'Krk') or muni and not known[muni]:
                muni = ''
            s['birth_place'] = place + (', ' + muni if muni and muni != place else '')
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/3-primorsko-goranska.pdf',
        brigade_code=99,
        output_path='website/public/3-primorsko-goranska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=lambda p, s, e: columns_reader(2)(p, s, e),
        script='latin',
        entry_start_re=re.compile(r'^§[op]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
