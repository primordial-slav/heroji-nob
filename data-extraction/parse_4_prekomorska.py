"""
Parser: 4. prekomorska brigada (brigade code 166).

Source: Edvin Pervanje, Jože A. Hočevar, "Četrta prekomorska brigada" (Knjižnica NOV in POS 25-III, 1969; znaci.org
        00003/783.pdf) →  website/public/pdfs/4-prekomorska.pdf (book pp. 327-333):
    p. 1        "Seznam padlih in umrlih borcev": "BOŽEGLAV DRAGO, r. 8. novembra 1914 Lokve pri Divači, p. 23. junija
                1944 pri prevozu materiala z letalom v domovino." (r. rojen, p. padel; "umri" = umrl)
    pp. 3-7     "Seznam vodilnega kadra brigade": under each staff (Štab brigade, Komanda stana, the battalions, the
                independent company) and duty, one a line, given name first, numbered in the order they served,
                "1. ANTON CERNE-ZVONE"; then the companies' officers, surname first, "BAKOTIN MARIN,". A man under
                several duties is one record.
The brigade's base supply department in Bari (pp. 335-338 of the book) is not the brigade and stays out.
"""
import re
import unicodedata

from _parser_scaffold import _record, extract_lines_single_column, run_parser, title_case
from _slovene_lists import OWN

U = 'A-ZČĆŽŠĐ'
FALLEN_PAGE = 1
UNITS = {'Stab brigade': 'štaba brigade', 'Štab brigade': 'štaba brigade', 'Komanda stana': 'komande stana',
         '1. bataljon': '1. bataljona', '2. bataljon': '2. bataljona', '3. bataljon': '3. bataljona',
         'Samostojna četa brigade': 'samostojne čete brigade'}
COMPANY = {'Komandirji čet': 'komandir čete', 'Politični komisarji čet': 'politični komisar čete',
           'Namestniki komandirjev': 'namestnik komandirja čete',
           'Pomočniki političnih komisarjev čet': 'pomočnik političnega komisarja čete'}


def fold(t: str) -> str:
    t = (t or '').lower().replace('đ', 'dj')
    return re.sub(r'[^a-z]', '', ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c)))


def fix(t: str) -> str:
    """'2UGELJ' = Žugelj, 'JANEZlC' = Janežič: capitals the scan misread."""
    return re.sub(rf'(?<=[{U}])l(?=[{U}]|\b)', 'I', t).replace('2U', 'ŽU')


def two_words(words: list[str]) -> list[str]:
    """'MILOS ST ANO JE VIC' -> MILOS STANOJEVIC: a name of two words the scan spaced apart; the shortest
    neighbours join first, the first word (the given name, or the surname in the companies' lists) stays whole."""
    words = list(words)
    while len(words) > 2:
        i = min(range(1, len(words) - 1), key=lambda k: len(words[k]) + len(words[k + 1]))
        words[i:i + 2] = [words[i] + words[i + 1]]
    return words


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, unit, duty, company, note = [], '', '', '', False
    for ln in extract_lines_single_column(pdf_path, start, end):
        t = ln['text'].strip()
        note = note or t.startswith('OPOMBA')                                 # the editor's note under the last list
        if note or re.fullmatch(r'[\d\W]{1,4}', t) or t.startswith(('SEZNAM', '*')):
            continue
        if ln['page'] == FALLEN_PAGE:
            if re.match(r'^(?:Padli|Umrli)\s*:', t):
                continue
            if ln['y'] > 600 or re.match(r'^(?:Seznam padlih|tov in podatkov|morskih brigad|občin ter)', t):
                continue                                                      # the footnote under the list
            starts = bool(re.match(rf'^[{U}2][{U}2l\s]+,', t))
            out.append(dict(ln, text=('§p§ ' if starts else '') + t))
            continue
        head = t.rstrip(': ')
        if head in UNITS:
            unit, company = UNITS[head], ''
            continue
        if head in COMPANY:
            company, unit = COMPANY[head], ''
            continue
        m = re.match(r'^\d+\.\s*(.+?),?\.?$', t)
        if m and duty and not company:
            out.append(dict(ln, text=f'§k§{duty}|{unit}§ {m.group(1)}'))
            continue
        if company and re.match(rf'^[{U}a-z]', t):
            out.append(dict(ln, text=f'§c§{company}|§ {t.rstrip(",.")}'))
            continue
        if t.endswith(':') or re.match(r'^[A-ZČŠŽ][a-zčšžć\- ]+:?$', t):
            duty = re.sub(r'\s*:\s*$', '', t)
    return out


