"""
The order of battle of the NOVJ: the detachment, brigade, division and corps tables ("Pregledi") of Nikola Anić, Sekula Joksimović,
Mirko Gutić, Narodnooslobodilačka vojska Jugoslavije - pregled razvoja oružanih snaga narodnooslobodilačkog pokreta
1941-1945 (znaci.org 00003/523, book pp. 589-860), read into data-extraction/novj/: detachments.json (512 of the 556
partisan odredi: the scan lacks the spreads with rows 36-45, 394-406, 458-470 and 541-547, and row 324's first lines),
brigades.json (367), divisions.json (68: the NOVJ's, KNOJ's, air force and Italian divisions) and corps.json (18), each row with its cells as printed and
its periods (who it was under, and when) read from them; site_links.json ties the site's brigades and divisions to
their rows.

The tables are spreads of two book pages, each row started by its number in the first column; the reader finds each
column's edges on each spread (the scan shifts them up to 6 pt) and lines the right-hand page up with the left, which
sits a few points off. Row numbers the OCR dropped or misread ("SY", "225") are read back from the run of numbers.
The 86 MB book is cached in data-extraction/.cache/znaci_library/books/00003_523.pdf (git-ignored); fetch it from
https://znaci.org/00003/523.pdf if missing.

Usage: python data-extraction/read_novj_structure.py
"""
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
PDF = HERE / '.cache' / 'znaci_library' / 'books' / '00003_523.pdf'
OUT = HERE / 'novj'
UNITS_TS = HERE.parent / 'website' / 'app' / 'data' / 'units.ts'

# each table: its PDF pages, the edges between its columns (a scan shifts them up to 6 pt), the columns
TABLES = {
    'brigades': (702, 747, [45, 129, 187, 246, 298, 418, 476, 579, 634, 691],
                 ['no', 'name', 'formed', 'formed_from', 'makeup', 'changes', 'strength', 'parent', 'disbanded', 'note',
                  'sources']),
    'divisions': (748, 769, [29, 99, 155, 214, 272, 309, 400, 471, 558, 700],
                  ['no', 'name', 'formed', 'from_brigades', 'from_units', 'strength', 'parent', 'strength_changes',
                   'composition', 'arms', 'sources']),
    'detachments': (657, 701, [44, 152, 212, 280, 322, 410, 503, 588, 648, 700],
                    ['no', 'name', 'formed', 'place', 'strength', 'makeup', 'parent', 'disbanded', 'reorganized', 'note',
                     'sources']),
    'corps': (780, 787, [26, 86, 145, 203, 261, 319, 410, 470, 529, 581, 702],
              ['no', 'name', 'formed', 'subordinate', 'divisions', 'detachments', 'units', 'territorial', 'staff', 'area',
               'strength_arms', 'sources']),
}
EDGES = TABLES['brigades'][2]
COLS = TABLES['brigades'][3]


def page_edges(words, width, EDGES=EDGES):
    """Each edge: within 9 pt of the template's, the x that the fewest words lie across"""
    scale = width / 841.85
    cover = [0] * int(width + 2)
    for w in words:
        if w[2] - w[0] > 150:
            continue
        for x in range(int(w[0]), int(w[2]) + 1):
            if 0 <= x < len(cover):
                cover[x] += 1
    out = []
    for e in EDGES:
        e = e * scale
        best = min(range(int(e - 9), int(e + 10)), key=lambda x: (cover[x], abs(x - e)))
        out.append(best)
    return out


def lines_of(words):
    """Words into lines by their middle y (a line: words within 3 pt), left to right"""
    rows = []
    for w in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        mid = (w[1] + w[3]) / 2
        if rows and abs(rows[-1][0] - mid) < 3:
            rows[-1][1].append(w)
        else:
            rows.append([mid, [w]])
    return [(m, sorted(ws, key=lambda w: w[0])) for m, ws in rows]


def join(lines):
    text = ''
    for t in lines:
        t = t.strip()
        if not t:
            continue
        if text.endswith('-') and not text.endswith(' -') and t[:1].islower():
            text = text[:-1] + t
        elif text:
            text += ' ' + t
        else:
            text = t
    return re.sub(r'\s+', ' ', text).strip()


