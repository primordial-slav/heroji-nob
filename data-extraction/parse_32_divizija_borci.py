"""
Parser: 32. Zagorska divizija (brigade code 35) — "Borci 32. divizije NOVJ", a second book.

Source: Grupa autora, "32. divizija NOVJ" (znaci.org 00003/542.pdf), chapter X "Borci 32. divizije NOVJ" (book
        pp. 431-662)  →  website/public/pdfs/32-divizija-borci.pdf (PDF pages 518-749 of the book).
Two columns, Latin, a hanging indent; by unit: 1. Štab divizije, 2. Prištapske jedinice, 3. Udarna brigada
Braća Radić, 4. Brigada Matija Gubec, 5. Brigada Mihovil Pavlek Miškina, 6. I udarna zagorska brigada, 7. Borci
s nepotpunim podacima, 8. Dopune i ispravci (more soldiers by unit, then corrections "str. 449 BEREKOVIĆ ĐURO,
dodati: ...", which are left out):
    KLEPAC IVAN, Antuna, r. 1923, s. Kloštar, Ivanić Grad, Hrvat, radnik, čl. KPJ, NOV 1941, ranjen 1943. i 1944.
The father's name (genitive) follows the given name. The unit the soldier is listed under goes to
unit_detail; the book lists a man under each unit he fought in, with all his details under the first.
The division's roster (names only, 32-divizija.pdf) is the unit's first book, IDs 1-10041; these get IDs
from 100001.
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import _record, extract_lines_two_column, repair_lj_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
SECTIONS = [
    (re.compile(r'^1\.\s+ŠTAB'), 'Štab divizije'),
    (re.compile(r'^2\.\s+PRIŠTAPSKE|^PRIŠTAPSKE JEDINICE$'), 'Prištapske jedinice'),
    (re.compile(r'^3\.\s+UDARNA BRIGADA|^Udarna Brigada BRAĆA RADIĆ$|^Udama Brigada BRAĆA RADIĆ$'), 'Udarna brigada Braća Radić'),
    (re.compile(r'^4\.\s+BRIGADA MATIJA|^Brigada MATIJA GUBEC$'), 'Brigada Matija Gubec'),
    (re.compile(r'^5\.\s+BRIGADA MIHOVIL|^Brigada MIHOVIL PAVLEK$'), 'Brigada Mihovil Pavlek Miškina'),
    (re.compile(r'^6\.\s+I\s+UDARNA|^I UDARNA ZAGORSKA$'), 'I udarna zagorska brigada'),
    (re.compile(r'^7\.\s+BORCI S NEPOTPUNIM'), 'none'),            # no unit; 'none' keeps the marker off _LEADING_JUNK
]
HEADING_REST = re.compile(r'^(?:DIVIZIJE|32\. DIVIZIJE|RADIĆ|BRAĆA|MIŠKINA|BRIGADA|PODACIMA|ISPRAVCI U OSTALIM|POGLAVLJIMA|'
                          r'8\.\s+DOPUNE I ISPRAVCI|\*\s*\*\s*\*)$')
_state = {'section': None, 'stop': False}
_margin: dict = {}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    # each column's entry starts are its leftmost lines; continuations are indented ~8 pt
    by_col: dict = {}
    for ln in lines:
        col = (ln['page'], ln['x'] > 250)
        if re.match(rf"^['‘]?[{U}]", ln['text']):
            by_col.setdefault(col, []).append(ln['x'])
    for col, xs in by_col.items():
        _margin[col] = min(xs)
    return lines


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if _state['stop'] or (ln['page'] == 1):
        return False                                                        # the chapter's note; the corrections
    if re.fullmatch(r'[\d.\s]*32\. divizija NOVJ|\d{1,3}', t):
        return False                                                        # running heads, page numbers
    for rx, name in SECTIONS:
        if rx.match(t):
            _state['section'] = name
            return False
    if HEADING_REST.match(t):
        return False
    if t.startswith('str. ') and _state['section'] is not None and ln['page'] >= 231:
        _state['stop'] = True                                               # "str. 449 BEREKOVIČ ĐURO, dodati: ..."
        return False
    margin = _margin.get((ln['page'], ln['x'] > 250), ln['x'])
    if ln['x'] <= margin + 3 and re.match(rf"^['‘]?[{U}]", t):
        t = '§' + (_state['section'] or 'none') + '§ ' + re.sub(r"^['‘]", '', t)
    ln['text'] = t
    return True


ETHNIC = {'Hrvat', 'Hrvatica', 'Srbin', 'Srpkinja', 'Slovenac', 'Slovenka', 'Musliman', 'Muslimanka', 'Mađar', 'Rus',
          'Nijemac', 'Talijan', 'Čeh', 'Slovak', 'Poljak', 'Židov', 'Jevrej', 'Ukrajinac', 'Crnogorac', 'Makedonac'}
_first: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('32-divizija-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name'].upper()] += 1


def father_nominative(w: str) -> str:
    """'Antuna' → Antun, 'Mije' → Mijo, 'Josipa' → Josip: the given name a genitive comes from, if any."""
    stem = w[:-1]
    for c in (stem, stem + 'o', stem + 'a', stem + 'e', w[:-2] + 'ij' if w.endswith('ia') else ''):
        if c and _first[c.upper()] >= 3:
            return c
    return ''


SURNAME_END = re.compile(r'(?:IĆ|IČ|AC|AK|EK|EC|OV|IN|AR|AJ|AN|ER|EŠ|UŠ|OR|UK)$')


def split_glued(tok: str) -> list[str]:
    """'BERMANECPAVAO' → BERMANEC PAVAO: the longest known given name at the end; else after a surname ending
    ('BASTIĆSIME' → BASTIĆ SIME)."""
    for k in range(3, len(tok) - 2):
        if _first[tok[k:]] >= 5 and len(tok[k:]) >= 3:
            return [tok[:k], tok[k:]]
    for k in range(len(tok) - 3, 3, -1):
        if SURNAME_END.search(tok[:k]) and re.search('[AEIOU]', tok[k:]) and len(tok[k:]) >= 3:
            return [tok[:k], tok[k:]]
    return [tok]


def parse_entry(text: str) -> dict:
    m = re.match(r'^§([^§]*)§\s*', text)
    section = m.group(1) if m and m.group(1) != 'none' else ''
    text = text[m.end():] if m else text
    text = re.sub(rf'^([{U}][{L}]+)(?=\s+[{U}]{{2,}})', lambda x: x.group(1).upper(), text)   # "Kočiš JANOŠ"
    text = re.sub(rf'^([{U}\-]+):', r'\1', text)                                             # "BABIC: ANTE"
    text = re.sub(rf'(?<=[{U}])I\.(?=[{U}])', 'L', text)                                      # "SI.AVKO"
    text = re.sub(rf'^([{U}][{U}\-() ]*[{U})])\.\s+(?=[{U}])', r'\1, ', text)                 # "BOLFAN MIRKO. Stjepana"
    text = re.sub(r'\s+(?=r\.\s*1[89]\d\d)', ', ', text, count=1) if re.match(rf'^[^,]*\sr\.\s*1[89]\d\d', text) else text
    head, _, rest = text.partition(',')
    prefix = []
    # a woman's other surname: "BARBARIČ r. HAJNIĆ JELICA" (née), "BABIĆ Antuna ud. KNEŽEVIĆ MARIJA" (married)
    wm = re.match(rf'^(.*?)\s*(r\.|rod\.|ud\.)\s*-?\s*([{U}][{U}{L}\-]+)\s+(.+)$', head)
    if wm and re.search(rf'[{U}]{{2}}', wm.group(4)):
        first_part, kind, other, given_part = wm.groups()
        prefix.append(('rođ. ' if kind in ('r.', 'rod.') else 'ili ') + other.title())
        fm = re.match(rf'^([{U}][{U}\-]+)\s+([{U}][{L}]+)$', first_part)              # "BABIĆ Antuna"
        if fm:
            head, father_inline = f'{fm.group(1)} {given_part}', fm.group(2)
        else:
            head, father_inline = f'{first_part} {given_part}', ''
    else:
        father_inline = ''
    # another spelling in brackets: "BARAK (BARAN) ALEKSANDAR", "ANIĆ SLAVKO (STANKO)"
    for am in re.finditer(r'\s*\(([^)]+)\)', head):
        prefix.append('ili ' + am.group(1).strip().title())
    head = re.sub(r'\s*\([^)]*\)?|[()]', ' ', head)
    dr = re.search(r'(?:^|\s|-)dr\.\s*', head)
    if dr:
        head = head[:dr.start()] + ' ' + head[dr.end():]
        prefix.append('dr.')
    toks = [t for t in re.split(r'[\s]+|(?<=[A-ZČĆŽŠĐ])-(?=dr)', head.strip('- ')) if t]
    if len(toks) == 1:
        toks = split_glued(toks[0])
    toks = [t.rstrip('.') if len(t) > 2 else t for t in toks]                              # "KRANJEC VILIM."
    if len(toks) == 3 and _first[toks[1] + toks[2]] >= 3:
        toks = [toks[0], toks[1] + toks[2]]                                                # "SLA VICA" = Slavica
    last, given = (toks[0], ' '.join(toks[1:])) if len(toks) >= 2 else ((toks[0] if toks else ''), '')
    gm = re.match(rf'^\s*([{U}]{{3,}})(?:,|$)', rest) if not given else None
    if gm:
        given, rest = gm.group(1), rest[gm.end():]                                         # "JURETIČ, IVAN, Franje"
    if len(toks) == 3 and _first[toks[2]] and not _first[toks[1]]:
        last, given = toks[0] + '-' + toks[1], toks[2]                                     # SEVEROVIĆ JANŽEK MILKA
    rest = rest.strip()
    if father_inline:
        rest = f'{father_inline}, {rest}'
    father = ''
    seg, sep, after = rest.partition(',')
    seg = seg.strip()
    if (re.fullmatch(rf'[{U}][{L}]+', seg) and seg.endswith(('a', 'e', 'ia')) and seg not in ETHNIC
            and father_nominative(seg)):
        father, rest = seg, after.strip()
    elif (re.fullmatch(rf'[{U}][{L}]+', seg) and seg not in ETHNIC and _first[seg.upper()] >= 10
          and re.match(r'\s*(?:r\.|s\.)', after)):
        father, rest = seg, after.strip()                                   # in the nominative: "Stjepan, r. 1920"
    if prefix:
        rest = '; '.join(prefix) + ('; ' + rest if rest else '')
    rec = _record(last, given, father, rest)
    if father:
        rec['fathers_name'] = father_nominative(father) if father.endswith(('a', 'e', 'ia')) and father_nominative(father) else father
    if section:
        rec['unit_detail'] = section
    return rec


BIRTH = re.compile(r'(?:^|,\s*)r\.\s*(1[89]\d\d)\b')


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(soldiers)                                       # "MIUENKO" = Miljenko
    for s in soldiers:
        m = BIRTH.search(s['additional_info'])
        if m and not s['birth_year']:
            s['birth_year'] = m.group(1)
    return soldiers


if __name__ == '__main__':
    import sys
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/32-divizija-borci.pdf',
        brigade_code=35,
        output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/32-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
        id_start=100001,
        keep_other_sources=len(sys.argv) <= 1,
    )
