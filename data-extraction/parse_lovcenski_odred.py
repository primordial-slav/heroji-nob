"""
Đuro Vujović, *Lovćenski partizanski odred* (Istorijski institut SR Crne Gore, Titograd 1976; znaci.org 00003/2425,
a 380 MB scan with no text layer): "Poginuli, strijeljani i umrli borci NOR-a 1941-1945. sa teritorije Lovćenskog NOP
odreda" (book pp. 611-713), a book across units. Its entries are added to the records of the soldiers they describe
(scripts/match_references.py), the rest go to Ostali borci.

The site's PDF website/public/pdfs/lovcenski-odred-pali-borci.pdf is the scan's PDF pages 304-355, each spread split
into its two book pages (fetched page by page with HTTP range requests, not the whole file). The text is Tesseract's
(data-extraction/ocr_scan.py, `--lang srp --columns 2`, read from the full grayscale pages; the site's PDF holds them
made 1-bit), saved in data-extraction/ocr/lovcenski-odred-pali-borci.json; this parser reads only that file.

Cyrillic, two columns, each entry hanging, numbered through the list and within its place ("642 (36)."), under the
heading of its srez ("ЦЕТИЊСКИ СРЕЗ") and of its village or town ("Ц е т и њ е"): "1. АНДРИЋ Андра МАРКО — МАРКИША,
рођен 1914. у Цетињу, кројач, погинуо 1. децембра 1941. на Пљевљима." The book titles the list as the region's
fallen fighters, and its author's note says it counts every one he could find; every entry goes in (a man of the other
side would be named so, and none is). The author's note under the title (book pp. 611-612) is not read. IDs
9084xxxxxx, by the book's number. Each entry names the site's brigades its text names (`units`) and has the box of its
lines on its first page.

Output: data-extraction/znaci/lovcenski-odred-pali-borci-entries.json
Usage: python data-extraction/parse_lovcenski_odred.py [--sample N] [--heads]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import ocr_scan  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
from _ocr_readback import CYR, LOOKALIKE, Corpus, _distance, fold, latin, title  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402

PDF = 'lovcenski-odred-pali-borci.pdf'
OUT = HERE / 'znaci' / 'lovcenski-odred-pali-borci-entries.json'
PREFIX = '9084'
TITLE = 'Poginuli, strijeljani i umrli borci NOR-a 1941-1945. sa teritorije Lovćenskog NOP odreda'
# an entry starts with its number, maybe its number within the place: "642 (36). БУРОВИЋ", "1. АНДРИЋ"
START = re.compile(r'^\W{0,2}([\d#%?][\d#%?:]{0,4})\s*[.,:;]?\s*(?:\(\s*([\dIlOoЗзбi]{1,3})\s*\)?\s*[.,:;)]*[A-ZА-Я]?)?$')   # ":29.", "152 (39.", "7# (13)", "1:44"
UNITS = [(r'\b(?:Prv\w+|1\.)\s+proletersk\w*\s+brigad', 1), (r'\b(?:Drug\w+|2\.)\s+proletersk\w*\s+brigad', 39),
         (r'\b(?:Treć\w+|3\.)\s+(?:proletersk\w*\s+)?sandžačk', 5),
         (r'\b(?:Četvrt\w+|4\.)\s+(?:crnogorsk\w*\s+)?proletersk', 40), (r'\b(?:Pet\w+|5\.)\s+(?:crnogorsk\w*\s+)?proletersk', 41),
         (r'\b(?:Šest\w+|6\.)\s+crnogorsk', 106), (r'\b(?:Sedm\w+|7\.)\s+crnogorsk', 28), (r'\b(?:Osm\w+|8\.)\s+crnogorsk', 38),
         (r'\b(?:Prv\w+|1\.)\s+bokeljsk', 102), (r'\b(?:Deset\w+|10\.)\s+hercegovačk', 43),
         (r'\b(?:Četvrt\w+|4\.)\s+sandžačk', 98), (r'\b(?:Drug\w+|2\.)\s+dalmatinsk', 7),
         (r'\b(?:Treć\w+|3\.)\s+krajišk', 10), (r'\bVrhovn\w+\s+štab', 112), (r'\bCentraln\w+\s+bolnic', 117)]
DEATH = re.compile(r'\b(poginu[oa]|umr(?:o|la)|ubijen[a]?|strijeljan[a]?|streljan[a]?|nesta[oa]|podlegao|podlegla|'
                   r'obješen[a]?|spaljen[a]?|izgubio\s+život|stradao|stradala)\b(.{0,90}?)\b(19[4-5]\d)\b', re.I)
CORPUS: Corpus | None = None


SREZ = {'cetin': 'Cetinjski srez', 'bars': 'Barski srez', 'kotor': 'Kotorski srez', 'budv': 'Budvanski srez',
        'titograd': 'Titogradski srez', 'podgor': 'Podgorički srez', 'danilovgrad': 'Danilovgradski srez',
        'ulcinj': 'Ulcinjski srez', 'nikš': 'Nikšićki srez'}
# the villages' and towns' headings, read from the page images: (page, the heading's top, rounded) -> the name; the
# OCR garbles their spaced italics ("Ko" | "о a x")
HEADS: dict[tuple[int, int], str] = {}
HEADS_FILE = HERE / 'ocr' / 'lovcenski-odred-pali-borci.heads.json'
# lines the OCR garbled, read from the page images: {page, y, x (the line's top and left, rounded), text, and a new top
# or left where the OCR set the line elsewhere}; an empty text drops the line (a speck, a line read twice)
LINES_FILE = HERE / 'ocr' / 'lovcenski-odred-pali-borci.lines.json'


def is_srez(text: str) -> str | None:
    t = ''.join(LOOKALIKE.get(ch, ch) for ch in re.sub(r'\s+', '', text)).replace('3', 'З')
    m = re.search(r'([А-ЯЂЈЉЊЋЏA-Z]{4,})(СРЕЗ|SREZ|SRЕZ|СРEЗ|CPE3|ОПШТИНА)\W*$', t)
    if not m:
        return None
    lat = fold(latin(m.group(1)))
    return next((v for k, v in SREZ.items() if lat.startswith(fold(k))), title(latin(m.group(1))) + ' srez')


def page_lines(page: dict) -> list[tuple[int, dict]]:
    """The page's lines with their column; a page read by Tesseract's own layout (no cut: p. 16, skewed) takes the
    column from where the line starts"""
    if page['cuts']:
        return [(ln['col'], ln) for ln in page['lines']]
    mid = page['width'] * 0.45
    return [(0 if ln['x0'] < mid else 1, ln) for ln in page['lines']]


def margins(page: dict) -> dict[int, float]:
    """Each column's left margin: where its entries' first lines start (the hanging lines stand about 12 pt in)"""
    out = {}
    for col in (0, 1):
        lines = [ln for c, ln in page_lines(page) if c == col and len(ln['words']) > 2]
        # where its numbered lines start (a number and a name): the specks in a margin are no measure
        starts = sorted(ln['x0'] for ln in lines if re.match(r'\W{0,2}\d{1,4}\b', ln['words'][0][4]) and
                        any(re.match(r'\W?[А-ЯЂЈЉЊЋЏA-Z3]{3}', w[4]) for w in ln['words'][1:3]))
        if len(starts) >= 3:
            out[col] = starts[len(starts) // 2] - 2
            continue
        xs = sorted(ln['x0'] for ln in lines)
        if xs:
            low = [x for x in xs if x <= xs[len(xs) // 20] + 4]
            out[col] = sorted(low)[len(low) // 2]
    return out


def headings(pno: int, page: dict, lines: list[tuple[int, dict]]) -> list[dict]:
    """The headings over the page, a srez's in capitals ("ЦЕТИЊСКИ СРЕЗ") and a place's in spaced letters ("Ц е т и
    њ е", "Ријечка општина"), each starting a new block of two columns. Centred, they cross the cut between the
    columns, so the OCR reads them as two short lines at one height ("Ц е т" | "и ње", "Ба" | "р"), each standing
    alone in its column (a gap above and below it): the left one ends at the cut and starts well in from the margin
    (an entry's last line starts at the hanging indent), the right one starts at the cut."""
    margin = margins(page)
    cut = page['cuts'][0] if page['cuts'] else page['width'] / 2
    def text_of(ln):
        return ' '.join(w[4] for w in ln['words'])
    def short(ln):
        t = text_of(ln)
        return len(ln['words']) <= 3 and not re.search(r'[\d,]', t)
    cands = []
    for c, ln in lines:
        text = text_of(ln)
        if is_srez(text):
            cands.append((c, ln, text))
            continue
        if re.search(r'[\d,]', text) or len(ln['words']) > 12 or len(re.sub(r'\W', '', text)) > 24:
            continue
        toks = [re.sub(r'\W', '', w[4]) for w in ln['words']]
        spaced = sum(1 for t in toks if len(t) <= 2) >= 0.6 * len(toks)
        at_cut = (c == 1 and ln['x0'] <= cut + 8) or \
            (c == 0 and ln['x1'] >= cut - 12 and ln['x0'] > margin.get(0, 0) + 40)
        across = ln['x0'] < cut < ln['x1']
        if not (across or (at_cut and (spaced or len(toks) <= 3 and len(''.join(toks)) <= 14))):
            continue
        same = sorted(l2['top'] for c2, l2 in lines if c2 == c and l2 is not ln)
        above = max([t for t in same if t < ln['top']], default=-99)
        below = min([t for t in same if t > ln['top']], default=9999)
        if ln['top'] - above >= 8 and below - ln['top'] >= 8:
            cands.append((c, ln, text))
    out, used = [], set()
    for c, ln, text in cands:
        if id(ln) in used:
            continue
        mates = [(c2, l2, t2) for c2, l2, t2 in cands if c2 != c and abs(l2['top'] - ln['top']) < 6 and id(l2) not in used]
        mates += [(c2, l2, text_of(l2)) for c2, l2 in lines if c2 != c and abs(l2['top'] - ln['top']) < 6 and
                  id(l2) not in used and short(l2) and l2 not in [m[1] for m in mates]]
        group = sorted([(c, ln, text)] + mates[:1], key=lambda x: x[1]['x0'])
        if len(group) == 1 and not (ln['x0'] < cut < ln['x1']) and not is_srez(text):
            continue                                   # half a line at the cut with nothing beside it
        used |= {id(g[1]) for g in group}
        top = min(g[1]['top'] for g in group)
        out.append({'top': top, 'wide': True, 'col': c, 'ocr': ' '.join(g[2] for g in group),
                    'ids': {id(g[1]) for g in group},
                    'box': (min(g[1]['x0'] for g in group), top, max(g[1]['x1'] for g in group),
                            max(g[1]['bottom'] for g in group))})
    return sorted(out, key=lambda h: h['top'])


def head_name(pno: int, h: dict) -> str:
    s = is_srez(h['ocr'])
    if s:
        return s
    name = HEADS.get((pno, round(h['top'])))
    if name:
        return name
    joined = re.sub(r'(?<=\S) (?=\S)', '', h['ocr']).strip(' .,|')
    return latin(joined) if re.fullmatch(r'[А-ЯЂЈЉЊЋЏа-яђјљњћџ ]{3,}', joined) else '?'


def bands(pno: int, page: dict) -> list[list[tuple[str, object]]]:
    """The page in reading order: bands between the headings over the page, each band its left column, then its
    right; a heading over one column stands among its lines. Items: ('head', heading), ('line', ln)."""
    lines = page_lines(page)
    if pno == 1:                                   # the title above, the author's note below the first entries
        note = min((ln['top'] for c, ln in lines if re.match(r'^\W{0,2}\*?\s*Овај\s+списак', ' '.join(w[4] for w in ln['words']))), default=1e9)
        lines = [(c, ln) for c, ln in lines if ln['top'] < note - 2]
    if pno == 2:                                   # the note runs on under p. 612's entries
        note = min((ln['top'] for c, ln in lines if re.match(r'^\W{0,2}Грешке\s+могу', ' '.join(w[4] for w in ln['words']))), default=1e9)
        lines = [(c, ln) for c, ln in lines if ln['top'] < note - 2]
    heads = headings(pno, page, lines)
    # the running head and the page's foot, and lines of specks (the scan's edge: "|", "E:", "+") are no text
    def junk(ln):
        text = ' '.join(w[4] for w in ln['words'])
        return ln['top'] < 25 or ln['top'] > 490 or (len(re.sub(r'[^\w]|\d|_', '', text)) <= 2 and not re.search(r'\d', text))
    keep = {i for h in heads if h['wide'] or len(re.sub(r'\W', '', h['ocr'])) >= 3 for i in h['ids']}
    heads = [h for h in heads if h['ids'] & keep]
    lines = [(c, ln) for c, ln in lines if id(ln) in keep or not junk(ln)]
    folio = str(610 + pno)                             # the book's page number, at a line's end
    for c, ln in lines:
        if len(ln['words']) > 1 and ln['words'][-1][4].strip('.,') == folio:
            ln['words'] = ln['words'][:-1]
    wide = [h for h in heads if h['wide']]
    head_ids = {i for h in heads for i in h['ids']}
    col_heads = {next(iter(h['ids'])): h for h in heads if not h['wide']}
    out, edges = [], [-1.0] + [h['top'] - 0.5 for h in wide] + [1e9]
    for k in range(len(edges) - 1):
        lo, hi = edges[k], edges[k + 1]
        band = [('head', wide[k - 1])] if k else []
        for col in (0, 1):
            for c, ln in sorted(lines, key=lambda x: x[1]['top']):
                if c == col and lo <= ln['top'] < hi:
                    if id(ln) in col_heads:
                        band.append(('head', col_heads[id(ln)]))
                    elif id(ln) not in head_ids:
                        band.append(('line', ln))
        out.append(band)
    return out


PARTICLES = {'Де', 'Ди', 'Да', 'Ла', 'Ле', 'Фон', 'Ван', 'De', 'Di', 'Da', 'La', 'Le'}


def start_of(words: list[list]) -> tuple[re.Match | None, list[list]]:
    """The entry's number at a line's start, and the line's words after it ("642 (36). БУРОВИЋ"; "115 Mu БАТРИЋЕВИЋ"
    and "522 (89. _з ЛОПИЧИЋ" with the OCR's specks; ":29. ИВАНОВИЋ"; "7# (13)" with a garbled digit; "ši > 38 (52).
    СУЂИЋ" with specks from the gutter before it)"""
    def speck(w):
        return not re.search(r'\d', w[4]) and len(re.sub(r'\W', '', w[4])) <= 2 and w[4] not in PARTICLES and \
            not re.fullmatch(r'[-—–]{2,}|—', w[4])
    lead = 0
    while lead < 2 and len(words) > lead + 2 and speck(words[lead]):
        lead += 1
    if lead and START.match(words[lead][4]):
        words = words[lead:]
    if not words:
        return None, words
    m = START.match(words[0][4])
    rest = words[1:]
    if rest and (not m or rest[0][4].startswith('(')):
        m2 = START.match(words[0][4] + ' ' + rest[0][4])             # "642 (36)." read as two words
        if m2:
            m, rest = m2, rest[1:]
    if m and not m.group(2) and len(rest) > 1 and re.fullmatch(r'\(?[\dIlOoЗзбi]{1,4}[).,:;]*', rest[0][4]):
        rest = rest[1:]                       # the place's number without its brackets: "242 1928. МАРОШ", "567 039,"
    if not m:
        return None, words
    # specks between the number and the surname ("115 Mu БАТРИЋЕВИЋ", "951 GI). РАДУЛОВИЋ"); a dash for the surname
    # above ("--- Вука МИЛО") and a particle ("Де БЕНЕДЕТИ") are kept
    while len(rest) > 1 and (speck(rest[0]) or re.fullmatch(r'\W?\d\W?', rest[0][4])) and \
            (caps(rest[1][4]) or speck(rest[1])):
        rest = rest[1:]
    return m, [words[0]] + rest


def caps(word: str) -> bool:
    """A surname in capitals (after a speck: ".МИЛОШЕВИЋ"; a 3 the OCR read for З: "3VBEP"), not a place in the
    locative that follows a year at a hanging line's start ("1922. v Раломиру")"""
    letters = re.sub(r'[^А-Яа-яЂЈЉЊЋЏђјљњћџA-Za-z3]', '', word)
    return len(letters) >= 3 and sum(ch.isupper() or ch == '3' for ch in letters) >= 0.6 * len(letters)


def read() -> list[dict]:
    """The entries in the book's order. An entry starts at a column's margin with its number and a name (a year at a
    hanging line's start is followed by a small word: "1943. у Бару"); the lines under it in its column, down to the
    next start or heading, are its. The order the page is read in doesn't matter: the entries are put in the order
    of their numbers, and each place's heading is the one over its first entry, "(1)"."""
    ocr = ocr_scan.load(PDF)
    fixes = []
    for fix in json.loads(LINES_FILE.read_text(encoding='utf-8')):
        page = ocr['pages'][str(fix['page'])]
        hit = [ln for ln in page['lines'] if round(ln['top']) == fix['y'] and round(ln['x0']) == fix['x']]
        assert len(hit) == 1, fix
        fixes.append((fix, page, hit[0]))
    for fix, page, ln in fixes:
        if not fix['text']:
            page['lines'].remove(ln)
            continue
        ln['top'], ln['x0'] = fix.get('top', ln['top']), fix.get('x0', ln['x0'])
        ln['bottom'] = max(ln['bottom'], ln['top'] + 6)
        width, x, words = (ln['x1'] - ln['x0']) / max(1, len(fix['text'])), ln['x0'], []
        for t in fix['text'].split():
            words.append([x, ln['top'], x + len(t) * width, ln['bottom'], t, 99])
            x += (len(t) + 1) * width
        ln['words'] = words
    if HEADS_FILE.exists():
        HEADS.update({(r['page'], r['y']): r['name'] for r in json.loads(HEADS_FILE.read_text(encoding='utf-8'))})
    entries: list[dict] = []
    heads: list[dict] = []
    started, srez, place = False, '', ''
    for pno in range(1, len(ocr['pages']) + 1):
        page = ocr['pages'][str(pno)]
        margin = margins(page)
        col_of = {id(ln): c for c, ln in page_lines(page)}
        for bi, band in enumerate(bands(pno, page)):
            current = {0: None, 1: None}                    # the entry each column is in
            for kind, item in band:
                if kind == 'head':
                    item['name'] = head_name(pno, item)
                    item['page'] = pno
                    heads.append(item)
                    HEAD_LOG.append((pno, item))
                    started = started or item['name'].endswith('srez')
                    # the entries come in the book's order: each is under the srez and place headings read last
                    if item['name'].endswith('srez'):
                        srez, place = item['name'], ''
                    elif item['name'] != '?':
                        place = item['name']
                    for c in (0, 1):
                        if item['wide'] or c == item['col']:
                            current[c] = None
                    continue
                if not started:
                    continue
                ln = item
                col = col_of[id(ln)]
                m, words = start_of(ln['words'])
                # (the surname: a capital, or a 3 the OCR read for З ("3VBEP" = ЗУБЕР), after a speck (".МИЛОШЕВИЋ"))
                dash = len(words) > 2 and re.fullmatch(r'[-—–]{2,}|—', words[1][4])     # the surname above's
                if (pno, round(ln['top'])) in STARTS:
                    m, words = None, [ln['words'][0]] + [w for w in ln['words'] if caps(w[4]) or not re.search(r'\d', w[4])][1:]
                tolerance = 7 if page['cuts'] else 15                  # (p. 16, skewed: its margin wanders)
                named = len(words) > 1 and (dash or caps(words[1][4]) or (
                    # a surname the OCR set small after a number within the place ("217 (Il). Вукчевић"), a particle
                    m and m.group(2) and re.fullmatch(r'\W?[А-ЯЂЈЉЊЋЏA-Z][а-яђјљњћџa-z]{2,}\W*', words[1][4])) or (
                    words[1][4] in PARTICLES and len(words) > 2 and caps(words[2][4])))
                forced = STARTS.get((pno, round(ln['top'])))
                if forced:
                    m, named = re.match(r'(\d+)\s*(?:\((\d+)\))?', forced), True
                if (m and named
                        and (ln['x0'] < margin.get(col, 0) + tolerance or
                             (m.group(2) and caps(words[1][4]) and ln['x0'] < margin.get(col, 0) + 30)) and (m.group(1).replace(':', '').isdigit() or m.group(2))):
                    e = {'no': int(m.group(1).replace(':', '')) if m.group(1).replace(':', '').isdigit() else -1, 'local': m.group(2) or '', 'page': pno, 'band': bi, 'srez': srez, 'place': place,
                         'col': col, 'top': ln['top'], 'lines': [(pno, ln)], 'dash': bool(dash),
                         'words': list(words[2:] if dash else words[1:])}
                    entries.append(e)
                    current[col] = e
                elif current[col] is not None:
                    current[col]['lines'].append((pno, ln))
                    current[col]['words'] += ln['words']
                elif entries:
                    # a column's first lines continue the entry the column before ended with (the left column, or the
                    # previous page's right one)
                    entries[-1]['lines'].append((pno, ln))
                    entries[-1]['words'] += ln['words']
    number(entries)
    return entries


def local_no(text: str) -> int:
    t = text.translate(str.maketrans('IliOoЗзб', '11100336'))
    return int(t) if t.isdigit() else -1


def number(entries: list[dict]) -> None:
    """Each entry's number. Down a column the numbers rise, by one but where the OCR missed a start (its man stays
    glued to the entry above). A printed number is kept where it rises so from the entry above or to the entry below
    in its column and stands among the page's numbers; a misread one ("7256 (158)" for 1226, "1:44", "12657", "8 (8)"
    for 2058) is taken from its number within the place where that fits (the entry above's number less its own,
    and this one's), else from the entry above or below. Numbers no rule settles are in NUMBERS."""
    for e in entries:
        e['printed'], e['loc'] = e['no'], local_no(e['local'])
    cols: dict[tuple, list] = {}                   # a column of a band: the numbers jump at a heading over the page
    for e in entries:
        cols.setdefault((e['page'], e['band'], e['col']), []).append(e)
    for es in cols.values():
        es.sort(key=lambda e: e['top'])
    pages: dict[int, list] = {}
    for e in entries:
        pages.setdefault(e['page'], []).append(e)
    def rises(a, b):
        if a is None or b is None or a['no'] <= 0 or b['no'] <= 0:
            return False
        if a['loc'] > 0 and b['loc'] > a['loc']:                 # the same place: both numbers rise alike
            return b['no'] - a['no'] == b['loc'] - a['loc'] <= 2
        return 1 <= b['no'] - a['no'] <= 2
    for es in cols.values():
        for k, e in enumerate(es):
            above, below = (es[k - 1] if k else None), (es[k + 1] if k + 1 < len(es) else None)
            e['ok'] = e['no'] > 0 and (rises(above, e) or rises(e, below))
    for pno, es in pages.items():
        good = sorted(e['no'] for e in es if e['ok'])
        med = good[len(good) // 2] if good else 0
        for e in es:
            e['ok'] = e['ok'] and abs(e['no'] - med) <= len(es) + 2
            fixed = NUMBERS.get((pno, round(e['top'])))
            if fixed:
                e['no'], e['ok'] = fixed, True
    ok_pages = {p: sorted(e['no'] for e in es if e['ok']) for p, es in pages.items()}
    def page_bounds(p):
        before = [n for q in range(p - 1, 0, -1) for n in ok_pages.get(q, [])[-1:]][:1]
        after = [n for q in range(p + 1, p + 4) for n in ok_pages.get(q, [])[:1]][:1]
        return (before[0] + 1 if before else 1), (after[0] - 1 if after else 99999)
    for _ in range(4):
        for es in cols.values():
            for k, e in enumerate(es):
                if e['ok']:
                    continue
                above = next((es[i] for i in range(k - 1, -1, -1) if es[i]['ok']), None)
                below = next((es[i] for i in range(k + 1, len(es)) if es[i]['ok']), None)
                plo, phi = page_bounds(e['page'])
                lo = above['no'] + (k - es.index(above)) if above else plo
                hi = below['no'] - (es.index(below) - k) if below else phi
                # the number within the place, added to the base of an entry of the same place on the page (one
                # with a smaller number within the place, nearest above it in the book)
                before = [x for x in pages[e['page']] + pages.get(e['page'] - 1, [])
                          if x['ok'] and 0 < x['loc'] < e['loc'] and x['no'] < (lo if above else hi)]
                near = max(before, key=lambda x: x['no']) if before else None
                by_loc = [near['no'] - near['loc'] + e['loc']] if near else []
                by_loc = [n for n in by_loc if lo <= n <= hi]
                if lo > hi:
                    continue
                if above and (e['printed'] == lo or lo in by_loc[:1]):
                    no = lo
                elif by_loc:
                    no = by_loc[0]
                elif lo <= e['printed'] <= hi and (above or below):
                    no = e['printed']
                elif above:
                    no = lo
                elif below:
                    no = hi
                else:
                    continue
                e['no'], e['ok'] = no, True
    for es in cols.values():
        for k in range(1, len(es)):
            a, e = es[k - 1], es[k]
            if e['no'] <= a['no']:                          # "1368 (320), 1368 (321)"
                e['no'] = a['no'] + (e['loc'] - a['loc'] if a['loc'] > 0 and 1 <= e['loc'] - a['loc'] <= 2 else 1)
    taken = Counter(e['no'] for e in entries)
    for e in entries:
        if taken[e['no']] > 1 and e['printed'] != e['no'] and 0 < e['printed'] and not taken[e['printed']]:
            es = cols[(e['page'], e['band'], e['col'])]
            k = es.index(e)
            if (k == 0 or es[k - 1]['no'] < e['printed']) and (k + 1 == len(es) or e['printed'] < es[k + 1]['no']):
                taken[e['no']] -= 1
                e['no'] = e['printed']
                taken[e['no']] += 1
    for e in entries:
        fixed = NUMBERS.get((e['page'], round(e['top'])))
        if fixed:
            e['no'], e['ok'] = fixed, True


# entries whose number no rule settles, read from the page: (page, the line's top, rounded) -> the number
NUMBERS: dict[tuple[int, int], int] = {}
# lines that start an entry the OCR garbled past the rules ("РОЛОВИЋ Ника под МИЛЕВА, 1385 4"): (page, the line's
# top, rounded) -> "number (number within the place)"
STARTS: dict[tuple[int, int], str] = {}


HEAD_LOG: list = []


def text_of(words: list[list]) -> str:
    out = []
    for w in words:
        t = w[4]
        if re.fullmatch(r'[|~·•“"]+', t):
            continue
        core = re.sub(r'^\W+|\W+$', '', t)
        if w[5] < 80 and len(core) > 3 and core.isalpha() and core.islower():
            t = t.replace(core, CORPUS.word(core, alts=(w[6],) if len(w) > 6 else ()))
        out.append(latin(''.join(LOOKALIKE.get(ch, ch) for ch in t)) if not re.search('[A-Za-z]{2}', t) or
                   re.search('[А-Яа-я]', t) else latin(t))
    text = ' '.join(out)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    text = re.sub(r'\b1[08]([0-4]\d)\b', r'19\1', text)
    return re.sub(r'\s+([.,;:])', r'\1', re.sub(r'\s+', ' ', text)).strip()


DASHES = ('—', '-', '–', '--', '---')


def upper(t: str) -> bool:
    letters = re.sub(r'[^А-Яа-яЂЈЉЊЋЏђјљњћџA-Za-z3]', '', t)
    return len(letters) >= 2 and sum(ch.isupper() or ch == '3' for ch in letters) >= 0.6 * len(letters)


def lower_start(t: str) -> bool:
    core = re.sub(r'^\W+', '', t)
    return bool(core) and core[0].isalpha() and core[0].islower()


def head_of(raw_words: list[list]) -> tuple[str, str, str, str, str, int]:
    """SURNAME Father [(Nick)] GIVEN [— NICK], rođen ...: the surname and the given name in capitals, the father
    between them in small letters ("ЛУБАРДА Марка (Зека) БОЖО"; with none, the last word in capitals is the given
    name: "ЊЕГУШ МИЛОШ"); a woman's two surnames joined by a dash ("РАДУЛОВИЋ — МАРКОВИЋ Зарије БОСИЉКА"); a given
    name and what he was called joined by a hyphen ("ЈОВАН-ЈОЛЕ"). The name ends at its comma, or where the OCR lost
    it, at the first word in small letters after the given name ("рођен"). The OCR's slips: specks ("МРАКОВИЋ |
    Сима", "ЛОМПАР 4 Марка", "ДЕРВИШ it Николе"), a word broken at the line's end ("ПЕ- ТАР", "МИХАИ- ЛО"), the given
    name glued to the next word ("ШПИРОрођен"), the father's first letter set small ("пера ЈОВАН-ЈОКО"), the given
    name in small letters ("Пера Лука, рођен"), the father in capitals ("ПЕЈОВИЋ БУРА СТАНКО"). Returns the
    surname, the father, the given name, what he was called, the father's nickname, and how many words it took."""
    toks: list[list] = []                           # [the word, the number of raw words up to it]
    for k, w in enumerate(raw_words[:30]):
        t = w[4].strip('„"“”\'|_~')
        glued = re.match(r'^([А-ЯЂЈЉЊЋЏA-Z]{3,})([рpr][оo]\S*)$', t)
        if glued:                                    # "ШПИРОрођен"
            toks += [[glued.group(1) + ',', k + 1], [glued.group(2), k + 1]]
            continue
        if not t or (re.fullmatch(r'[\W\d_]{1,2}', t) and t not in DASHES):
            continue
        if toks and len(toks[-1][0]) > 1 and toks[-1][0].endswith('-') and toks[-1][0] not in DASHES and \
                t not in DASHES:
            toks[-1] = [toks[-1][0][:-1] + t, k + 1]
            continue
        toks.append([t, k + 1])

    def word(t):
        return t.strip(',.;:')

    def closes(t):
        return t.endswith(',') or t.endswith('.') and len(word(t)) > 2

    def small(t):                                    # a speck in small letters: "it", "o", "a.", "is"
        return len(word(t)) <= 2 and word(t).islower()

    def bio(t):                                      # the biography's first word
        return bool(re.match(r'(?:р[оo]|[рpr]o|по|po)\W*[ђbб]', t)) or t.startswith('рођ')
    i, used = 0, 0
    last, father, fnick, given, nick = [], '', '', [], []
    # the surname: the words in capitals; a second one after a dash when the father follows it
    while i < len(toks) and upper(toks[i][0]):
        last.append(word(toks[i][0]))
        used = toks[i][1]
        i += 1
        if closes(toks[i - 1][0]):
            break
        if i + 2 < len(toks) and toks[i][0] in DASHES and upper(toks[i + 1][0]) and not upper(toks[i + 2][0]) and \
                not lower_start(toks[i + 2][0]):
            i += 1
    # a comma or full stop after the surname is a speck where the father and the given name follow ("ВУЈАНОВИЋ.
    # Јована ДУШАН,", "БУРИЋ, „лабуда, СВЕТОЗАР")
    done = bool(last) and i > 0 and closes(toks[i - 1][0]) and not (
        i + 1 < len(toks) and not upper(toks[i][0]) and not bio(toks[i][0]) and upper(toks[i + 1][0]))
    while not done and i + 1 < len(toks) and (small(toks[i][0]) or toks[i][0] in DASHES) and \
            not upper(toks[i + 1][0]):
        i += 1                                       # "ДЕРВИШ it Николе МАТО", "ПОПОВИЋ — Петра БАЦО"
    if not done and len(last) >= 3 and CORPUS.fathers[fold(latin(last[-2]))] >= 20 and \
            not CORPUS.surnames[fold(latin(last[-2]))]:
        given, father = [last.pop()], last.pop()      # the father in capitals: "ПЕЈОВИЋ БУРА СТАНКО"
        done = True
    if not done and i < len(toks) and toks[i][0] not in DASHES and re.search(r'[А-Яа-яA-Za-z]', toks[i][0]) and \
            not upper(toks[i][0]) and not bio(toks[i][0]) and \
            (not lower_start(toks[i][0]) or (i + 1 < len(toks) and upper(toks[i + 1][0]))):
        father = word(toks[i][0])
        used = toks[i][1]
        i += 1
        if i < len(toks) and toks[i][0].startswith('('):              # the father's nickname: "Марка (Зека)"
            fnick = word(toks[i][0]).strip('()')
            used = toks[i][1]
            i += 1
        while i < len(toks) and small(toks[i][0]) and i + 1 < len(toks) and upper(toks[i + 1][0]):
            i += 1
        while i < len(toks) and upper(toks[i][0]):
            given.append(word(toks[i][0]))
            used = toks[i][1]
            i += 1
            if closes(toks[i - 1][0]):
                break
        if not given and i < len(toks) and not lower_start(toks[i][0]) and not bio(toks[i][0]) and \
                (closes(toks[i][0]) or i + 1 < len(toks) and bio(toks[i + 1][0])):
            given = [word(toks[i][0])]               # the given name in small letters: "Пера Лука, рођен"
            used = toks[i][1]
            i += 1
    elif len(last) > 1:
        given = [last.pop()]                        # no father: "ЊЕГУШ МИЛОШ"
    # what he was called, after a dash: "МАРКО — МАРКИША", "ЈОВАН - ЈОКО"
    if i + 1 < len(toks) and toks[i][0] in DASHES and upper(toks[i + 1][0]) and not closes(toks[i - 1][0]):
        nick.append(word(toks[i + 1][0]))
        used = toks[i + 1][1]
        i += 2
    c = CORPUS
    surname = '-'.join(c.surname(t) for t in last if t not in DASHES)
    fathers = c.genitive(father) if father else ''
    first = ''
    if given:
        parts = given[0].split('-')
        first = c.given(parts[0])
        if len(parts) > 1 and all(parts):                   # "ЈОВАН-ЈОЛЕ": Jovan, called Jole
            nick.insert(0, '-'.join(parts[1:]))
        nick[0:0] = given[1:]
    nicks = ' '.join(c.given(n) if c.givens[fold(latin(n))] else title(latin(n)) for n in nick if n)
    return surname, fathers, first, nicks, title(latin(fnick)) if fnick else '', used


WORDS: dict = {}
KEYWORDS = ['poginuo', 'poginula', 'strijeljan', 'strijeljana', 'podlegao', 'podlegla', 'zarobljen', 'zemljoradnik',
            'domaćica', 'radnik', 'učenik', 'učenica', 'januara', 'februara', 'aprila', 'avgusta', 'septembra',
            'oktobra', 'novembra', 'decembra', 'bataljonu', 'brigadi', 'brigade', 'crnogorske', 'crnogorskoj',
            'proleterske', 'proleterskoj', 'udarnoj', 'omladinske', 'omladinskoj']


def fix_text(text: str) -> str:
    """The biography's words the OCR garbled, read back from the words of the units' entries: one the site doesn't
    know takes the known one a letter away (two in a long word) and no other as close ("crpogorske", "novembpa");
    the first word is "rođen(a)" ("roben", "pođen", "robsp"); a lone "v" or "y" is "u"."""
    if not WORDS:
        counts: Counter = Counter()
        for f in sorted((HERE.parent / 'website' / 'public').glob('*soldiers.json')):
            for r in json.loads(f.read_text(encoding='utf-8')):
                counts.update(re.findall(r'\b[a-zčćžšđ]{3,}\b', r.get('additional_info') or ''))
        spelled: dict = {}
        table: Counter = Counter()
        for w, n in counts.items():
            k = fold(w)
            table[k] += n
            if n > spelled.get(k, (0, ''))[0]:
                spelled[k] = (n, w)
        WORDS['table'], WORDS['spelled'] = table, {k: w for k, (n, w) in spelled.items()}
    table, spelled = WORDS['table'], WORDS['spelled']
    # the biography starts with "rođen(a)", which the OCR breaks and garbles past the word table ("po 4 đen",
    # "ro- + đen", "robsp", "Bega", "4 rođen"): a few short words before the first date or year, none of them a word
    # the site knows but the garbled "rođen" itself, are that word
    date = re.search(r'\b\d{1,2}\.\s|\b1[89]\d\d\b|\b19\d\b', text)
    if date:
        prefix = text[:date.start()]
        words = re.findall(r'[A-Za-zČĆŽŠĐčćžšđ]+', prefix)

        def garbled(w):
            k = fold(w.lower())
            return len(w) <= 2 or table[k] < 5 or min(_distance(k, 'roden', 2), _distance(k, 'rodena', 2)) <= 2
        if len(prefix.split()) <= 4 and not re.match(r'\W*rođena?\s', prefix) and all(map(garbled, words)) and \
                'oko' not in words:
            text = ('rođena ' if re.search(r'a\W*$', prefix.strip()) or prefix.strip().startswith('rođena')
                    else 'rođen ') + text[date.start():]

    def one(m):
        w = m.group(0)
        if len(w) < 4 or not (w.islower() or w[1:].islower() and len(w) >= 6):
            return w
        k = fold(w.lower())
        if table[k] >= 5:
            return w if re.search('[čćžšđ]', w) or not w.islower() else spelled[k]
        # the list's own words, whose first letter the OCR garbles too ("potinuo", "ioginuo", "pošnuo")
        key = [x for x in KEYWORDS if abs(len(x) - len(k)) <= 1 and _distance(k, fold(x), 2) <= (1 if len(x) < 7 else 2)]
        if len(key) == 1:
            return key[0]
        near = CORPUS.nearest(w.lower(), table, least=5) if w.islower() else ''
        return spelled.get(near, w) if near else w
    text = re.sub(r'[A-Za-zČĆŽŠĐčćžšđ]+', one, text)
    return re.sub(r'(?<=\s)[vVyY](?=\s)', 'u', text)


# names the page doesn't print or the rules can't read: number -> (surname, father, given, what he was called)
NAMES = {
    1199: ('Jovanović', 'Nika', 'Vladimir', ''),        # the entry's first line is not printed: see the lines file
    672: ('Mudreša', 'Joka', 'Milutin', ''),
    13: ('Gatalo', 'Rista', 'Milutin', ''), 20: ('Đurić', 'Labuda', 'Nikola', ''), 29: ('Ivanović', 'Rada', 'Vuko', ''),
    35: ('Iličković', 'Jovana', 'Miodrag', 'Tićo'), 41: ('Kapisoda', 'Rada', 'Šćepan', ''),
    82: ('Pejović', 'Pera', 'Ljubomir', 'Ljubo'), 96: ('Radulović', 'Nikole', 'Spasoje', ''),
    98: ('Radusinović', 'Ilije', 'Blagota', 'Blažo'), 102: ('Ražnatović', 'Mihaila', 'Nikola', ''),
    109: ('Ćosović', 'Luke', 'Vuko', ''), 110: ('Uskoković', 'Milutina', 'Dragica', ''),
    111: ('Škuletić', 'Rada', 'Savo', ''), 115: ('Batrićević', 'Butora', 'Božidar', ''),
    117: ('Batrićević', 'Labuda', 'Đorđe', 'Đoko'), 136: ('Lipovina', 'Luke', 'Đuro', ''),
    154: ('Zuber', 'Laza', 'Vaso', ''), 176: ('Filipović', 'Pera', 'Đuro', ''), 190: ('Martinović', 'Kića', 'Dušan', ''),
    210: ('Bogdanović', 'Kićuna', 'Mirko', ''), 217: ('Vukčević', 'Sava', 'Jole', ''),
    306: ('Vojvodić', 'Đurana', 'Petar', ''), 349: ('Đurašević', 'Sava', 'Mašan', ''),
    397: ('Popović', 'Joka', 'Luka', ''), 427: ('Šaban', 'Joka', 'Daro', ''), 477: ('Janković', 'Lazara', 'Milan', ''),
    488: ('Jovićević', 'Marka', 'Božo', ''), 489: ('Jovićević', 'Marka', 'Božo', ''),
    495: ('Jovićević', 'Luke', 'Jovan', ''), 496: ('Jovićević', 'Mijata', 'Mato', ''), 518: ('Lopičić', 'Iva', 'Đoko', ''),
    529: ('Marković', 'Stevana', 'Vuko', ''), 547: ('Pejović', 'Đura', 'Stanko', ''),
    557: ('Petričević', 'Jovana', 'Marko', ''), 559: ('Petričević', 'Marka', 'Milo', ''),
    560: ('Petričević', 'Staniše', 'Milo', ''), 567: ('Ražnatović', 'Andrije', 'Dušan', ''),
    584: ('Strugar', 'Markiše', 'Ivan', ''), 605: ('Šofranac', 'Mitra', 'Marko', ''),
    606: ('Šofranac', 'Petra', 'Milovan', ''), 640: ('Đurković', 'Blagote', 'Dušan', 'Đaro'),
    653: ('Kovačević', 'Luke', 'Milorad', ''), 659: ('Lompar', 'Iva', 'Đorđije', 'Đoko'),
    660: ('Lompar', 'Nika', 'Marko', ''), 690: ('Radović', 'Luke', 'Spasoje', ''), 705: ('Rajković', 'Draga', 'Špiro', ''),
    730: ('Vujović', 'Đuraša', 'Jagoš', ''), 735: ('Vukčević', 'Tomaša', 'Đuro', ''), 760: ('Popivoda', 'Mata', 'Miloš', ''),
    772: ('Kaluđerović', 'Sava', 'Milo', ''), 777: ('Mitrović', 'Filipa', 'Andrija', ''),
    778: ('Pajović', 'Rada', 'Vasilije', ''), 801: ('Krivokapić', 'Sima', 'Krsto', ''),
    807: ('Krivokapić', 'Đura', 'Periša', ''), 822: ('Popović', 'Spasoja', 'Pavle', ''),
    866: ('Vučinić', 'Bogdana', 'Gojko', ''), 878: ('Gardašević', 'Goluba', 'Obren', ''),
    895: ('Mićunović', 'Steva', 'Vuko', ''), 926: ('Barović', 'Mijajla', 'Simo', ''),
    951: ('Radulović', 'Simona', 'Vuko', ''), 967: ('Radulović', 'Blagote', 'Savo', ''),
    972: ('Sekulić', 'Draga', 'Nikola', ''), 1001: ('Jovović', 'Miloša', 'Vlado', ''),
    1003: ('Jovović', 'Jovana', 'Dragutin', 'Drago'), 1006: ('Jovović', 'Radovana', 'Radosav', 'Rajko'),
    1039: ('Stamatović', 'Andrije', 'Radovan', ''), 1040: ('Stamatović', 'Mijajla', 'Radosav', ''),
    1094: ('Vukmanović', 'Đikana', 'Jelena', ''), 1161: ('Đukanović', 'Nikole', 'Gavro', ''),
    1203: ('Jovanović', 'Joka', 'Milivoje', ''), 1223: ('Klisić', 'Rada', 'Pavle', ''),
    1229: ('Knežević', 'Đura', 'Nikola', ''), 1237: ('Kovačević', 'Ilije', 'Špiro', ''),
    1259: ('Leković', 'Mila', 'Vladimir', 'Vlado'), 1278: ('Marković', 'Špira', 'Božidar', ''),
    1279: ('Marković', 'Nika', 'Branko', ''), 1291: ('Marković', 'Boža', 'Uroš', ''),
    1292: ('Marović', 'Marka', 'Blažo', ''), 1318: ('Mišljen', 'Pera', 'Arsenije', ''),
    1334: ('Orlandić', 'Maša', 'Gojko', ''), 1344: ('Orlandić', 'Joka', 'Špiro', ''),
    1347: ('Pekić', 'Rada', 'Božo', ''),               # the page has "ВОЖО"
    1366: ('Plamenac', 'Laza', 'Jovan', ''), 1368: ('Plamenac', 'Joka', 'Svetozar', 'Sveto'),
    1381: ('Radoman', 'Mila', 'Blažo', ''), 1397: ('Sjekloća', 'Mila', 'Svetozar', ''),
    1416: ('Tomašević', 'Jola', 'Ivo', ''), 1417: ('Tomašević', 'Jola', 'Milutin', 'Milo'),
    1483: ('Sanković', 'Mitra', 'Niko', ''), 1505: ('Đedović', 'Nika', 'Marko', ''),
    1515: ('Medigović', 'Miloša', 'Milica', ''), 1527: ('Pavlović', 'Vida', 'Mitar', ''),
    1542: ('Šaljaga', 'Luko', 'Andrija', ''), 1567: ('De Benedeti', '', 'Ernesto', ''),
    1568: ('De Benedeti', 'Laza', 'Milica', ''), 1586: ('Đukanović', 'Pera', 'Neđeljko', ''),
    1659: ('Berjašević', 'Omera', 'Sulejman', ''), 1661: ('Junković', 'Đoke', 'Anton', ''),
    1697: ('Brašnja', 'Nelja', 'Rizaja', ''), 1707: ('Dabović', 'Luke', 'Marko', ''),
    1716: ('Đakonović', 'Vučete', 'Luka', ''), 1735: ('Maksimović', 'Alekse', 'Dušan', ''),
    1748: ('Nuculović', 'Prelje', 'Marko', ''), 1808: ('Katelan', 'Jakoba', 'Jozo', ''),
    1811: ('Lalošević', 'Ilije', 'Andrija', ''), 1824: ('Mihailović', 'Milorada', 'Darislav', ''),
    1910: ('Matković', 'Josipa', 'Viktor', 'Vito'), 1913: ('Mikijeljević', 'Nika', 'Joko', ''),
    1914: ('Mikijeljević', 'Jovana', 'Ljubo', ''), 1916: ('Moric', 'Iva', 'Vaso', ''),
    1927: ('Petković', 'Ilije', 'Nikola', ''), 1928: ('Petković', 'Šima', 'Tripo', ''),
    1929: ('Petković', 'Đura', 'Frano', ''), 1940: ('Raičević', 'Boška', 'Krsto', ''),
    1948: ('Smodlaka', '', 'Meljko', ''), 1966: ('Batuta', 'V.', 'Mare', ''), 1968: ('Batuta', 'Jova', 'Savo', ''),
    2000: ('Ercegović', 'Jova', 'Vlado', ''), 2007: ('Ivetić', 'M.', 'Dušan', ''), 2018: ('Marinović', 'Laza', 'Ilija', ''),
    2064: ('Ivančević', 'Sava', 'Đuro', ''), 2083: ('Martinović', 'Ilije', 'Mitar', ''),
    2095: ('Stanišić', 'Jova', 'Dušan', ''), 2096: ('Stanišić', 'Đura', 'Ilija', ''),
    2098: ('Stanišić', 'Jova', 'Krsto', ''), 2099: ('Stanišić', 'Nika', 'Krsto', ''),
}


# The author counts among the fallen fighters "everyone who died in the war and belonged to the NOP" (his note under
# the title), its activists too, and none of the victims of terror; by the rule for such lists (the user's decision of
# 2026-10-14) only the fighters go in: the entry says borac, names a military duty or an army unit
# (parse_mosorski_odred_2.fighter, or "u 2. bataljonu ...", "u Lovćenskom NOP odredu"), or he fell, died of wounds,
# was captured or went missing; one shot, dead in a camp or prison, killed at home, or killed as an illegal party
# worker stays out
UNIT_IN = re.compile(r'\bu\s+(?:\S+\s+){0,4}(?:bataljon\w*|brigad\w*|odred\w*|čet[ia]\b|divizij\w*|korpus\w*|KNOJ\w*|'
                     r'artiljerij\w*|NOVJ|NOV\b|partizan\w*|eskadril\w*|bateriji)|\bna\s+vojnoj\s+dužnosti', re.I)
COMBAT = re.compile(r'\bpogin(?:uo|ula)\b|\bpodleg\w*\b|\bzadobijen\w*|\bu\s+borbi\b|\bzarobljen\w*|\bnesta[oa]\b|'
                    r'\branjen\w*', re.I)
NOT_FIGHTER = re.compile(r'kao\s+(?:ilegal\w*|aktivist\w*|talac|taoc\w*|odbornik\w*|saradnik\w*|politički\s+radnik)|'
                         r'od\s+strane\s+(?:četnik|okupator|italijan|njemač|nijemac|ustaš|bugar|kvisling)\w*|'
                         r'bombardovanj\w*|zaklan\w*|samoubistv\w*', re.I)


def fighter(rec: dict) -> bool:
    text = rec['additional_info']
    return mos.fighter(rec) or bool(UNIT_IN.search(text)) or bool(COMBAT.search(text) and not NOT_FIGHTER.search(text))


ORDER = 'АБВГДЂЕЖЗИЈКЛЉМНЊОПРСТЋУФХЦЧЏШ'
INITIAL = {'Lj': 'Љ', 'Nj': 'Њ', 'Dž': 'Џ', 'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'Đ': 'Ђ', 'E': 'Е',
           'Ž': 'Ж', 'Z': 'З', 'I': 'И', 'J': 'Ј', 'K': 'К', 'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р',
           'S': 'С', 'T': 'Т', 'Ć': 'Ћ', 'U': 'У', 'F': 'Ф', 'H': 'Х', 'C': 'Ц', 'Č': 'Ч', 'Š': 'Ш'}


def alphabet_fix(recs: list[dict]) -> None:
    """The font's Ђ reads as Б: a surname read with B among a place's names in the Cyrillic alphabet's order
    (А Б В Г Д Ђ Е ...) whose neighbours stand after В before it and after Ђ behind it is a Đ one ("БУРИЋ" between
    ГАТАЛО and ИВАНОВИЋ is Đurić); the names the page gave by hand (NAMES) stay"""
    def key(r):
        s = r['last_name']
        ch = INITIAL.get(s[:2]) or INITIAL.get(s[:1])
        return ORDER.index(ch) if ch else -1
    groups: dict[str, list] = {}
    for r in recs:
        groups.setdefault(r['additional_info'].split(': ')[0], []).append(r)
    b, dj = ORDER.index('Б'), ORDER.index('Ђ')
    for rs in groups.values():
        keys = [key(r) for r in rs]
        for k, r in enumerate(rs):
            if keys[k] != b or r['no'] in NAMES:
                continue
            before = next((keys[i] for i in range(k - 1, -1, -1) if keys[i] not in (b, dj, -1)), -1)
            after = next((keys[i] for i in range(k + 1, len(rs)) if keys[i] not in (b, dj, -1)), len(ORDER))
            if before > b and after > dj:
                old = r['last_name']
                r['last_name'] = 'Đ' + old[1:]
                r['name'] = r['name'].replace(old, r['last_name'], 1)


def entry(e: dict, before: dict | None) -> dict:
    """The entry as a record of the book; before: the entry above it, whose surname a dash repeats ("--- Вука МИЛО")"""
    if e['dash'] and before:
        _, father, given, nick, fnick, n = head_of([[0, 0, 0, 0, 'ХХ', 99]] + e['words'])
        last, n = before['last_name'], n - 1
    else:
        last, father, given, nick, fnick, n = head_of(e['words'])
    if e['no'] in NAMES:
        last, father, given, nick = NAMES[e['no']]
    rest = fix_text(text_of(e['words'][n:])).lstrip(' ,.;')
    born = re.search(r'ro[đd]en[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)\.?\s*(?:god\w*\.?\s*)?(?:u|na)\s+'
                     r'(?:s\.\s*|selu\s+)?([A-ZČĆŽŠĐ]\w+(?:\s+[A-ZČĆŽŠĐ]\w+)?)', rest)
    death = None
    for d in DEATH.finditer(rest):
        death = d
    when = None
    if death:
        dm = re.search(rf'(\d{{1,2}})\.\s*(januar|februar|mart|april|maj|jun|jul|avgust|septemb|oktob|novemb|decemb)\w*\s+{death.group(3)}',
                       death.group(0))
        when = parse_when(f'{dm.group(1)}. {dm.group(2)} {death.group(3)}') if dm else None
    first = [ln for p, ln in e['lines'] if p == e['page']]
    heading = ', '.join(x for x in (e['srez'], e['place']) if x)
    shown = ' '.join(x for x in (last, father + (f' ({fnick})' if fnick and father else ''), given, nick) if x)
    rec = {'soldier_id': f"{PREFIX}{e['no']:06d}", 'name': shown,
           'last_name': last, 'also': [], 'first_name': given, 'nick': nick, 'fathers_name': father, 'no': e['no'],
           'birth_year': born.group(1) if born and 1850 < int(born.group(1)) < 1933 else '',
           'born_in': nominative(born.group(2)) if born else '',
           'death_year': death.group(3) if death else '', 'death_date': iso(when[0]) if when and when[0][2] else '',
           'units': sorted({code for pat, code in UNITS if re.search(pat, rest, re.I)}),
           'additional_info': f'{TITLE}, {heading}: {rest}' if heading else f'{TITLE}: {rest}', 'list': TITLE,
           'pdf_file': PDF, 'pdf_page': e['page'], 'pdf_x': round(first[0]['x0'], 1), 'pdf_y': round(first[0]['top'] - 1, 1),
           'pdf_x_left': round(min(ln['x0'] for ln in first), 1), 'pdf_x_end': round(max(ln['x1'] for ln in first) + 1, 1),
           'pdf_y_end': round(max(ln['bottom'] for ln in first) + 1, 1)}
    return rec


def nominative(place: str) -> str:
    """A birthplace the entry gives in the locative ("u Cetinju", "u Zagredi"): the nominative the site knows best"""
    from itertools import product
    from extract_structured_fields import Extractor
    words = place.split()
    best = (CORPUS.places[fold(place)], place)
    for combo in product(*(Extractor._variants(Extractor, w) for w in words)):
        cand = ' '.join(combo)
        n = CORPUS.places[fold(cand)]
        if cand != place and n > best[0]:
            best = (n, cand)
    return best[1]


def main() -> None:
    global CORPUS
    CORPUS = Corpus()
    raw = read()
    recs: list[dict] = []
    for e in sorted(raw, key=lambda e: e['no']):
        recs.append(entry(e, recs[-1] if recs else None))
    alphabet_fix(recs)
    every = recs
    recs = [r for r in every if fighter(r)]
    print(f'{len(every)} entries, {len(recs)} fighters kept, {len(every) - len(recs)} left out (shot, died in camps '
          f'and prisons, killed at home, illegal workers)')
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    # the book numbers 2,107 entries, and read in the page's order the numbers rise by one
    order = sorted(raw, key=lambda e: (e['page'], e['band'], e['col'], e['top']))
    bad = [(a['no'], b['no'], b['page']) for a, b in zip(order, order[1:]) if b['no'] != a['no'] + 1]
    if bad or len(every) != 2107 or [r['no'] for r in every] != list(range(1, 2108)):
        print(f'  CHECK the numbers: {len(every)} entries, breaks in the reading order {bad}')
    print(f"  no birth year: {sum(not r['birth_year'] for r in recs)}, no birthplace: {sum(not r['born_in'] for r in recs)}, "
          f"no father: {sum(not r['fathers_name'] for r in recs)}, death year: {sum(bool(r['death_year']) for r in recs)}, "
          f"units: {Counter(u for r in recs for u in r['units'])}")
    if '--heads' in sys.argv:
        for h, n in Counter(r['additional_info'].split(': ')[0] for r in recs).items():
            print(f'    {n:4d} {h}')
    if '--sample' in sys.argv:
        random.seed(5)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"    {r['no']}. {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['units']} | "
                  f"{r['additional_info'][len(TITLE):][:120]}")


if __name__ == '__main__':
    main()