def parse_fallen(text: str) -> dict:
    head, _, rest = text.partition(',')
    words = fix(head).replace('2', 'Ž').split()
    last = title_case(words[0]) if words else ''
    given = ' '.join(title_case(w) for w in words[1:])
    rest = re.sub(r'\s+', ' ', re.sub(r'(?<=[a-zčšž])[-­]\s+(?=[a-zčšž])', '', rest)).strip().rstrip('.')
    rest = re.sub(r'\bumri\b', 'umrl', rest)
    rec = _record(last, given, '', rest)
    y = re.search(r'\br\.\s*(?:\d{1,2}\.\s*[a-z]+\s+)?(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    if re.search(r'\bp\.\s', rest):
        rec['death_type'] = 'poginuo'
    elif re.search(r'\bumrl\b|žrtev|ponesrečil', rest):
        rec['death_type'] = 'umro'
    d = re.search(r'\b(?:p\.|umrl)\s+((?:\d{1,2}\.\s*)?(?:[a-z]+\s+)?(?:leta\s+)?19\d\d)', rest)
    if d:
        rec['death_date'] = re.sub(r'^leta\s+', '', d.group(1))
    return rec


def parse_officer(text: str) -> dict:
    m = re.match(r'^§([kc])§([^|]*)\|([^§]*)§\s*(.*)$', text)
    kind, duty, unit, name = m.groups()
    name = fix(name)
    notes = []
    vd = re.match(r'^v\.\s*d\.\s*', name)                                     # "v. d. BOŠKO KERKEZ": acting
    if vd:
        notes.append('v. d.')
        name = name[vd.end():]
    if name.startswith('dr. '):
        notes.append('dr.')
        name = name[4:]
    name, _, alias = name.partition('-')                                       # "ANTON CERNE-ZVONE"
    words = two_words(name.split())
    if kind == 'c':
        last, given = words[0], ' '.join(words[1:])
    else:
        last, given = words[-1], ' '.join(words[:-1])
    if alias.strip():
        notes.append('zvani ' + title_case(alias.strip()))
    duty = (duty[:1].lower() + duty[1:]).replace('pomoćnik', 'pomočnik').replace('SKO J', 'SKOJ')
    where = f' {unit}' if unit and not duty.endswith(unit) else ''
    rec = _record(title_case(last.upper()), title_case(given.upper()), '', '; '.join(notes + [f'{duty}{where}']))
    rec['_duty'] = True
    return rec


def parse_entry(text: str) -> dict:
    if text.startswith(('§k§', '§c§')):
        return parse_officer(text)
    return parse_fallen(re.sub(r'^§p§\s*', '', text))


def post(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        duty = s.pop('_duty', False)
        key = (fold(s['last_name']), fold(s['first_name']))
        if duty and key in seen:
            first = seen[key]
            have = first['additional_info'].split('; ')
            first['additional_info'] = '; '.join(have + [x for x in s['additional_info'].split('; ') if x not in have])
            continue
        seen.setdefault(key, s)
        out.append(s)
    return out


if __name__ == '__main__':
    OWN['file'] = '4-prekomorska-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/4-prekomorska.pdf',
        brigade_code=166,
        output_path='website/public/4-prekomorska-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[pkc]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
