"""
Parser: 23. srpska NOU brigada (brigade code 89).

Source: Dragoljub Ž. Mirčetić Duško, "23. srpska brigada" (znaci.org 00001/214_15.pdf, its pages 17-53, book
        pp. 352-388)  →  website/public/pdfs/23-srpska.pdf. Cyrillic, one column, a hanging indent:
    "Pregled poginulih i umrlih boraca i rukovodilaca" (Prilog 2; the author found 475: 320 in the brigade's records
    in the army archive and 155 more):
        ALEKSIĆ Marka SVETISLAV, 1922, Sekurić, Rekovac, zemljoradnik. U NOVJ od novembra 1944, borac 2. čete,
            4. bataljona. Poginuo 10. februara 1945. u selu Porečina.
The OCR reads Ћ as Н, Б or Е ("АЛЕКСИН", "АНТОНИЈЕВИЕ"; repaired where the name with -ić is known), Ђ as Б, and
spells some surnames in Latin look-alikes of the Cyrillic letters ("JAНKOBНR" = Janković: read back with the Užički
odred's decoder). The parser sets the birthplace: the village and the municipality after the year.
"""
import re

from _parser_scaffold import _record, death_type_from_text, repair_cyrillic_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_starts: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 150)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 2:
            return x
    return xs[0] if xs else ln['x']


LOOK = {'A': ('A', 'L', 'D'), 'B': ('V', 'B', 'Đ', 'Ć'), 'C': ('S', 'C'), 'H': ('N', 'I'), 'N': ('N', 'I', 'Ć'), 'P': ('R', 'P'),
        'R': ('Ć', 'R'), 'X': ('H',), 'Y': ('U',), '4': ('Č',), '0': ('O',), 'E': ('E', 'Ć'), '®': ('F',),
        'LJ': ('LJ',), 'NJ': ('NJ',), 'Š': ('Š',)}
MULTI = re.compile(r'A>|Aa|Az|Lz|L>|N>|N»|H>|III|UI|IU|.')
SIGNS = {'A>': 'LJ', 'Aa': 'LJ', 'Az': 'LJ', 'Lz': 'LJ', 'L>': 'LJ', 'N>': 'NJ', 'N»': 'NJ', 'H>': 'NJ', 'III': 'Š', 'UI': 'Š', 'IU': 'Š'}
_names: dict = {}


def read_back(word: str, field: str) -> str | None:
    """A name the text layer spells with Latin look-alikes of Cyrillic letters or with signs ("BEAaKOBNR",
    "CTE®ANOBNR", "LzUBOMIR"): the reading the other units know best, if the word as printed is unknown."""
    if not _names:
        from parse_uzicki_odred import FIRST, LAST
        _names.update(last=LAST, first=FIRST)
    known = _names[field]
    if len(word) < 3:
        return None
    parts = [SIGNS.get(p, p.upper()) for p in MULTI.findall(word)]
    options = [LOOK.get(p, (p,)) for p in parts]
    if sum(len(o) > 1 for o in options) > 8:
        return None
    best = max((''.join(c) for c in __import__('itertools').product(*options)), key=lambda c: known[c])
    # a garbled spelling other books share ("MIAAN" twice in 7. krajiška) yields to a reading far more common
    return best if best != word.upper() and known[best] >= max(2, 10 * known[word.upper()]) else None


def decode_head(t: str) -> str:
    head, sep, rest = t.partition(',')
    words = head.split(' ')
    for i, w in enumerate(words):
        core = w.rstrip('.')
        if len(core) >= 3 and sum(c.isupper() for c in core) >= len(core) - 2:
            parts = core.split('-')
            reads = [read_back(p, 'last' if i == 0 else 'first') for p in parts]
            if any(reads):
                words[i] = '-'.join(r or p for r, p in zip(reads, parts)) + w[len(core):]
    return ' '.join(words) + sep + rest


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*', t) or re.match(r'^[-"»]?\s*\d{3}$', t):
        return False                                                         # page numbers, specks
    if ln['x'] <= margin(ln) + 5 and re.match(rf'^[{U}A-Z0-9>]{{3,}}', t) and not re.match(r'^(?:PREGLED|I RUKOVODILACA|NOVJ|U\s)', t):
        t = '§p§ ' + decode_head(t.replace('PL>EVIE', 'PLJEVIĆ'))         # П-Љ-Е-В-И-Ћ
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "feb- ruara"
    text = re.sub(r'^([^,]*?)\s+(?=1[89]\d\d\b)', r'\1, ', text, count=1)    # "ANTIN Dragoljuba ŽIVORAD 1920,"
    head, _, rest = text.partition(',')
    rest = rest.strip()
    notes = []
    alt = re.search(r'\s*\(([^)]+)\)', head)                                  # "MIKOVIĆ (MINOVIĆ) Save DUŠAN"
    if alt:
        notes.append('ili ' + alt.group(1).strip().title())
        head = head[:alt.start()] + head[alt.end():]
    toks = [t.rstrip('.').upper() if sum(c.isupper() for c in t) >= len(t.rstrip('.')) - 1 and len(t) > 2 else t
            for t in head.split()]                                           # "STOJILJKOVIĆ.", "ILIć"
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', toks[0]):
        caps.append(toks.pop(0))
    father = ''
    if toks and re.fullmatch(rf'(?:[{U}][{L}]*\.?|Lj\.|Nj\.)', toks[0]):
        father = toks.pop(0)                                                 # "Marka", "R."
    caps += [t for t in toks if re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', t)]
    extra = [t for t in toks if not re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', t)]
    if len(caps) >= 3 and caps[1] in ('LJ', 'NJ', 'DŽ') and not father:
        father = caps.pop(1).title() + '.'                                   # "JOVIĆ LJ. ČEDOMIR"
    last = caps[0] if caps else ''
    given = ' '.join(caps[1:])
    if not given and father and not father.endswith('.'):
        given, father = father, ''
    rec = _record(last, given.title() if given.isupper() else given, father,
                  '; '.join(notes + (['zvani ' + ' '.join(extra)] if extra else []) + ([rest] if rest else [])))
    y = re.match(r'(1[89]\d\d)\b', rest)
    if y:
        rec['birth_year'] = y.group(1)
    parts = [p.strip() for p in re.split(r'[,.]\s', re.sub(r'^1[89]\d\d\b[,.]?\s*', '', rest))]
    places = []
    for p in parts[:3]:
        if re.fullmatch(rf'[{U}][{L}]+(?:[\s-]+[{U}(]?[{L})]+)*', p):
            places.append(p)
        else:
            break
    if places:
        rec['birth_place'] = places[0] + (', ' + places[-1] if len(places) > 1 else '')
    rec['death_type'] = death_type_from_text(rest) or 'poginuo'
    return rec


READ = {'Bukobnn': 'Vuković', 'Cpbobnr': 'Srbović', 'Pamaaanobnr': 'Ramadanović', 'Ranbelobnr': 'Ranđelović',
        'Spasojevnn': 'Spasojević', 'Trnfunovnn': 'Trifunović', 'Petrovii': 'Petrović'}   # look-alikes no known reading decided


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = restore_diacritics(repair_cyrillic_ocr(soldiers))
    for s in soldiers:
        if s['last_name'].endswith('ii'):
            s['last_name'] = s['last_name'][:-1] + 'ć'                       # "CEKII", "PETROVII": Ћ read as И
        if s['last_name'] in READ:
            s['last_name'] = READ[s['last_name']]
            s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/23-srpska.pdf',
        brigade_code=89,
        output_path='website/public/23-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
