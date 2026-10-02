"""
Parser: 5. vojvođanska NOU brigada (brigade code 82).

Source: Nikola Mraović, "Peta vojvođanska brigada" (znaci.org 00001/81_4.pdf, its pages 1-156, book pp. 429-584)
        →  website/public/pdfs/5-vojvodjanska.pdf:
    "Spisak boraca i starešina Pete vojvođanske brigade" (4,459 names, the author says), one column, a hanging indent:
        ABADŽIJA Pavle, 1909, Vojka, St. Pazova, zemljoradnik, borac, poginuo juna 1944. kod Teočaka.
        AĆIMOVIĆ Jove Sava, 1921, Donji Tovarnik, Ruma, nestao 26. XII 1943. u pokretu od Dugih Njiva do Zelinje.
        ADAMOV Ž. Radica, 1925, Elemir, Zrenjanin, zemljoradnik, nestao 16. IV 1945. ispred s. Feričanci.
        ALIĆ RAMO, 1926, Bijeljina, krojački pomoćnik, borac, nestao 16. VII 1944. ...
The surname in capitals, the father (genitive, or an initial) and the given name not (some given names are in
capitals too). After the year: the birthplace and its municipality, the trade, the duty in the brigade, the fate
(survivors who died since: "umro posle rata").
"""
import re