def read(first, last, EDGES=EDGES, COLS=COLS):
    doc = fitz.open(PDF)
    rows, section = [], ''
    for pg in range(first, last + 1):
        page = doc[pg - 1]
        words = [w for w in page.get_text('words') if w[4].strip()]
        if not words:
            continue
        edges = page_edges(words, page.rect.width, EDGES)
        # headings across both halves ("NARODNOOSLOBODILAČKE ... BRIGADE SLOVENIJE"), in capitals, no row number
        starts = []
        lines = lines_of(words)
        # the notes at the foot of a table's first page ("N A P O M E N A:"), not column 10's header "Napomena"
        stop = next((mid for mid, ws in lines if mid > page.rect.height * 0.5
                     and re.sub(r'[^A-Z]', '', ' '.join(w[4] for w in ws))[:8] == 'NAPOMENA'), 1e9)
        words = [w for w in words if (w[1] + w[3]) / 2 < stop - 2]
        scale = page.rect.width / 841.85
        for mid, ws in lines_of(words):
            t = ' '.join(w[4] for w in ws)
            if sum(1 for w in ws if re.fullmatch(r'\d{1,2}', w[4])) >= 7 and len(ws) <= 13:
                continue                                                  # the header row "1 2 3 ... 11"
            first = ws[0]
            if ((first[0] < edges[0] - 3 or (first[0] < edges[0] and first[4].rstrip('.').isdigit())) and len(first[4]) <= 4 and len(ws) > 1 and first[4] not in ('Red.', 'br.', 'broj')):
                n = first[4].rstrip('.')
                starts.append((mid - 4, int(n) if n.isdigit() else 0, pg))   # 0: a number the OCR garbled ("SY")
            elif re.fullmatch(r'[A-ZČĆŽŠĐ „"“\-—–().:]{12,}', t):
                starts.append((mid - 4, None, t))
        # a row whose number the OCR dropped: a name that starts after a blank gap (rows stand apart, an entry's own
        # lines about 8 pt), as at the top of a page
        prev_mid = -1e9
        for mid, ws in lines_of([w for w in words if w[0] < edges[1]]):
            first = ws[0]
            gap = mid - prev_mid
            prev_mid = mid
            t = ' '.join(w[4] for w in ws)
            if (gap > 16 and edges[0] - 3 <= first[0] <= edges[0] + 14 and first[4][:1].isupper()
                    and not re.search(r'Naziv|jedinice|Datum|formiranja|NARODNO|BRIGADE|DIVIZIJE|KORPUS|Red\.', t)
                    and not any(abs(y + 4 - mid) < 7 for y, _, _ in starts)):
                starts.append((mid - 4, 0, pg))
        starts.sort()
        # the right-hand page of the spread sits a few points off the left: its first line under each row start
        gutter = (edges[5] + edges[6]) / 2 if len(edges) > 6 else 410
        right = sorted((w[1] + w[3]) / 2 for w in words if w[0] > gutter)
        offs = []
        for y, no, _ in starts:
            if no is not None:
                near = [m for m in right if y - 8 <= m <= y + 14]
                if near:
                    offs.append(min(near) - (y + 4))
        offs.sort()
        shift = offs[len(offs) // 2] if offs else 0.0
        for i, (y, no, extra) in enumerate(starts):
            if no is None:
                section = re.sub(r'\s+', ' ', extra).strip()
                continue
            y_end = starts[i + 1][0] if i + 1 < len(starts) else 1e9
            cells = {c: [] for c in COLS}
            mine = [w for w in words if (y <= (w[1] + w[3]) / 2 < y_end and w[0] <= gutter)
                    or (y + shift - 5 <= (w[1] + w[3]) / 2 < y_end + shift - 5 and w[0] > gutter)]
            for mid, ws in lines_of(mine):
                by = {c: [] for c in COLS}
                for w in ws:
                    k = sum(1 for e in edges if (w[0] + w[2]) / 2 > e)
                    by[COLS[k]].append(w[4])
                for c in COLS:
                    if by[c]:
                        cells[c].append(' '.join(by[c]))
            row = {c: join(v) for c, v in cells.items()}
            row['no'] = no
            row['section'] = section
            row['pdf_page'] = pg
            row['shift'] = round(shift, 1)
            rows.append(row)
    # a row without a number between two consecutive ones: lines of the row above (a header, a continued cell)
    keep = []
    for i, r in enumerate(rows):
        nxt = rows[i + 1]['no'] if i + 1 < len(rows) else None
        if r['no'] == 0 and keep and nxt == keep[-1]['no'] + 1:
            for c in COLS[1:]:
                if r[c] and not re.fullmatch(r'[\d\s_]+', r[c]):
                    keep[-1][c] = (keep[-1][c] + ' ' + r[c]).strip()
            continue
        keep.append(r)
    rows = keep
    # a "row" whose name is in capitals is a heading between rows ("DIVIZIJE STRANIH DRŽAVLJANA")
    for r in rows:
        if r['no'] == 0 and re.fullmatch(r'[A-ZČĆŽŠĐ .:„"“()\-]{6,}', r['name']) and not r['formed'][:1].isdigit():
            r['_heading'] = True
    rows = [r for r in rows if not r.get('_heading')]
    # a run of rows without numbers that fills a gap of its own length takes those numbers (rows 8 and 9 of the
    # divisions); runs between consecutive numbers are notes set between rows
    out, i = [], 0
    while i < len(rows):
        if rows[i]['no'] == 0:
            j = i
            while j < len(rows) and rows[j]['no'] == 0:
                j += 1
            a = out[-1]['no'] if out else 0
            b = rows[j]['no'] if j < len(rows) else None
            run = rows[i:j]
            if b is not None and b - a - 1 == len(run):
                for k, r in enumerate(run):
                    r['no_printed'] = 0
                    r['no'] = a + 1 + k
                out += run
            elif b is None or b == a + 1:
                pass
            else:
                out += run
            i = j
            continue
        out.append(rows[i])
        i += 1
    rows = out
    # numbers the OCR misread ("225" for 255, "SY" for 89): a number that breaks the run between its neighbours
    for i, r in enumerate(rows):
        prev = rows[i - 1]['no'] if i else 0
        nxt = rows[i + 1]['no'] if i + 1 < len(rows) else None
        if r['no'] != prev + 1 and (nxt is None or nxt == prev + 2):
            r['no_printed'] = r['no']
            r['no'] = prev + 1
    return rows


ORD = {'prva': 1, 'prvi': 1, 'druga': 2, 'drugi': 2, 'treća': 3, 'treći': 3, 'četvrta': 4, 'četvrti': 4, 'peta': 5,
       'peti': 5, 'šesta': 6, 'šesti': 6, 'sedma': 7, 'sedmi': 7, 'osma': 8, 'osmi': 8, 'deveta': 9, 'deveti': 9,
       'deseta': 10, 'deseti': 10, 'jedanaesta': 11, 'jedanaesti': 11, 'dvanaesta': 12, 'dvanaesti': 12,
       'trinaesta': 13, 'trinaesti': 13, 'četrnaesta': 14, 'četrnaesti': 14, 'petnaesta': 15, 'petnaesti': 15,
       'šesnaesta': 16, 'šesnaesti': 16, 'sedamnaesta': 17, 'sedamnaesti': 17, 'osamnaesta': 18, 'osamnaesti': 18,
       'devetnaesta': 19, 'devetnaesti': 19, 'dvadeseta': 20, 'dvadeseti': 20, 'trideseta': 30, 'četrdeseta': 40,
       'pedeseta': 50}
TENS = {'dvadeset': 20, 'trideset': 30, 'četrdeset': 40, 'pedeset': 50}
UNITS_ORD = {'prva': 1, 'prvi': 1, 'druga': 2, 'drugi': 2, 'treća': 3, 'treći': 3, 'četvrta': 4, 'četvrti': 4,
             'peta': 5, 'peti': 5, 'šesta': 6, 'šesti': 6, 'sedma': 7, 'sedmi': 7, 'osma': 8, 'osmi': 8,
             'deveta': 9, 'deveti': 9}
FOLD = str.maketrans('čćžšđ', 'cczsd')
MONTH = r'(?:januar\w*|februar\w*|mart\w*|april\w*|maj\w*|jun\w*|jul\w*|avgust\w*|septemb\w*|oktob\w*|novemb\w*|decemb\w*|jan\.|feb\.|sept?\.|okt\.|nov\.|dec\.|avg\.)'
DATE = (rf'(?:(?:početk\w*|početak|poč\.|sredin\w*|sred\.|kraj\w*|kr\.|[pd]\.\s?p\.|polovin\w*|prv\w+\s+polovin\w*|drug\w+\s+polovin\w*|jesen\w*|'
        rf'proleć\w*|prolje\w*|leto|ljeto|leta|ljeta|zim\w*)\s+)?(?:\d{{1,2}}\.?\s*)?(?:[IVX]{{1,4}}\.?\s*|{MONTH}\s*)?(?:19\d\d|194\.\d)\.?'
        rf'|kraja\s+rata|rasformiranja|formiranja'
        rf'|\d{{1,2}}\.\s*(?:[IVX]{{1,4}}\.?|{MONTH})(?=\s+(?:do|i)\b)')     # "od 13. II do maja 1943": the year after


def number(name: str) -> int | None:
    """"Dvadeset druga (srpska) divizija" -> 22, "13. proleterska" -> 13, "Dvadesetprva" -> 21"""
    n = name.strip().lower()
    m = re.match(r'(\d{1,3})\.', n)
    if m:
        return int(m.group(1))
    m = re.match(r'(dvadeset|trideset|četrdeset|pedeset)\s*(\w+)', n)
    if m and m.group(2) in UNITS_ORD:
        return TENS[m.group(1)] + UNITS_ORD[m.group(2)]
    w = re.match(r'([a-zčćžšđ]+)', n)
    return ORD.get(w.group(1)) if w else None


def periods(text: str, chain: bool = True, bare: bool = False) -> list[dict]:
    """"pod Vrhovnim štabom NOP i DVJ do 1. XI 1942. u 1. proleterskoj diviziji do septembra 1943. u 2. ..." ->
    [{unit, from, to}, ...]. A unit is the words before its "od"/"do". In a chain (who a unit was under, one at a
    time) a period without its own end runs to the next one's start, and one without its start begins where the one
    before ended; a list of what a unit held at once (a division's brigades, a corps' divisions) is no chain. With
    bare, a date with no "od" before it starts its unit's period too (the detachments: "14. divizija oktobar 1943.
    7. korpus od 24. decembra 1943.")."""
    text = re.sub(r'\s+', ' ', text or '').strip(' .;')
    if not text or text in ('—', '-'):
        return []
    marks = list(re.finditer(rf'\b(od|do|potom|i ponovo od|ponovo od)\s+({DATE})', text))
    if bare:
        marks = [m for m in re.finditer(rf'(?:\b(od|do|potom|i ponovo od|ponovo od)\s+|(?<![\w.]))({DATE})', text)
                 if m.group(1) or re.search(r'19\d\d|194\.\d', m.group(2))]
    out, pos = [], 0
    for m in marks:
        unit = text[pos:m.start()].strip(' ,.;')
        unit = re.sub(r'^(?:[—–-]\s*)?(?:i\s+)?(?:potom\s+)?(?:u\s+|pod\s+)?', '', unit).strip()
        kind, date = m.group(1) or 'od', m.group(2).strip(' .')
        if unit and re.search(r'[A-Za-zČĆŽŠĐčćžšđ]{2,}', unit):
            out.append({'unit': unit, 'from': '', 'to': ''})
        if out:
            if kind == 'do':
                out[-1]['to'] = date
            elif kind.endswith('od'):
                if out[-1]['from'] and kind != 'od':
                    out[-1]['again'] = date
                elif not out[-1]['from']:
                    out[-1]['from'] = date
        pos = m.end()
    tail = text[pos:].strip(' ,.;')
    tail = re.sub(r'^(?:[—–-]\s*)?(?:i\s+)?(?:potom\s+)?(?:u\s+|pod\s+)?', '', tail).strip()
    if tail and re.search(r'[A-Za-zČĆŽŠĐčćžšđ]{3,}', tail) and not re.match(r'(?:od|do)\s+\w+$', tail):   # "od juna"
        out.append({'unit': tail, 'from': '', 'to': ''})
    for a, b in zip(out, out[1:]) if chain else ():
        if not a['to'] and b['from']:
            a['to'] = b['from']
        if not b['from'] and a['to'] and a['to'] != 'kraja rata':
            b['from'] = a['to']                                  # "u 1. ... do X u 2. ...": the second from X
    for p in out:
        dv = re.search(r'(\d{1,2})\.?\s*(?:\([^)]*\)\s*)?(?:[a-zčćžšđ.]+\s+){0,2}(?:divizij|dizivij)', p['unit'], re.I)
        kp = re.search(r'(\d{1,2})\.\s*(?:\([^)]*\)\s*)?(?:[a-zčćžšđ]+\s+)?korpus', p['unit'], re.I)
        if dv:
            p['division'] = int(dv.group(1))
        elif kp:
            p['corps'] = p['unit']
    return out


def clean(t: str) -> str:
    t = re.sub(r'(?<=[a-zčćžšđ])- -?(?=[a-zčćžšđ])', '-', t or '')            # "makedonsko- -šiptarska"
    t = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', t)                      # "proleter- ska"
    return re.sub(r'\s+', ' ', t).strip()


def key(name: str) -> tuple:
    """(number, region word, named after) for matching: "Treća slovenačka brigada „Ivan Cankar"" ->
    (3, 'slovenack', 'cankar')"""
    n = clean(name)
    head = re.split(r'\(', n)[0]
    num = number(head)
    words = [w.translate(FOLD).lower() for w in re.findall(r'[A-Za-zČĆŽŠĐčćžšđ]+', head)]
    skip = {'prva', 'druga', 'treca', 'cetvrta', 'peta', 'sesta', 'sedma', 'osma', 'deveta', 'deseta', 'no', 'nou',
            'udarna', 'brigada', 'divizija', 'narodnooslobodilacka', 'novj', 'proleterska', 'dvadeset', 'trideset',
            'cetrdeset', 'pedeset'}
    region = next((w[:7] for w in words if w not in skip and w not in ORD and len(w) > 3), '')
    if 'proleterska' in [w for w in words] and not region:
        region = 'prolete'
    named = re.search(r'[„"]\s*([^"“”]+)', n)
    person = named.group(1).split()[-1].translate(FOLD).lower()[:6] if named else ''
    return num, region, person



# the site's units whose row the book's name doesn't give away: a KNOJ brigade of the same name, a brigade named for
# its place or person, two brigades that bore one number (12. krajiška: the one formed at Drinić, 19-20 February 1943)
# the book's own errata ("Ispravke", PDF p. 892) for cells of these tables, each checked on the scan
ERRATA = {
    ('detachments', 56, 'parent'): ('uradni', 'udarni'),                        # book p. 599
    ('detachments', 66, 'parent'): ('operativnia', 'operativna'),               # p. 601
    ('detachments', 228, 'disbanded'): ('8. VIII 1941', '8. VIII 1944'),       # p. 627, Imotski odred
    ('brigades', 95, 'parent'): ('27. divizija', '26. divizija'),              # p. 715, 11. dalmatinska
    ('brigades', 313, 'name'): ('(. hercegovačka', '(3. hercegovačka'),        # p. 768
}

LINKS = {
    'ljubljanska-brigada': ('brigades', 148), '4-splitska-brigada': ('brigades', 72),
    'prva-vojvodjanska-brigada': ('brigades', 18), '2-vojvodjanska-brigada': ('brigades', 206),
    '3-krajiska-proleterska-brigada': ('brigades', 12), '25-srpska-divizija': ('divisions', 25),
    '4-srpska-brigada': ('brigades', 169), '17-majevicka-brigada': ('brigades', 34), '25-brodska-brigada': ('brigades', 92),
    '21-tuzlanska-brigada': ('brigades', 50), '53-srednjobosanska-divizija': ('divisions', 54),
    '21-slavonska-brigada': ('brigades', 76), '32-zagorska-divizija': ('divisions', 33),
    '4-proleterska-brigada': ('brigades', 5), '5-proleterska-brigada': ('brigades', 6), '8-banijska-brigada': ('brigades', 63),
    '3-makedonska-brigada': ('brigades', 114), '18-hrvatska-brigada': ('brigades', 35), '12-krajiska-brigada': ('brigades', 29),
    '3-vojvodjanska-brigada': ('brigades', 207), '8-kordunaska-divizija': ('divisions', 8),
    'cankarjeva-brigada': ('brigades', 141), 'gubceva-brigada': ('brigades', 140), 'gradnikova-brigada': ('brigades', 144),
    'zidanskova-brigada': ('brigades', 164), 'braciceva-brigada': ('brigades', 153), 'tomsiceva-brigada': ('brigades', 8),
    '1-slovenska-artilerijska-brigada': ('brigades', 237), '1-kosovsko-metohijska-brigada': ('brigades', 221),
    '19-sjevernodalmatinska-divizija': ('divisions', 19), '14-hercegovacka-brigada': ('brigades', 48),
    '22-divizija': ('divisions', 22), '34-divizija': ('divisions', 35), '6-crnogorska-brigada': ('brigades', 53),
    '51-divizija': ('divisions', 53), '3-udarna-divizija': ('divisions', 3), '7-banijska-divizija': ('divisions', 7),
    '16-slavonska-omladinska-brigada': ('brigades', 71), 'druga-licka-brigada': ('brigades', 11),
    '13-proleterska-brigada': ('brigades', 17), '7-banijska-brigada': ('brigades', 62),
    'posavsko-trebavski-odred': ('detachments', 70), 'skofjeloski-odred': ('detachments', 443),
    'istrski-odred': ('detachments', 423), 'zapadnodolenjski-odred': ('detachments', 445),
    'posavski-odred': ('detachments', 486),
}


def main():
    if not PDF.exists():
        sys.exit(f'{PDF} is missing: fetch https://znaci.org/00003/523.pdf')
    tables = {}
    for name, (first, last, edges, cols) in TABLES.items():
        rows = read(first, last, edges, cols)
        for r in rows:
            for (table, no, col), (wrong, right) in ERRATA.items():
                if table == name and r['no'] == no and wrong in r[col]:
                    r[col] = r[col].replace(wrong, right)
            r['name'] = clean(r['name'])
        tables[name] = rows
    for b in tables['brigades']:
        b['periods'] = periods(clean(b['parent']))
    for d in tables['divisions']:
        d['periods'] = periods(clean(d['parent']))
        d['brigades'] = periods(clean(d['composition']), chain=False)
    for c in tables['corps']:
        c['divisions_periods'] = periods(clean(c['divisions']), chain=False)
    for o in tables['detachments']:
        o['periods'] = periods(clean(o['parent']), bare=True)
        if 'C R N E' in o['section']:                            # the heading set in spaced capitals
            o['section'] = 'NOP ODREDI CRNE GORE I SANDŽAKA'
        if o['no'] > 540:      # Kosovo's heading is on a spread the scan lacks; Vojvodina's rows end at 540 (Ž)
            o['section'] = 'NOP ODREDI KOSOVA I METOHIJE'
    OUT.mkdir(exist_ok=True)
    for name, rows in tables.items():
        (OUT / f'{name}.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')

    site = re.findall(r"id: '([^']+)',\s*name: '([^']+)'", UNITS_TS.read_text(encoding='utf-8'))
    links = {}
    for uid, uname in site:
        kind = ('divisions' if 'divizij' in uname else 'brigades' if 'brigad' in uname
                else 'detachments' if 'odred' in uname else None)
        if not kind:
            continue
        if uid in LINKS:
            kind, no = LINKS[uid]
        else:
            k = key(uname)
            cands = [r['no'] for r in tables[kind] if (lambda rk: (rk[0] == k[0] and rk[1] and rk[1] == k[1])
                                                        or (k[2] and k[2] == rk[2]))(key(r['name']))]
            if len(cands) != 1:
                print(f'  {uid}: {len(cands)} rows, left out')
                continue
            no = cands[0]
        row = next(r for r in tables[kind] if r['no'] == no)
        links[uid] = {'table': kind, 'no': no, 'name': row['name']}
    (OUT / 'site_links.json').write_text(json.dumps(links, ensure_ascii=False, indent=1), encoding='utf-8')
    print(', '.join(f'{k} {len(v)}' for k, v in tables.items()), f"; {len(links)} of the site's units linked")


if __name__ == '__main__':
    main()
