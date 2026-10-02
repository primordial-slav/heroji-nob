"""
Parser: 15. srpska NOU brigada (brigade code 86).

Source: Vojislav Nikčević, "Petnaesta srpska brigada" (znaci.org 00003/477.pdf, its pages 156-174, book pp. 155-173)
        →  website/public/pdfs/15-srpska.pdf. Cyrillic, three lists:
    pp. 1-12    "Spisak boraca i rukovodilaca 15. srpske brigade", names only, two columns, the father's initial after
                the given name:  Avramović Stojan V.
    pp. 13-16   "Spisak poginulih boraca i rukovodilaca", a hanging indent:
                    VELIČKOVIĆ Cvetana DUŠAN, rođen 1908, S. Jasenica, Dobrič, borac 2. čete, 4. bataljona, poginuo
                    27. jula 1944, Leskovac.
    pp. 17-19   "Spisak ranjenih boraca i rukovodilaca", in the same form ("ranjen 9. septembra 1944, kod Leskovca").
The roster holds everyone, so a fallen or wounded soldier is in it too. Л is read as J1 ("VJ1ADIMIR"). A soldier
known by one name ("VLADA (harmonikaš) iz Toplice") keeps an empty surname.
"""
import re

from _parser_scaffold import _record, death_type_from_text, extract_lines_single_column, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROSTER_TO, WOUNDED_FROM = 12, 17


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    return columns_reader(2)(pdf_path, 1, ROSTER_TO) + extract_lines_single_column(pdf_path, ROSTER_TO + 1, end_page)


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
    t = re.sub(rf'(?<=[{U}])J1|J1(?=[{U}])', 'L', t).replace('J1', 'L').replace('j1', 'l')   # Л read as J1
    if re.fullmatch(r'[\d\W]{1,5}|\W*\w{0,2}\W*', t) or ln['y'] < 125 or t.startswith('*') or re.match(r'^\*?\s*(?:Spisak|Podaci|Ovaj spisak)', t):
        return False                                                         # headings, footnotes, page numbers
    if ln['y'] > 555:
        return False                                                         # the footnotes under each list
    if ln['page'] <= ROSTER_TO:
        t = re.sub(r'^[•·&\W]+(?=\w)', '', t)                                 # "•Marković"
        t = re.sub(rf'^(\S*?[{L}])([{U}][{L}])', r'\1 \2', t)                  # "ČičićMihajlo"
        t = re.sub(r'\bJT(?=[a-z])', 'L', t)                                    # "JTazar" (Л)
        if not re.fullmatch(rf'[{U}]\S*(?:\s+(?:dr\.?|[-–]|[{U}(„"]\S*|\d\.)){{1,5}}', t):
            return False                                                     # the note under the list's heading
        ln['text'] = '§r§ ' + t
        return True
    if ln['x'] <= margin(ln) + 5 and re.match(rf'^[{U}]{{2,}}', t):
        t = ('§w§ ' if ln['page'] >= WOUNDED_FROM else '§p§ ') + t
    ln['text'] = t
    return True


def roster(text: str) -> dict:
    notes = []
    if re.search(r'\bdr\.?\s', text):
        notes.append('dr')
        text = re.sub(r'\bdr\.?\s+', '', text)
    text = re.sub(r'(?<=\s)3\.(?=\s|$)', 'Z.', text)                           # the initial З read as the digit
    father = ''
    m = re.search(r'\s+[-–]\s*(.+)$', text)                                 # a nickname after a dash: "Dedić Živojin - Žika R."
    if m:
        nick = m.group(1).strip(' „"“')
        f = re.search(rf'\s*\b((?:[{U}]|Lj|Nj|Dž|St|Bl)\.)$', nick)
        if f:
            father, nick = f.group(1), nick[:f.start()].strip()
        if nick:
            notes.append('zvani ' + nick)
        text = text[:m.start()]
    toks = text.split()
    if not father and len(toks) > 2 and re.fullmatch(rf'(?:[{U}]|Lj|Nj|Dž|St|Bl)\.?', toks[-1]):
        father = toks.pop()
    last = toks[0] if toks else ''
    given = toks[1] if len(toks) > 1 else ''
    if len(toks) > 2:
        notes.append('zvani ' + ' '.join(toks[2:]))
    return _record(last, given, father.rstrip('.') + '.' if father else '', '; '.join(notes))


def bio(text: str, kind: str) -> dict:
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "kurir- ski"
    text = re.sub(r'\s*\(nadimak\)', '', text)                                # "BORA - Bombaš (nadimak)"
    text = re.sub(r'(?<![,\s])\s+(?=rođen[a]?\s)', ', ', text, count=1)       # "MIJGUŠA rođena 1924"
    head, _, rest = text.partition(',')
    notes = []
    if re.search(r'\bdr\.?\s', head):
        notes.append('dr')
        head = re.sub(r'\bdr\.?\s+', '', head)
    m = re.search(r'\s*\(([^)]+)\)', head)                                   # "VLADA (harmonikaš)"
    if m:
        notes.append('zvani ' + m.group(1).strip())
        head = head[:m.start()] + head[m.end():]
    m = re.search(rf'\s+-\s*([{U}][{L}]+(?:\s+\(nadimak\))?)', head)          # "BORA - Bombaš (nadimak)"
    if m:
        notes.append('zvani ' + m.group(1).replace('(nadimak)', '').strip())
        head = head[:m.start()]
    m = re.search(r'\s+(iz\s+.+)$', head)                                    # "VLADA iz Toplice"
    if m:
        rest = m.group(1) + (', ' + rest if rest else '')
        head = head[:m.start()]
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})?', toks[0]):
        caps.append(toks.pop(0))
    father = toks.pop(0) if toks and re.fullmatch(rf'[{U}][{L}]*\.?', toks[0]) else ''
    rest_given = ' '.join(toks)
    if caps and (len(caps) >= 2 or father or rest_given):
        last, given = caps[0], ' '.join(caps[1:] + ([rest_given] if rest_given else []))   # "AVRAMOVIĆ V. STOJAN"
    else:
        last, given = '', (caps[0] if caps else '')                          # "VLADA (harmonikaš)": one name
    rec = _record(last or '§', given, father, '; '.join(notes + ([rest.strip()] if rest.strip() else [])))
    y = re.search(r'rođen[a]?\s+(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.match(rf'\s*rođen[a]?\s+(?:1[89]\d\d)?,?\s*(?:u\s+)?([{U}][^,]*?)(?:,\s*([{U}][^,]*?))?,\s*(?=[{L}])', rest)
    if b:
        rec['_birth'] = [p.strip() for p in b.groups() if p]
    if kind == 'p':
        rec['death_type'] = death_type_from_text(rest) or 'poginuo'
    return rec


def parse(text: str) -> dict:
    kind = text[1]
    text = re.sub(r'^§\w§\s*', '', text)
    return roster(text) if kind == 'r' else bio(text, kind)


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        if s['last_name'] == '§':                                            # a soldier known by one name
            s['last_name'] = ''
            s['full_name'] = ' '.join(p for p in (s['middle_name'], s['first_name']) if p)
        parts = s.pop('_birth', None)
        if parts:
            s['birth_place'] = ', '.join(parts)                              # "G. Brijanje, Bojnik", as printed
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/15-srpska.pdf',
        brigade_code=86,
        output_path='website/public/15-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=re.compile(r'^§\w§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
    )