from _parser_scaffold import _record, death_type_from_text, run_parser

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
    if re.fullmatch(r"[•'\\]?\d{3}\.?(?:\s+p<m)?|\W*\w{1,3}\W*", t):
        return False                                                         # page numbers, letter headings, specks
    if ln['page'] == 1 and (ln['y'] < 75 or ln['y'] > 270):
        return False                                                         # the heading, and the author's note under it
    t = re.sub(r'[\s.,»•]{3,}$', '.', t)                                      # "Baljkovac. .,,».,..,•.,"
    t = t.replace('Ö', 'O').replace('Ü', 'U')                                 # "KÖNRAD Stjepan"
    t = re.sub(rf'^(?:[\s.,:;•\'"`´^/<>»«|]|i\s)+(?=[{U}]{{2}})', '', t)        # ". TANOŠEVIĆ", "• PERIĆEVIĆ", "i MIŠKOVIĆ"
    t = re.sub(r'^\S+', lambda m: re.sub(rf'(?<=[{U}])[1l](?=[{U}])', 'I', re.sub(rf'(?<=[{U}])0(?=[{U}])', 'O', m.group(0))), t)   # "B1LEK", "J0VIČIN"
    if ln['x'] <= margin(ln) + 6 and re.match(rf'^[{U}]{{2,}}', t) and not re.match(r'^[IVX]+\s+19', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


ABBREV = {'St. Pazova': 'Stara Pazova', 'Sr. Mitrovica': 'Sremska Mitrovica', 'Sr. Karlovci': 'Sremski Karlovci',
          'S. Mitrovica': 'Sremska Mitrovica', 'S. Karlovci': 'Sremski Karlovci', 'Sr. Mihaljevci': 'Sremski Mihaljevci',
          'St. Banovci': 'Stari Banovci', 'N. Banovci': 'Novi Banovci', 'N. Karlovci': 'Novi Karlovci',
          'N. Sad': 'Novi Sad', 'Sr. Kamenica': 'Sremska Kamenica', 'Sr. Laze': 'Sremske Laze'}


def place(word: str) -> str:
    word = re.sub(r'\s+', ' ', word.strip())
    return ABBREV.get(word, word)


PREFIX = {'Vel': ('Veliki', 'Velika', 'Veliko', 'Velike'), 'Vcl': ('Veliki', 'Velika', 'Veliko', 'Velike'),
          'Mal': ('Mali', 'Mala', 'Malo', 'Male'), 'St': ('Stari', 'Stara', 'Staro', 'Stare'), 'Si': ('Stari', 'Stara', 'Staro', 'Stare'),
          'Ban': ('Banatski', 'Banatska', 'Banatsko'), 'Bos': ('Bosanski', 'Bosanska', 'Bosansko'), 'Bač': ('Bački', 'Bačka', 'Bačko'),
          'Sr': ('Sremski', 'Sremska', 'Sremsko', 'Sremske'), 'Srem': ('Sremski', 'Sremska', 'Sremsko', 'Sremske'),
          'S': ('Sremski', 'Sremska', 'Sremsko', 'Sveti', 'Sveta'), 'D': ('Donji', 'Donja', 'Donje'), 'G': ('Gornji', 'Gornja', 'Gornje'),
          'N': ('Novi', 'Nova', 'Novo'), 'Sv': ('Sveti', 'Sveta'), 'Loz': ('Lozničko',)}


def known_place(name: str, known) -> str:
    """'Ban. Karađorđevo' -> 'Banatsko Karađorđevo', 'Kariovčić' -> 'Karlovčić', 'Sr. Mitrovjca' -> 'Sremska Mitrovica':
    the form the other units know; else as printed."""
    m = re.match(r'^(\w+)\.\s*(.+)$', name)
    cands = [f'{full} {m.group(2)}' for full in PREFIX.get(m.group(1), ())] if m else []
    for i, ch in enumerate(name):                                            # one letter misread: i/l, j/i, c/e
        for a, b in (('i', 'l'), ('l', 'i'), ('j', 'i'), ('c', 'e'), ('e', 'c'), ('I', 'l')):
            if ch == a:
                cands.append(name[:i] + b + name[i + 1:])
    cands = [c for c in cands if known.get(c)]
    if known.get(name) and not m:
        return name
    return max(cands, key=lambda c: known[c]) if cands else name


def places(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    import extract_structured_fields as esf
    known = esf.build_extractor({k: v for k, v in esf.load_live().items() if k != 82}).places      # the other units' places
    for s in soldiers:
        parts = s.pop('_places', [])
        if parts:
            s['birth_place'] = ', '.join(dict.fromkeys(known_place(p, known) for p in parts))
    return soldiers


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "zemlj- oradnik"
    text = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', text)
    text = re.sub(rf'(?<=[{U}])0(?=[{U}])', 'O', text)
    text = re.sub(rf'^([{U}]{{2,}}),\s*(rođ\.\s+[^,]+)', r'\1 \2', text)    # "RAJINAC, rođ. DIMIĆ Miladina Radoslavka."
    text = re.sub(r'^([^,]*?[^\s,\d])[.,]?\s+(1[89]\d\d\b)', r'\1, \2', text, count=1)   # "AMBROZI Pavel 1922,", "TADIĆ Miomir. 1924"
    head, _, rest = text.partition(',')
    rest = rest.strip()
    notes = []
    head = re.sub(r'\s+-?(?:rođ\.|rođena|rod\.|udova|udata)\s+([A-ZČĆŽŠĐ][\w/\'’-]*)',
                  lambda m: notes.append(('udova ' if 'udov' in m.group(0) else 'rođ. ') + re.sub(r"[/'’]", '', m.group(1)).title()) or '', head)
    head = re.sub(r'\bdr\.?\s+', lambda m: notes.append('dr') or '', head)                     # "KRSTIĆ dr Stanko"
    head = re.sub(rf'^([{U}]{{2,}}) ([ĆČŽŠĐ])(?=\s)', r'\1\2', head)                            # "KOLARI Ć Tončika"
    head = re.sub(rf'\b([{U}][{L}]+) ([{L}]{{1,4}})\b', r'\1\2', head)                           # "Dimitri je", "Fran ja"
    head = re.sub(rf'(?<=\s)[\'"„“»«`]+|[\'"„“»«`!^\\]+(?=\s|$)', '', head)                     # '"Petar', "Džema!"
    head = re.sub(rf'(?<=\s)([šžčćđ])(?=[{L}]{{2}})', lambda m: m.group(1).upper(), head)       # "žika" = Žika
    head = head.rstrip(' .')
    head = re.sub(r'\s*\(([^)]+)\)', lambda m: notes.append('zvani ' + m.group(1).strip()) or '', head)   # "(Bata)"
    head = re.sub(r'\s*[»"„]([^«"“]+)[«"“]', lambda m: notes.append('zvani ' + m.group(1).strip()) or '', head)
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})?', toks[0]):
        caps.append(toks.pop(0))
    father = ''
    if len(toks) >= 2 and re.fullmatch(rf'(?:[{U}]|Dž|Lj|Nj|DŽ|LJ|NJ)\.?', toks[0]):
        father = toks.pop(0).rstrip('.').title() + '.'                       # "ADAMOV Ž. Radica", "OSTOJIĆ M Todor"
    if not toks and len(caps) >= 2:
        given = caps.pop()                                                   # "ALIĆ RAMO"
    elif len(toks) >= 2 and not father:
        father, given = toks[0], toks[1]                                     # "AĆIMOVIĆ Jove Sava"
        if len(toks) > 2:
            notes.append('zvani ' + ' '.join(toks[2:]))
    else:
        given = toks[0] if toks else ''
        if len(toks) > 1:
            notes.append('zvani ' + ' '.join(toks[1:]))
    last = ''.join(caps) if any(len(c) <= 3 for c in caps) and len(caps) > 1 else ' '.join(caps)   # "TAN KO VIĆ"
    rec = _record(last, given.title() if given.isupper() else given, father, '; '.join(notes + ([rest] if rest else [])))
    rest2 = re.sub(r'^(1[89]\d\d)\.\s+', r'\1, ', re.sub(r'^rođ\.\s+[^,]*,\s*', '', rest))   # "1922. Novo Selo"
    rest2 = re.sub(r'\b(Sv|St|Sr|Si|Vel|Vcl|Ban|Bos|Bač|Srem|Mal|Loz|[NDGSBT])\.\s*', r'\1§', rest2)   # "Sv. Đurađ" stays one word
    parts = [p.strip().replace('§', '. ') for p in re.split(r'[,;]|\.\s+(?=[A-ZČĆŽŠĐ])', rest2)]   # some pages print "Lelić. Valievo"
    if parts and re.fullmatch(r'1[89]\d\d\.?', parts[0]):
        rec['birth_year'] = parts[0].rstrip('.')
        parts = parts[1:]
    places = []
    for p in parts[:2]:
        p = re.split(r'\s+(?=(?:zemlj|radnik|borac|bolničar|domaćica|đak|učeni|desetar|vodnik|komandir|komesar|pol\.|referent|student|službenik|nadničar)\w*)', p)[0]
        p = re.split(r'\.\s+(?=[a-zčćžšđ])', p)[0]                             # "Šid. mašinbravar"
        p = re.sub(r'^([šžčćđ])', lambda m: m.group(1).upper(), p.strip().rstrip('.^'))    # "šid" = Šid
        if re.fullmatch(rf'[{U}][{L}]*\.?(?:[\s-]+[{U}{L}][{L}]+\.?)*', p) and not re.match(r'(?:SKOJ|KPJ)', p):
            places.append(place(p))
        else:
            break
    if places:
        rec['_places'] = places
    dt = death_type_from_text(rest)
    if dt:
        rec['death_type'] = dt
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/5-vojvodjanska.pdf',
        brigade_code=82,
        output_path='website/public/5-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=places,
    )
