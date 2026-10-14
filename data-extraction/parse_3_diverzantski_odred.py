"""
Parser: Treći diverzantski odred (brigade code 161).

Source: Vukašin Karanović, "Treći diverzantski odred" (znaci.org 00003/541.pdf), Prilog IV
        →  website/public/pdfs/3-diverzantski-odred.pdf (book pp. 587-591):
    pp. 1-5     "Pregled boraca i starješina Trećeg diverzantskog odreda": everyone of the 3. diverzantska grupa,
                četa, bataljon and odred, names only, two columns, "BREZAK MILAN**," (** the fallen; "*" the book
                doesn't explain, kept as printed)
    p. 5        "Pregled poginulih diverzanata": "BREZAK MILAN, Desetar 1944. Borac 1945." Each is a man of the
                roster: his duty and the year go into his record, which the list marks fallen.
"""
import re
import unicodedata
from difflib import SequenceMatcher

from _parser_scaffold import _record, extract_lines_two_column, run_parser, title_case

U = 'A-ZČĆŽŠĐ'
FALLEN_PAGE, FALLEN_FROM_Y = 5, 290


def fold(text: str) -> str:
    t = (text or '').lower().replace('đ', 'dj')
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', t)


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    split = {}                                                               # the columns stand elsewhere on every page
    for p in {ln['page'] for ln in lines}:
        xs = sorted(ln['x'] for ln in lines if ln['page'] == p and re.match(rf'^[{U}]{{2}}', ln['text'].strip()))
        left = xs[len(xs) // 10]
        right = min((x for x in xs if x > left + 100), default=left + 200)
        split[p] = right - 30                                                # "Desetar 1944." / "čete 1944." under the left entry
    lines.sort(key=lambda l: (l['page'], l['x'] > split[l['page']], l['y']))
    parts = []
    for ln in lines:                                                         # "GULIĆ FRANJO*, GÜSTIN JOSIP": two names a line
        t = re.sub(r'^,\s*', '', ln['text'].strip().replace('"', '').replace('/', ''))   # ", FIJAČKO FRANJO," split off
        if ln['page'] == FALLEN_PAGE and ln['y'] > FALLEN_FROM_Y:
            parts.append((ln, t))
        else:
            parts += [(ln, x.strip()) for x in re.split(rf',\s+(?=[{U}][{U}Üü])', t) if x.strip()]
    out = []
    for ln, t in parts:
        fallen = ln['page'] == FALLEN_PAGE and ln['y'] > FALLEN_FROM_Y
        if re.fullmatch(r'[\d\W]{1,5}|P|PRILOG IV|R E G L ED|P RE|G L E D|POGINULIH|DIVERZANATA|Pog\.', t) \
                or re.match(r'^(?:BORACA I STARJEŠINA|TREĆEG DIVERZANTSKOG|\*)', t):     # "* Umro poslije rata": the key
            continue
        if ln['page'] == FALLEN_PAGE and ln['y'] > 540:
            continue                                                         # the editor's note under the lists
        starts = re.match(rf'^[{U}][{U}1Ü]+(?:[\s-]|\*|,|$)', t)               # "GÜSTIN JOSIP" and not re.match(r'^\d|^[A-Z]-dir|^3\. DIVER', t)
        if fallen and not re.match(rf'^[{U}][{U}]+\s+(?:[{U}]\.\s+)?[{U}(]', t):
            starts = False                                                   # "SALIH-SALKO, Zastavnik": the line before goes on
        if starts and fallen and re.match(rf'^SALIH-SALKO', t):
            starts = False
        kind = 'f' if fallen else 'r'
        out.append(dict(ln, text=(f'§{kind}§ ' if starts else '') + t))
    return out


def parse_entry(text: str) -> dict:
    kind = text[1]
    text = re.sub(r'^§[rf]§\s*', '', text)
    if kind == 'r':
        mark = re.search(r'(\*+)', text)
        name = re.sub(r'\s+-', '-', re.sub(r'\*+|,\s*$|-$', '', text)).strip(' ,')   # "NEĐELJKA / -NEDA"
        note = re.search(r'\s*(\([^)]*\)|»[^«]*«)', name)                      # "ČEH (KORITNA)", "BAJA »BOSANAC«"
        extra = note.group(1) if note else ''
        name = (name[:note.start()] + name[note.end():]).strip() if note else name
        words = name.replace('1', 'I').split()
        last = title_case(words[0]) if words else ''
        given = ' '.join(title_case(w) for w in words[1:])
        given, _, alias = given.partition('-')                                 # "VULINEC FRANJO-FRANC"
        notes = ([f'zvani {alias.strip().title()}'] if alias.strip() else []) + ([extra] if extra else [])
        # the key under the first page: "* Umro poslije rata", "** Poginuo u toku NOR-a"
        if mark and len(mark.group(1)) == 1:
            notes.append('umro poslije rata')
        if mark and len(mark.group(1)) == 2:
            notes.append('poginuo u toku NOR-a')
        rec = _record(last, given.strip(), '', '; '.join(notes))
        if mark:
            rec['death_type'] = 'umro' if len(mark.group(1)) == 1 else 'poginuo'
        return rec
    m = re.match(rf'^([{U}]+(?:\s+\([{U}]+\))?)\s+(?:([{U}])\.\s+)?([{U}][{U}-]+)\s*,\s*(.*)$', text)
    if not m:
        return {}
    last = title_case(re.sub(r'\s*\(.*\)', '', m.group(1)))
    given = title_case(m.group(3).split('-')[0])                              # "SALIHOVIĆ SALIH-SALKO"
    duty = re.sub(r'\s+', ' ', m.group(4)).strip(' ,')
    rec = _record(last, given, m.group(2) or '', 'poginuo; ' + duty)
    rec['death_type'] = 'poginuo'
    years = re.findall(r'\b(19\d\d)\b', duty)
    if years:
        rec['death_date'] = years[-1]
    rec['_fallen_list'] = True
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """The list of the fallen goes into the roster's records: the man's duty and year, and his fall."""
    roster = [s for s in soldiers if not s.get('_fallen_list')]
    out = [s for s in roster]
    for s in soldiers:
        if not s.pop('_fallen_list', False):
            continue
        key = (fold(s['last_name']), fold(s['first_name']))
        cands = [r for r in roster if (fold(r['last_name']), fold(r['first_name'])) == key]
        if not cands:                                       # "BARANAČIĆ MIJO**" on the roster, "BARANČIĆ MIJO" here
            cands = [r for r in roster if r.get('death_type') == 'poginuo' and fold(r['first_name']) == key[1]
                     and SequenceMatcher(None, fold(r["last_name"]), key[0]).ratio() >= 0.7]
        if len(cands) == 1:
            r = cands[0]
            r['additional_info'] = re.sub(r'(?:; )?poginuo u toku NOR-a', '', r['additional_info'])
            r['additional_info'] = '; '.join(x for x in (r['additional_info'], s['additional_info']) if x)
            r['death_type'] = 'poginuo'
            if s.get('death_date'):
                r['death_date'] = s['death_date']
            if r['last_name'] != s['last_name']:
                r['additional_info'] += f' (u pregledu poginulih: {s["last_name"]} {s["first_name"]})'
            continue
        out.append(s)                                                         # not on the roster, or two men of the name
    return out


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/3-diverzantski-odred.pdf',
        brigade_code=161,
        output_path='website/public/3-diverzantski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[rf]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
