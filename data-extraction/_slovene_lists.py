"""
The rosters and lists of the fallen at the back of the Knjižnica NOV in POS monographs (znaci.org 00003/7xx).

Two columns, a hanging indent, the names in ordinary letters (surname first):
    Seznam borcev   Adam Jože-Ciril, 1920, Sodražica
                    Adamič Bara-Beba, roj. Cemič, 1921, Maribor
    Padli           Afal Jože-Branko, Stružnica 1922—1944
"Jože-Ciril" is the given name and the partisan name he went by (written "zvani Ciril;" as in Ljubljanska).
The scans are skewed, so an entry is told from its continuation lines by the indent against the line before,
not by a fixed margin. The text layer reads Ž as 2 ("2ebovec"), š and č inside a word as S and C ("AdleSič"),
l as I after a capital ("AIojz"), and 9 as 0 in years ("1011" = 1911).
"""
import glob
import json
import re

from _parser_scaffold import _record

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


_GIVEN: set = set()


def given_names() -> set:
    """Every given name the site's units print (to tell "Ažman Ivan" from a place, "Velika Loka")."""
    if not _GIVEN:
        for f in glob.glob('website/public/*soldiers.json'):
            for r in json.load(open(f, encoding='utf-8')):
                if r.get('first_name'):
                    _GIVEN.add(r['first_name'])
    return _GIVEN


class Indent:
    """prepare_fn and line_filter: marks each line that starts an entry with '§<kind>§ ' (kind: 's' roster, 'p'
    fallen) and drops headings and page numbers. An entry starts at the column's margin, measured near the line
    (within 60 pt above and below), so the scan's skew doesn't move it; continuation lines sit ~9 pt in."""

    def __init__(self, padli_from: int | None, headings: re.Pattern, split_x: float = 250):
        self.padli_from = padli_from
        self.headings = headings
        self.split_x = split_x
        self.cols: dict = {}

    def prepare(self, lines: list[dict]) -> None:
        for ln in lines:
            t = ln['text'].strip()
            if t and not re.fullmatch(r'[\d\W]{1,5}', t) and not self.headings.match(t):
                self.cols.setdefault((ln['page'], ln['x'] > self.split_x), []).append((ln['y'], ln['x']))

    def margin(self, ln: dict) -> float:
        near = sorted(x for y, x in self.cols.get((ln['page'], ln['x'] > self.split_x), []) if abs(y - ln['y']) <= 60)
        for x in near:                                                       # the leftmost x two other lines share
            if sum(1 for o in near if abs(o - x) <= 3) >= 3:
                return x
        return near[0] if near else ln['x']

    def __call__(self, ln: dict) -> bool:
        t = ln['text'].strip()
        t = re.sub(r'^1(19\d\d)$', r'† \1', t)                                  # "11946": † 1946, on a line of its own
        if re.fullmatch(r'[\d\W]{1,5}', t) or self.headings.match(t):
            return False
        kind = 'p' if self.padli_from and ln['page'] >= self.padli_from else 's'
        indent = ln['x'] - self.margin(ln)
        starts = re.match(rf'^(?:[{U}]|[2šžčć][{L}])', t)                     # "žužek": a lowercase Ž
        # "Surname Given," or "Surname Given-Alias, 1920": where the scan curves or was pasted, entries drift in
        # and continuation lines out, so a line that doesn't start at the margin must read as a name
        name = rf'^\S+ (?:(?:dr|ing|arh)\. )?[{U}][{L}]+(?:-[{U}]\S*)?'
        strict = re.match(name + r'(?:[,.]| 1[89]\d\d)', t)
        bare = re.fullmatch(r'\S+ (\S+)', t)                                       # "Ažman Ivan": a name and nothing else
        loose = strict or re.search(r',|1[89]\d\d', t) or (bare and bare.group(1) in given_names())
        if starts and ((indent < 4 and loose) or (indent < 14 and strict)):
            t = f'§{kind}§ ' + t
        ln['text'] = t
        return True


