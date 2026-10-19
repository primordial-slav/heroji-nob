"""
Entries glued into the one before, in units whose parser missed a heading: the next man's heading and bio stayed in
another man's text ("... borac. BEATOVIK - ŠEVKUŠIK JOVANKA, rođena 1925. godine ..."). Each case is read by hand
from the record's text and listed in SPLITS below: the host keeps its text up to the first glued heading (an edit;
for an entry merged into another record it lands in that record's other_sources), each glued man becomes a record of
the host's unit (an add) with the name as the heading prints it, put in the unit's spelling where the scan garbled it
("PETROVIN" = Petrović, "NNKOANR" = Nikolić), his text from his heading to the next, and his place on the page: the
heading's surname in capitals, the first after the host's start in reading order (the next column, then the next
page). Page furniture glued in between (a list's title, a number) is cut off (JUNK). The boxes are drawn by
entry_boxes.py from the new starts; in a list whose parser draws them (entry_boxes.INLINE_ENTRIES: the Proleterski
bataljon Bosanske krajine's Karasijević) the new record has none and the host keeps its box.
Found with a scan for capitals after a sentence's end (see CLAUDE.md, Known OCR Issues); done on 2026-10-17.
Usage, from the project root: python scripts/split_glued_entries.py --range=LO-HI [--write]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'data-extraction'))
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber  # noqa: E402

from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

R = 'the entry was glued into the one before (its heading missed by the parser), read from the record and the page, 2026-10-17'
# unit data file: {host id: [(heading as in the text, last, father as printed, father in the nominative, given, nickname)]}
SPLITS = {
    '1-dalmatinska-soldiers.json': {
        '0036011112': [('MANDIC Vida GLIGORIJE GLIGO', 'Mandić', 'Vida', 'Vido', 'Gligorije', 'Gligo')],
        '0036012014': [('VOJVODIĆ Feda DIMITRIJE ZEKO', 'Vojvodić', 'Feda', 'Fedo', 'Dimitrije', 'Zeko')],
        '0036010050': [('BILIC Jovana BOZO MARIJAN', 'Bilić', 'Jovana', 'Jovan', 'Božo', 'Marijan'),
                       ('BOGDAN Marka PETAR PEKO', 'Bogdan', 'Marka', 'Marko', 'Petar', 'Peko'),
                       ('CETKOVIC Tome PETAR PERO', 'Ćetković', 'Tome', 'Tomo', 'Petar', 'Pero')],
        '0036010519': [('ĐAPIC Nikole ĐURO BUKETA', 'Đapić', 'Nikole', 'Nikola', 'Đuro', 'Buketa'),
                       ('GALIC Marjana JURE VELIKI', 'Galić', 'Marjana', 'Marjan', 'Jure', 'Veliki'),
                       ('IVAN GUVO', 'Guvo', '', '', 'Ivan', '')],
        '0036011514': [('REIC Ante SREČKO PETICA', 'Reić', 'Ante', 'Ante', 'Srećko', 'Petica'),
                       ('ROMAC Radeta PASKO ZDRAVKO', 'Romac', 'Radeta', 'Rade', 'Paško', 'Zdravko'),
                       ('SCEKIC Gavra VLADIMIR VLADO', 'Šćekić', 'Gavra', 'Gavro', 'Vladimir', 'Vlado')],
    },
    '11-dalmatinska-soldiers.json': {
        '0053000195': [('BAČIĆ (Mate) SREĆKO', 'Bačić', 'Mate', 'Mate', 'Srećko', ''),
                       ('BADELJ (Ivana) VLADIMIR', 'Badelj', 'Ivana', 'Ivan', 'Vladimir', ''),
                       ('BALIĆ (Jakova) DINKO', 'Balić', 'Jakova', 'Jakov', 'Dinko', ''),
                       ('BALOLJ (Ivana) IVAN', 'Balolj', 'Ivana', 'Ivan', 'Ivan', ''),
                       ('BANDALOVIĆ (Jure) ANDRIJA', 'Bandalović', 'Jure', 'Jure', 'Andrija', ''),
                       ('BANDELJ (Angela) ALOJZ', 'Bandelj', 'Angela', 'Angel', 'Alojz', ''),
                       ('BANDELJ (Alojza) ANGEL', 'Bandelj', 'Alojza', 'Alojz', 'Angel', '')],
        '0053000966': [('GREGOV (Silvestra) JOSIP-Moreto', 'Gregov', 'Silvestra', 'Silvestar', 'Josip', 'Moreto')],
        '0053001123': [('JURIĆ (Petra) NIKOLA', 'Jurić', 'Petra', 'Petar', 'Nikola', ''),
                       ('LIVEŠĆEK (Ivana) STANKO', 'Livešček', 'Ivana', 'Ivan', 'Stanko', ''),
                       ('MARENTA (Jakova) MILKO', 'Marenta', 'Jakova', 'Jakov', 'Milko', ''),
                       ('OLIVADIĆ LUKA', 'Olivadić', '', '', 'Luka', ''),
                       ('PETROSIĆ (Luke) IVAN', 'Petrosić', 'Luke', 'Luka', 'Ivan', ''),
                       ('RAŽNJEVIĆ ŠIME', 'Ražnjević', '', '', 'Šime', ''),
                       ('RIZZO (Carmelov) GIOVANNI', 'Rizzo', 'Carmelov', 'Carmelo', 'Giovanni', ''),
                       ('ROKI JURAJ', 'Roki', '', '', 'Juraj', ''),
                       ('ROSIĆ (Tode) TODOR', 'Rosić', 'Tode', 'Todo', 'Todor', ''),
                       ('STIPANOVIĆ ANDRIJA', 'Stipanović', '', '', 'Andrija', ''),
                       ('ŠPILJAK (Ecilijin) FILIP', 'Špiljak', 'Ecilijin', 'Ecilija', 'Filip', ''),
                       ('TOMASIĆ (Marina) MARIN', 'Tomasić', 'Marina', 'Marin', 'Marin', ''),
                       ('VRŽINA (Filipa) ANTE', 'Vržina', 'Filipa', 'Filip', 'Ante', ''),
                       ('VUKELIC (Joze) MATO', 'Vukelić', 'Joze', 'Jozo', 'Mato', ''),
                       ('ZAMBULIN (Andrije) NIKOLA', 'Zambulin', 'Andrije', 'Andrija', 'Nikola', ''),
                       ('ŽANETIĆ FRANE', 'Žanetić', '', '', 'Frane', '')],
        '0053002909': [('URLIČ (Šimuna) ANTE', 'Urlić', 'Šimuna', 'Šimun', 'Ante', '')],
    },
    '12-srpska-soldiers.json': {'0090000426': [('LEPOJEVIĆ Ljubomira MILORAD', 'Lepojević', 'Ljubomira', 'Ljubomir', 'Milorad', '')]},
    '15-majevicka-soldiers.json': {'0049011911': [('ŠAŠKINOVIC (Mileka) MIKAJLO', 'Šaškinović', 'Mileka', 'Milek', 'Mikajlo', '')]},
    '19-bircanska-soldiers.json': {
        '0023000098': [('BEATOVIK - ŠEVKUŠIK JOVANKA', 'Beatović-Ševkušić', '', '', 'Jovanka', '')],
        '0023000132': [('BILIB - JOKIB DANILA OLGA', 'Bilić-Jokić', 'Danila', 'Danilo', 'Olga', '')],
        '0023000771': [('KRSTIK - KOSARIK MILUNKA', 'Krstić-Kosarić', '', '', 'Milunka', '')],
        '0023000932': [('MEBIKOVIK - KOMORAŠ BAJRE FATIMA', 'Mehiković-Komoraš', 'Bajre', 'Bajro', 'Fatima', '')],
        '0023001368': [('PRODANOVIK - PERIK SAVE DANICA', 'Prodanović-Perić', 'Save', 'Savo', 'Danica', '')],
    },
    '22-srpska-soldiers.json': {
        '0074000414': [('KRSTIĆ Uroša MILOSAV', 'Krstić', 'Uroša', 'Uroš', 'Milosav', '')],
        '0074001210': [('ĐEEKOVIĆ Radomira MILOSAV', 'Đeković', 'Radomira', 'Radomir', 'Milosav', '')],
    },
    '23-srpska-soldiers.json': {'0089000469': [('NNKOANR Vladimira DRAGIVOJE', 'Nikolić', 'Vladimira', 'Vladimir', 'Dragivoje', '')]},
    '3-krajiska-proleterska-soldiers.json': {'0010204167': [('RANCIC (Rajšić) MILOŠ', 'Rančić', '', '', 'Miloš', '')]},
    '4-proleterska-soldiers.json': {
        '0040010241': [('DUBLJEVIĆ M. ŽARKO', 'Dubljević', 'M.', '', 'Žarko', '')],
        '0040010401': [('GUBEROVIĆ B. VUKAŠIN', 'Guberović', 'B.', '', 'Vukašin', '')],
        '0040011381': [('RADOVIĆ R. DRAGOJE', 'Radović', 'R.', '', 'Dragoje', '')],
        '0040011944': [('ĐUKIĆ M. MILOSAV', 'Đukić', 'M.', '', 'Milosav', '')],
    },
    '5-srpska-soldiers.json': {'0127000396': [('IMILENKOVIN Tihomira SAVA', 'Milenković', 'Tihomira', 'Tihomir', 'Sava', '')]},
    '6-dalmatinska-soldiers.json': {
        '0103000081': [('EVELJA ANTE', 'Evelja', '', '', 'Ante', '')],
        '0103000095': [('GOCLIO ANTE', 'Goclio', '', '', 'Ante', '')],
        '0103000250': [('PURCINOV NIKOLA', 'Purcinov', '', '', 'Nikola', '')],
    },
    '7-krajiska-soldiers.json': {'0048013526': [('VASILJEVIĆ Ilije ĐORĐE', 'Vasiljević', 'Ilije', 'Ilija', 'Đorđe', '')]},
    '8-krajiska-soldiers.json': {'0014010471': [('KUKIČ (D2) MEHMED', 'Kukić', '', '', 'Mehmed', '')]},
    'druga-licka-soldiers.json': {
        '0003013290': [('RASETA -PLEĆAS LAZE SARA', 'Rašeta-Plećaš', 'Laze', 'Lazo', 'Sara', '')],
        '0003013960': [('VIGNJEVIĆ - DRAĆA NIKOLE DUKA', 'Vignjević-Draća', 'Nikole', 'Nikola', 'Duka', '')],
        '0003014200': [('ZORIC - JAG LICA PERE DOBRI NKA DOJA', 'Zorić-Jaglica', 'Pere', 'Pero', 'Dobrinka', 'Doja'),
                       ('ZORIC - TRSTENJAK JOVE MARA', 'Zorić-Trstenjak', 'Jove', 'Jovo', 'Mara', ''),
                       ('ZRNIĆ - VORKAPIC MILICA', 'Zrnić-Vorkapić', '', '', 'Milica', '')],
    },
    'kalnicki-odred-soldiers.json': {'0058003188': [('STIMEC FRANJO', 'Štimec', 'Matije', 'Matija', 'Franjo', '')]},
    'mosorski-odred-soldiers.json': {
        '0148001449': [('LEKŠIĆ Ante MATE', 'Lekšić', 'Ante', 'Ante', 'Mate', '')],
        '0148001512': [('LONČAR Simuna IVAN', 'Lončar', 'Simuna', 'Šimun', 'Ivan', '')],
    },
    'mostarski-bataljon-soldiers.json': {
        '0125000313': [('DŽEVAD M. JUSUFBEGOVIĆ', 'Jusufbegović', 'M.', '', 'Dževad', '')],
        '0125000370': [('AISA O. KRPO', 'Krpo', 'O.', '', 'Aisa', '')],
        '0125000526': [('2IVKO G. PAPO HENĆI', 'Papo', 'G.', '', 'Živko', 'Henći')],
    },
    'osjecka-soldiers.json': {'0104000527': [('IVANOVIC-KARIC Mladena SAVO', 'Ivanović-Karić', 'Mladena', 'Mladen', 'Savo', '')]},
    'posavski-odred-soldiers.json': {
        '0110001656': [('PETROVIN Živane ŽIVKO', 'Petrović', 'Živane', 'Živana', 'Živko', '')],
        '0110001838': [('RANKOVIE Janka ŽIVORAD', 'Ranković', 'Janka', 'Janko', 'Živorad', '')],
        '0110002306': [('VLAJKOVIN', 'Vlajković', '', '', 'Milka', '')],
    },
    'proleterski-bataljon-bk-soldiers.json': {'0163000126': [('KARASIJEVIĆ J. DRAGO', 'Karasijević', 'J.', '', 'Drago', '')]},
    'toplicki-odred-soldiers.json': {'0093000075': [('RATOMIR VUKAŠINOVIĆ JANIĆIJE', 'Vukašinović', '', '', 'Ratomir', 'Janićije')]},
    'treca-proleterska-soldiers.json': {'0005010459': [('KOSOVIK GAVRO', 'Kosović', '', '', 'Gavro', '')]},
}
# what a heading's own words leave in the man's text: the name's rest up to the bio
NAME_TAIL = re.compile(r'^\s*(?:\((?:VESIN|Rajšić)\)\s*)?(?:MILKA\s*)?')
# page furniture glued in between: a list's title, an entry's number, a speck
JUNK = [r'\s*AESTE DALMATINSKE BRIGADE LI BORCI$', r'\s*PREŽIVJELI BO \(na dan 15\.$', r'\s*[:•«]\s*\d{1,3}\.$',
        r'\s*-i\.$', r'\s*I$', r'\s*N E M C I :$']


def cleaned(text: str) -> str:
    text = text.strip()
    for p in JUNK:
        text = re.sub(p, '', text).strip()
    return text


def fold(s: str) -> str:
    return re.sub(r'[^A-Z]', '', s.upper().translate(str.maketrans('ČĆŽŠĐ', 'CCZSD')))


_pages = {}


def words(pdf_file: str, page: int) -> list:
    key = (pdf_file, page)
    if key not in _pages:
        with pdfplumber.open(ROOT / 'website' / 'public' / 'pdfs' / pdf_file) as pdf:
            _pages[key] = viewer_words(pdf.pages[page - 1]) if page <= len(pdf.pages) else []
    return _pages[key]


def find(host: dict, heading: str, after: tuple) -> tuple:
    """(page, x, y, box words) of the heading's first word in capitals: the first after `after` (page, column, y) in
    reading order, the columns of a page split at its middle"""
    for first in (heading.split()[0].rstrip(','), heading.split()[-1].rstrip(',')):   # the surname, else the given name
        hit = _find(host, first, after)                                # (the scan's ДУБЈБЕВИЋ for Dubljević)
        if hit:
            return hit
    raise SystemExit(f"not found: {heading} after {after} in {host['pdf_file']}")


def _find(host: dict, first: str, after: tuple):
    for p in range(host['pdf_page'], host['pdf_page'] + 9):          # a bio can run over pages
        ws = words(host['pdf_file'], p)
        if not ws:
            continue
        mid = (min(w['x0'] for w in ws) + max(w['x1'] for w in ws)) / 2
        if len(after) == 4:                                            # the host's place: (page, x, y, 'host')
            after = (after[0], after[1] > mid, after[2] + 3)            # below the host's own heading, in its column
        cands = []
        for w in ws:
            t = cyrillic_to_latin(w['text']).rstrip(',.').replace('l', 'I')   # "ĐAPlC": the scan's l for I in capitals
            if t == first or (t.isupper() and len(t) > 2 and fold(t) == fold(first)):
                order = (p, w['x0'] > mid, w['top'])
                if order > after:
                    cands.append((order, w))
        if cands:
            order, w = min(cands, key=lambda c: c[0])
            # the line's start in that column ("•21. GUBEROVIĆ", or the given name the fallback found)
            line = [v for v in ws if abs(v['top'] - w['top']) < 2 and (v['x0'] > mid) == (w['x0'] > mid) and v['x0'] <= w['x0']]
            return order, round(min(v['x0'] for v in line), 1), round(w['top'], 1)
    return None


def main():
    lo, hi = [int(v) for v in next(a for a in sys.argv if a.startswith('--range=')).split('=')[1].split('-')]
    corr = json.load(open(ROOT / 'corrections.json', encoding='utf-8'))
    nid = max([c['id'] for c in corr if lo <= c['id'] <= hi] + [lo - 1]) + 1
    taken = {c.get('new_id') for c in corr if c['action'] == 'add'}
    new = []
    for unit_file, hosts in SPLITS.items():
        recs = json.load(open(ROOT / 'website' / 'public' / unit_file, encoding='utf-8'))
        code = recs[0]['soldier_id'][:4]
        used = {s['soldier_id'] for s in recs} | {o.get('soldier_id') for s in recs for o in s.get('other_sources', ())} | taken
        found = {}
        for s in recs:
            for e in [s] + [o for o in s.get('other_sources', ()) if not o.get('unit_file') and not o.get('ref_book')]:
                if e.get('soldier_id') in hosts:
                    found[e['soldier_id']] = (s, e)
        for hid, men in hosts.items():
            keeper, host = found[hid]
            info = host['additional_info']
            pos = []
            for heading, *_ in men:
                i = info.find(heading, pos[-1] + 1 if pos else 0)
                assert i > 0, (hid, heading)
                pos.append(i)
            new.append({'action': 'edit', 'soldier_id': hid, 'fields': {'additional_info': cleaned(info[:pos[0]])},
                        'reason': f"{host.get('full_name') or host.get('name')}: the next entries were glued into its text; {R}"})
            after = (host['pdf_page'], host['pdf_x'], host['pdf_y'], 'host')
            # the glued men take ids in the host's list's block, from 9001 (0053000195 -> 0053009001-)
            block = int(hid[4:]) // 10000 * 10000
            for k, (heading, last, fgen, fnom, given, nick) in enumerate(men):
                body = info[pos[k] + len(heading):(pos[k + 1] if k + 1 < len(men) else len(info))]
                body = cleaned(NAME_TAIL.sub('', body).lstrip(' ,'))
                if heading == 'STIMEC FRANJO':
                    body = re.sub(r'^Matije,\s*', '', body)
                if nick:
                    body = f'zvani {nick}; {body}'
                order, x, y = find(host, heading, after)
                after = order
                rec = {'last_name': last, 'middle_name': fgen, 'fathers_name': fnom, 'first_name': given,
                       'additional_info': body, 'pdf_file': host['pdf_file'], 'pdf_page': order[0], 'pdf_x': x, 'pdf_y': y}
                seq = block + 9001
                while f'{code}{seq:06d}' in used:
                    seq += 1
                new_id = f'{code}{seq:06d}'
                used.add(new_id)
                new.append({'action': 'add', 'soldier_id': keeper['soldier_id'], 'new_id': new_id, 'record': rec,
                            'reason': f"{last} {fgen + ' ' if fgen else ''}{given}: glued into the entry of "
                                      f"{host.get('full_name') or host.get('name')}; {R}"})
                print(new_id, last, fgen, given, nick, f"p{order[0]} x{x} y{y}", '|', body[:70])
    for i, c in enumerate(new):
        c['id'] = nid + i
    assert nid + len(new) - 1 <= hi, 'past the range'
    print(len(new), 'corrections,', sum(c['action'] == 'add' for c in new), 'men')
    if '--write' in sys.argv:
        corr += new
        open(ROOT / 'corrections.json', 'w', encoding='utf-8', newline='\n').write(json.dumps(corr, ensure_ascii=False, indent=2) + '\n')
        print('written', new[0]['id'], '-', new[-1]['id'])


if __name__ == '__main__':
    main()
