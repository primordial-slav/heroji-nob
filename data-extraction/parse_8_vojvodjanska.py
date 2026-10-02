"""
Parser: 8. vojvođanska udarna brigada (brigade code 78).

Source: Nikola Božić, "Rovovi i mostobrani: Osma vojvođanska brigada" (znaci.org 00001/184_9.pdf, its pages 2-49,
        book pp. 675-722)  →  website/public/pdfs/8-vojvodjanska.pdf:
    "Spisak poginulih i nestalih boraca i rukovodilaca Osme vojvođanske udarne brigade", one column, a hanging indent:
        ARADACKI Pavla Milivoj, rođ. 1928, Bečej, poginuo u Crncu 21. I 1945.
        ANUŠIĆ P. Ivan, rođ. 1926, Subotica, poginuo u s. Repić 7. V 1945.
The surname in capitals, the father (genitive, or an initial) and the given name not.
"""
import re

from _parser_scaffold import _record, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_starts: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 80)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 3:
            return x
    return xs[0] if xs else ln['x']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}|\w', t) or re.match(r'^(?:S ?P ?I ?S ?A ?K|POGINULIH I NESTALIH|VOJVOĐANSKE UDARNE)', t):
        return False
    if ln['x'] <= margin(ln) + 6 and re.match(rf'^[{U}]{{2,}}', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


NAME = re.compile(rf'^([{U}]{{2,}}(?:[- ][{U}]{{2,}})*)\s+(?:([{U}][{L}]+|[{U}]\.)\s+)?([{U}][{L}]+(?:-[{U}][{L}]+)?)\s*(?:\(([^)]*)\))?\s*,?\s*')


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "Petro- vom"
    text = re.sub(r"^(\S+?)['’]", r'\1', text).replace("'", '')               # "VOJNO'VIĆ"
    text = re.sub(rf'(?<=[{U}])5(?=[{U}])', 'Š', text)                        # "HOLA5EVIĆ"
    text = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', text)
    text = re.sub(rf'(?<=[{U}])0(?=[{U}])', 'O', text)
    text = re.sub(rf'^([{U}]{{2,}})-\s+', r'\1 ', text)                       # "MANDIĆ- Mihajlo"
    text = re.sub(rf'^([{U}]{{2,}}),\s+(?=[{U}][{L}])', r'\1 ', text)         # "ČOLIĆ, Joca"
    text = re.sub(rf'(?<=\s)([{U}]) ([{L}]{{2,}})(?=,)', r'\1\2', text)         # "ZEINAĐ I mre"
    toks = text.split(' ')
    caps = 0
    while caps < len(toks) and re.fullmatch(rf'[{U}]+', toks[caps]):
        caps += 1
    if caps > 1 and any(len(w) <= 3 for w in toks[:caps]):                   # "TAN KO VIĆ Šime"
        text = ''.join(toks[:caps]) + ' ' + ' '.join(toks[caps:])
    notes = []
    alt = re.match(rf'^([{U}]{{2,}})\s+(?:\((?:ili\s+)?([^)]+)\)|ili\s+([{U}]{{2,}}))\s*', text)   # "MATIĆ (KOLION)", "BIČKOVIĆ ili BIČKUNOVIĆ"
    if alt:
        notes.append('ili ' + (alt.group(2) or alt.group(3)).title())
        text = alt.group(1) + ' ' + text[alt.end():]
    m = NAME.match(text)
    if not m:
        head, _, rest = text.partition(',')
        toks = head.split()
        return _record(toks[0].title() if toks else '', ' '.join(toks[1:]), '', '; '.join(notes + ([rest.strip()] if rest.strip() else [])))
    last, father, given, nick = m.groups()
    rest = text[m.end():].strip()
    notes += [f'zvani {nick}'] if nick else []
    rec = _record(last.title(), given, father or '', '; '.join(notes + ([rest] if rest else [])))
    b = re.match(rf'^rođ\.?\s*(?:(1[89]\d\d)\.?,?\s*)?((?:u\s+)?[{U}][^,]*(?:,\s*[{U}][^,]*?)?)(?=,\s*[{L}]|,\s*(?:pogin|nesta|umr)|\s+(?:pogin|nesta|umr)|$)', rest)
    if b:
        if b.group(1):
            rec['birth_year'] = b.group(1)
        place = b.group(2).strip()
        if place and not place.startswith('u '):
            rec['birth_place'] = place
    rec['death_type'] = 'nestao' if re.search(r'\bnesta(?:o|la)\b', rest) else 'umro' if re.search(r'\bumr(?:o|la)\b', rest) else 'poginuo'
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/8-vojvodjanska.pdf',
        brigade_code=78,
        output_path='website/public/8-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=restore_diacritics,
    )