def fix_ocr(t: str) -> str:
    t = re.sub(rf'(?<![\w])2(?=[{L}])', 'Ž', t)                              # "2ebovec"
    t = re.sub(r'(^|,\s)([šžčć])', lambda m: m.group(1) + m.group(2).upper(), t)   # "žužek", ", črneča vas"
    t = re.sub(rf'(?<=[{L}])([ČŠŽ])', lambda m: m.group(1).lower(), t)      # "KarlovŠek"
    t = re.sub(r'\u00ad\s*', '', t)                                          # a soft hyphen at a line break
    t = re.sub(r',?\s+1(19\d\d)\s*$', r' † \1', t)                         # "Mokronog, 11967"
    t = re.sub(rf'(?<=[{L}])S(?=[{L}])', 'š', t)                             # "AdleSič"
    t = re.sub(rf'(?<=[{L}])C(?=[{L}]|\b)', 'č', t)                          # "ZemljariC"
    t = re.sub(rf'(?<=\b[{U}])I(?=[{L}])', 'l', t)                           # "AIojz"
    t = re.sub(r'\b10(\d\d)\b', r'19\1', t)                                  # "1011" = 1911
    return re.sub(r'\s+[f†]\s?(19\d\d)\b', r' † \1', t)                      # "f 1970": died after the war


def name_part(head: str) -> tuple[str, str, list[str]]:
    """'Ahčin dr. Marjan-Marjan' -> ('Ahčin', 'Marjan', ['dr.', 'zvani Marjan'])."""
    toks = head.replace('.', '. ').split()
    out = []
    for w in toks:                                                           # "Zara n Ludvik": a letter cut off the word
        if out and re.fullmatch(rf'[{L}]{{1,3}}', w) and w not in ('pri', 'na', 'v'):
            out[-1] += w
        else:
            out.append(w)
    if len(out) > 2 and out[1][:1].islower() and out[1] not in ('pri', 'na', 'v'):
        out[:2] = [out[0] + out[1]]                                          # "No vina Rado"
    other = [w.strip('()') for w in out[1:2] if w.startswith('(') and w.endswith(')')]
    out = [w for w in out if w.strip('()') not in other]                     # "Čok (Cioch) Anton"
    pre = [w for w in out if w in ('dr.', 'ing.', 'mr.', 'arh.')]
    out = [w for w in out if w not in pre]
    if len(out) > 2 and out[0] in ('De', 'Del', 'Di', 'Da', 'Van', 'Von'):    # "De Gleria Mitja"
        out[:2] = [out[0] + ' ' + out[1]]
    last = out[0] if out else ''
    rest = ' '.join(out[1:])
    given, _, alias = rest.partition('-')
    parts = given.split()
    if len(parts) > 1 and any(len(w) <= 2 or w[0].islower() for w in parts[1:]):
        given = ''.join(parts)                                               # "Pa vel", "J anko": one name spaced apart
    alias = re.sub(r'\s+(?=[{L}])'.replace('{L}', L), '', alias.strip())     # "Dra vin" = Dravin
    notes = pre + ['ili ' + o for o in other] + (['zvani ' + alias] if alias else [])
    return last, given.strip(), notes


def parse_roster(text: str) -> dict:
    """'Adamič Bara-Beba, roj. Cemič, 1921, Maribor'"""
    text = fix_ocr(re.sub(r'^§s§\s*', '', text))
    m = re.search(r',|\s(?=1[89]\d\d)', text)
    head, rest = (text[:m.start()], text[m.end():].strip()) if m else (text, '')
    last, given, notes = name_part(head.rstrip('.'))
    born = re.match(r'^((?:roj|por)\.\s*[^,]+),\s*', rest)                   # maiden or married name
    if born:
        notes.append(born.group(1))
        rest = rest[born.end():]
    rest = re.sub(r'^(1[89]\d\d)\.?\s', r'\1, ', rest)
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    by = re.match(r'^(1[89]\d\d)\b', rest)
    if by:
        rec['birth_year'] = by.group(1)
    return rec


def parse_fallen(text: str) -> dict:
    """'Afal Jože-Branko, Stružnica 1922—1944': the place, the years of birth and death."""
    text = fix_ocr(re.sub(r'^§p§\s*', '', text))
    head, _, rest = text.partition(',')
    if not rest:                                                             # "Cad Justin —1944": no comma
        m = re.search(r'\s(?=(?:1[89]\d\d)?\s*[—–-]+\s*19\d\d)', text)
        if m:
            head, rest = text[:m.start()], text[m.end():]
    last, given, notes = name_part(head)
    rest = rest.strip()
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    yrs = re.search(r'(1[89]\d\d)?\s*[—–-]+\s*(19\d\d)\s*$', rest)
    place = rest[:yrs.start()].strip(' ,') if yrs else ''
    if yrs and yrs.group(1):
        rec['birth_year'] = yrs.group(1)
    rec['death_type'] = 'poginuo'
    if yrs:
        rec['death_date'] = yrs.group(2)
    if place and not re.search(r'\d', place):
        rec['birth_place'] = place
    return rec


def parse(text: str) -> dict:
    return parse_fallen(text) if text.startswith('§p§') else parse_roster(text)
