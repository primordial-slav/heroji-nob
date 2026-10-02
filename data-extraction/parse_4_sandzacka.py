"""
Parser: 4. sandžačka NOU brigada (brigade code 98).

Source: Čedo Drulović, "Četvrta sandžačka brigada" (znaci.org 00001/271_9.pdf, its pages 3-28, book pp. 460-485)
        →  website/public/pdfs/4-sandzacka.pdf. Cyrillic, one column, numbered entries with a hanging indent:
    pp. 1-10    "Spisak poginulih boraca i rukovodilaca 4. sandžačke NOU brigade" (281), the father as an initial:
                    1. AGIĆ M. ČAZIM, borac, rođen 1926. godine u s. Zvijezda kod Prijepolja. Poginuo 9. 12. 1944. ...
    pp. 11-26   "Spisak ranjenih boraca i rukovodilaca 4. sandžačke NOU brigade" (477), the father's name in brackets:
                    1. AJDAROVIĆ (Azima) NURO, borac 4. bataljona, ranjen 15. februara 1945. godine na položaju kod ...
The book letter-spaces some surnames ("Ј А Н К О В И Ћ") and the text layer reads Л as Ј1 and З as 3; on two pages
the numbers stand apart from their names, so an entry also starts with a name in capitals at the left margin. A
soldier the list of the wounded prints twice (wounded twice) keeps both entries. The parser sets the birthplace:
the village and the place after "kod" in the nominative ("kod Prijepolja" = Prijepolje).
"""
import re
from itertools import product

import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
WOUNDED_FROM = 11
_starts: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 150)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 4) >= 3:
            return x
    return xs[0] if xs else ln['x']


def spaced(text: str) -> str:
    """"J A N K O V I Ć" = JANKOVIĆ: a run of three or more single capitals is one word."""
    return re.sub(rf'\b(?:[{U}] ){{2,}}[{U}]\b', lambda m: m.group(0).replace(' ', ''), text)


def keep(ln: dict) -> bool:
    t = spaced(ln['text'].strip()).replace('J1', 'L').replace('j1', 'l')
    if re.fullmatch(r'[\d\W]{1,6}', t) or re.match(r'^(?:Si[ip]sak|Spisak|4\. sandžačke|i rukovodilaca)', t):
        return False                                                         # headings, page numbers
    lst = 'r' if ln['page'] >= WOUNDED_FROM else 'p'
    if re.match(rf'^\W?\d[\dG;:]{{0,3}}[.,]?\s+[{U}]{{2,}}', t) or (ln['x'] <= margin(ln) + 6 and re.match(rf'^[{U}]{{3,}}\s+[{U}(]', t)):
        t = f'§{lst}§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    lst = text[1]
    text = re.sub(r'^§.§\s*\W?(?:\d[\dG;:]{0,3}[.,]?\s+)?', '', text)       # "2G;0." = 280.
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "Pogi- nuo"
    head, _, info = text.partition(',')
    info = info.strip()
    words = [w for w in re.sub(r'(?<=\.)(?=\S)', ' ', head.replace('3.', 'Z.').replace('X.', 'H.')).split()]
    father = ''
    paren = re.search(rf'\(([{U}][{L}]+)\)', head)                           # "AJDAROVIĆ (Azima) NURO"
    if paren:
        father = paren.group(1)
        words = [w for w in words if not w.startswith('(')]
    caps = [w.rstrip('.') for w in words if re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*\.?', w)]
    init = [w for w in words if re.fullmatch(rf'(?:[{U}]|LJ|NJ|DŽ|Lj|Nj|Dž)\.', w)]
    if not father and init:
        father = init[0].title()
    last = caps[0] if caps else ''
    given = ' '.join(caps[1:]).title()
    rec = _record(last, given, father, info)
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d\.?\s*(?:godine|god\.)?\s*)?u\s+(s\.\s*|selu\s+)?([{U}][{L}]+(?:\s+[{U}][{L}]+)?)'
                  rf'(?:\s*(?:,|—|kod)\s*([{U}][{L}]+(?:\s+[{U}][{L}]+)?))?', info)
    if b:
        rec['_birth'] = (bool(b.group(1)), b.group(2), b.group(3) or '')
    rec['death_type'] = death_type_from_text(info) or ('poginuo' if lst == 'p' else '')
    rec['_list'] = lst
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    known = top._corpus()[0]

    def nominative(place: str) -> str:
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in place.split()))]
        forms = [f for f in forms if f != place and known[f] > known[place]]
        return max(forms, key=lambda f: known[f]) if forms else place

    for s in soldiers:
        s.pop('_list', None)
        birth = s.pop('_birth', None)
        if birth:
            village, place, muni = birth
            place = place if village else nominative(place)                  # "u s. Zvijezda", "u Pljevljima" = Pljevlja
            muni = nominative(muni) if muni else ''                          # "kod Prijepolja" = Prijepolje
            s['birth_place'] = place + (', ' + muni if muni and muni != place else '')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-sandzacka.pdf',
        brigade_code=98,
        output_path='website/public/4-sandzacka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§[pr]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
