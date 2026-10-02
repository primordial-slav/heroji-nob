"""
Parser: 14. primorsko-goranska brigada (brigade code 95).

Source: Vladimir-Dušan Matetić, "14. primorsko-goranska brigada" (znaci.org 00003/544.pdf, its pages 227-264, book
        pp. 227-264)  →  website/public/pdfs/14-primorsko-goranska.pdf. Latin, one column, a hanging indent:
    "Spisak poginulih boraca 14. primorsko-goranske brigade", the surname first, the father's name (genitive) or
    initial between it and the name, not in capitals:
        Barac Andrije Dragutin, rođen 1. I. 1910. u s. Grižane — Crikvenica, borac 2. čete 4. bataljona, poginuo
            26. XI 1944. kod s. Klapavica, Lika, sahranjen u s. Klapavica.
A second surname in brackets ("Nadalić (Šatić) I. Ivan") goes to the entry ("ili Šatić"). The parser sets the
birthplace: the village after "s." as printed with its municipality, a town after "u" in the nominative the other
units know ("u Puli" = Pula).
"""
import re
from itertools import product

import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_starts: dict = {}
TEXT_FIXES = [('Josipt ', 'Josip, '), ('Mi jo,', 'Mijo,'), ('Hrg Jurja, Ivan', 'Hrg Jurja Ivan')]   # the text layer's slips


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 120)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 2:
            return x
    return xs[0] if xs else ln['x']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,8}|\d+\*?\s+\d+|\W*\w{0,2}\W*', t) or re.match(r'^(?:SPISAK|14\. PRIMORSKO)', t):
        return False                                                         # page numbers ("15* 227"), the heading
    if ln['x'] <= margin(ln) + 6 and re.match(rf'^[{U}][{L}]+(?:\s*\([{U}][{L}]+\))?\s+[{U}]', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    for bad, good in TEXT_FIXES:
        text = text.replace(bad, good)
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "bata- ljona"
    head = re.split(r',|\s(?=ro[đd]en)', text, 1)[0]
    info = text[len(head):].lstrip(',').strip()
    notes = []
    alt = re.search(rf'\s*\(([{U}][{L}]+)\)', head)                           # "Nadalić (Šatić) I. Ivan"
    if alt:
        notes.append('ili ' + alt.group(1))
        head = head[:alt.start()] + head[alt.end():]
    words = head.split()
    if len(words) >= 3:
        last, father, given = words[0], words[1], ' '.join(words[2:])
    elif len(words) == 2:
        last, father, given = words[0], '', words[1]
    else:
        last, father, given = (words[0] if words else ''), '', ''
    rec = _record(last, given.rstrip('.'), father, '; '.join(notes + [info]))
    y = re.search(r'\bro[đd]en[a]?\s+(?:\d{1,2}\.\s*[IVX ]+\.?\s*)?(1[89]\d\d)', info)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.search(rf'\bro[đd]en[a]?\s+(?:[\dIVX. ]*?1[89]\d\d[.,]?\s*(?:godine\s*)?)?,?\s*(?:u\s+)?(s\.\s*)?'
                  rf'((?:Sv\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)?)(?:\s*—\s*(?:otok\s+)?([{U}][{L}]+(?:\s+[{U}][{L}]+)?))?', info)
    if b and not re.match(r'(?:Istri|Italiji)$', b.group(2)):
        rec['_birth'] = (bool(b.group(1)), b.group(2), b.group(3) or '')
    rec['death_type'] = death_type_from_text(info) or 'poginuo'
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
        birth = s.pop('_birth', None)
        if birth:
            village, place, muni = birth
            place = place if village else nominative(place)                  # "u s. Kuželj" as printed, "u Puli" = Pula
            s['birth_place'] = place + (', ' + muni if muni and muni != place else '')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/14-primorsko-goranska.pdf',
        brigade_code=95,
        output_path='website/public/14-primorsko-goranska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
