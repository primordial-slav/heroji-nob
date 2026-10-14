"""
Compute the box each soldier's entry covers on its source page.

The website's PDF viewer highlights a soldier's entry with a box. This script
stores that box's right and bottom edges (pdf_x_end, pdf_y_end) next to the
entry start (pdf_x, pdf_y), in the same viewer coordinate space
(pdf_coords.viewer_words), plus pdf_x_left where the entry's lines reach left
of its first line (books whose paragraphs indent only the first line).

The box starts at the stored entry start and follows the entry's lines down
its column. It stops before:
  - the start of another soldier on the same page (from the unit's own records),
  - a line that starts a new entry by the book's indentation, for entries the
    data doesn't know about: back at the first line's x where continuation
    lines are indented (hanging indent, numbered entries; at the x where the
    column's known entries start, if the first line starts right of it, as
    where a scan cut or garbled its first letters), or indented like the
    first line where only first lines are (Cyrillic books, 6. krajiška's
    appendix), after a line that ends a sentence. The style is measured per
    book and page, from the lines that follow known entry starts; books set
    flush rely on the next two rules,
  - a vertical gap wider than the book's line spacing (headings, footnotes,
    page numbers, blank space between flush entries),
  - the end of the column. An entry that runs on to the next column or page
    is only boxed on the page where it starts.
Scan specks the OCR read as characters in the margins are left out of lines.

It runs last in the data pipeline, after corrections (apply_corrections.py
calls fill_boxes), so the boxes always follow the final positions. Idempotent:
the boxes depend only on the PDFs and each record's pdf_file/pdf_page/pdf_x/pdf_y. Entries
of other books merged into a record (its other_sources) get their boxes the same way.

Reading words is slow (~0.2 s a page), so the lines of every page read are
cached under data-extraction/.cache/ (keyed by PDF size and mtime).

Usage:
    python data-extraction/entry_boxes.py                 # dry run: stats only
    python data-extraction/entry_boxes.py --apply         # write the boxes
    python data-extraction/entry_boxes.py --brigade 1 --apply
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

ROOT = _HERE.parent
PDF_DIR = ROOT / 'website' / 'public' / 'pdfs'
CACHE_DIR = _HERE / '.cache' / 'entry_boxes'
CACHE_VERSION = 3

BOX_FIELDS = ('pdf_x_end', 'pdf_y_end', 'pdf_x_left', 'pdf_rects')

# Lists that run the names on, comma after comma, under each heading (Druga proleterska's fallen, by place and
# date): their parser boxes each name's own words, in two boxes (pdf_rects) where the name runs on to the next
# line, and those boxes are kept; a column-down box would hold a dozen names.
INLINE_ENTRIES = {'druga-proleterska.pdf', '12-dalmatinska.pdf', '12-vojvodjanska.pdf', '13-vojvodjanska.pdf',
                  '7-srpska.pdf',   # these three: their parsers' boxes (layouts this module misreads)
                  '11-krajiska-zene.pdf',   # 11. krajiška's women, names run on
                  'pozega-cete.pdf',   # the Požega companies' rolls (Užički odred, 2. proleterska): names run on
                  '4-proleterska-formiranje.pdf',   # the 4. proleterska at formation: a table over each spread, its rows the parser's
                  'ludbreg-poginuli.pdf',   # the Ludbreg lists: the name left, its place set apart on the right
                  '3-banijska.pdf',   # 3. banijska: names only, three columns that stand anywhere
                  '1-tenkovski-bataljon.pdf',   # Prvi tenkovski bataljon: two narrow columns left of the page's middle
                  'dalmatinci-prva-proleterska.pdf',   # Dalmatinci u Prvoj proleterskoj: two or three columns, a page each its own
                  'proleterski-bataljon-bk.pdf',   # Proleterski bataljon Bosanske krajine: bio blocks beside the portraits
                  'tuzla-spomen-knjiga.pdf',   # the Tuzla memorial book: bios beside photographs (its records in unit 122)
                  'spomenica-crnogorskim-antifasistima.pdf',   # a table: the parser boxes each row
                  '4-pomorski-sektor.pdf',   # IV pomorski obalni sektor: the fallen's name left, death right (roster boxed alike)
                  'kokrski-odred.pdf',   # Kokrški odred: names run on in a few paragraphs (each boxed by its lines)
                  'viski-bataljon.pdf',   # Viški dobrovoljački bataljon: names run on under each platoon
                  # books across units whose names run on (Gončin's and Tmušić's Srem): their records in unit 122
                  'u-rovovima-srema-poginuli.pdf', 'sremski-front-poginuli.pdf'}


# ─────────────────────────────────────────────
# Page reading
# ─────────────────────────────────────────────

# Books printed in two columns; the gutter is found on every page, since it
# moves between odd and even pages.
TWO_COLUMN = {
    'iskra-in-plamen-padli.pdf',            # Iskra in plamen 3: the dead of Polje's villages, the fallen in the army
    'cazinska-krajina-pali-borci.pdf',      # Stradanja u Cazinskoj krajini: the fallen fighters, a line each
    'susak-rijeka-spomenica.pdf',           # Sušak i Rijeka u NOB: the spomenica's holders, a name a line
    'zascitna-enota-vpv.pdf',               # the protection battalion of the Slovene leadership: four lists
    '8-krajiska-sjecanja-poginuli.pdf',     # Osma krajiška - sjećanja boraca: the fallen, landscape pages
    'mostarski-bataljon.pdf',               # Mostarski bataljon (Ćemalović): the fighters' bios
    '18-srpska.pdf',                        # 18. srpska (Milosavljević): everyone in the brigade
    'eskadrile-novj.pdf',                   # 1. i 2. eskadrila NOVJ (Pejčić): the squadrons' people
    'sercerjeva.pdf',                       # Šercerjeva brigada (Ambrožič-Novljan): volunteers, the fallen
    '3-diverzantski-odred.pdf',             # Treći diverzantski odred (Karanović): the roster, the fallen
    '42-vazduhoplovna.pdf',                 # 42. vazduhoplovna divizija (Pejčić): the division's people
    '9-dalmatinska-divizija.pdf',           # 9. dalmatinska divizija (Egić): the fallen, names only
    '3-dalmatinska-poginuli.pdf',           # 3. dalmatinska (Egić): the fallen, names only
    'zagrebacki-odred.pdf',                 # Zagrebački odred: the roster, a fighter a line or two
    'hak-10-korenica-udbina.pdf',           # Korenica i Udbina (Karlovac knj. 10): the fallen
    'hak-14-donji-lapac.pdf',               # Donji Lapac (Karlovac knj. 14): the fallen
    'hak-19-vojnic.pdf',                   # Karlovac knj. 19: the fallen
    'hak-18-slunj-veljun.pdf',             # Karlovac knj. 18: the fallen
    'hak-15-duga-resa.pdf',                # Karlovac knj. 15: the fallen
    'hak-12-dreznica.pdf',                 # Karlovac knj. 12: the fallen
    'hak-16-gornje-dubrave.pdf',           # Karlovac knj. 16: the fallen
    'hak-13-gracac.pdf',                    # Gračac (Karlovac knj. 13): the fallen
    'hak-7-plascanska-dolina.pdf',          # Plaščanska dolina (Karlovac knj. 7): the fallen
    'bitka-kod-oborova-poginuli.pdf',       # Bitka kod Oborova: the names in two columns
    'moste-polje-spomenica-1941.pdf',       # Moste-Polje: the spomenica holders, each entry hanging
    'vis-spomenica-1941.pdf',               # Vis: the spomenica holders, a name a line
    'jevreji-jugoslavije-ucesnici-nor.pdf', # Romano, Jevreji Jugoslavije: the participants, each entry hanging
    '13-proleterska-spisak.pdf',
    '7-krajiska-spisak.pdf',
    '11-dalmatinska.pdf',
    'kalnicki-odred.pdf',
    '8-kordunaska-divizija.pdf',
    'karlovacka.pdf',                       # Karlovačka: both lists
    '3-primorsko-goranska.pdf',             # 3. primorsko-goranska: officers and medics, the fallen
    '6-dalmatinska.pdf',                    # 6. dalmatinska: the fallen
    '8-banijska-poginuli.pdf',              # 8. banijska: the fallen and dead
    'cankarjeva.pdf',
    'gubceva.pdf',
    'zidanskova.pdf',
    'skofjeloski-odred.pdf',
    'istrski-odred.pdf',
    '1-slovenska-artilerijska.pdf',
    '1-kosovsko-metohijska.pdf',
    '19-sjevernodalmatinska.pdf',
    '32-divizija-borci.pdf',
    '6-krajiska-prezivjeli.pdf',
    '17-slavonska-poginuli.pdf',
    '17-slavonska-prezivjeli.pdf',
    '19-bircanska.pdf',
    '3-krajiska-proleterska.pdf',
    'druga-licka-sjecanja-poginuli.pdf',
    'druga-licka-sjecanja-prezivjeli.pdf',
    'ljubljanska-brigada.pdf',
    'prva-vojvodjanska.pdf',
    'tuzlanski-odred.pdf',
    # Viktor Kučan, Borci Sutjeske: one chapter per brigade, per staff, and the Central Hospital
    'borci-sutjeske-1-dalmatinska.pdf',
    'borci-sutjeske-10-hercegovacka.pdf',
    'borci-sutjeske-15-majevicka.pdf',
    'borci-sutjeske-16-banijska.pdf',
    'borci-sutjeske-2-dalmatinska.pdf',
    'borci-sutjeske-3-dalmatinska.pdf',
    'borci-sutjeske-3-krajiska.pdf',
    'borci-sutjeske-4-proleterska.pdf',
    'borci-sutjeske-5-proleterska.pdf',
    'borci-sutjeske-6-istocnobosanska.pdf',
    'borci-sutjeske-7-banijska.pdf',
    'borci-sutjeske-7-krajiska.pdf',
    'borci-sutjeske-8-banijska.pdf',
    'borci-sutjeske-druga-proleterska.pdf',
    'borci-sutjeske-prva-proleterska.pdf',
    'borci-sutjeske-treca-proleterska.pdf',
    'borci-sutjeske-vrhovni-stab.pdf',
    'borci-sutjeske-1-proleterska-divizija.pdf',
    'borci-sutjeske-2-proleterska-divizija.pdf',
    'borci-sutjeske-3-udarna-divizija.pdf',
    'borci-sutjeske-7-banijska-divizija.pdf',
    'borci-sutjeske-centralna-bolnica.pdf',
}
# Books printed in more columns: {file: columns}; gutter k is looked for around k/columns of the width
MULTI_COLUMN = {
    '32-divizija.pdf': 4,           # a roster, names only
    'gradnikova.pdf': 3,            # Gradnikova: the fallen and the others, three columns
    'deveta.pdf': 3,                # Deveta brigada: the roster, three columns
    'zapadnodolenjski-odred.pdf': 3,  # Zapadnodolenjski odred: roster and fallen, three columns
    'beogradski-bataljon.pdf': 3,   # Beogradski bataljon: the roster, three columns of bios
}


# Books two columns on some pages only: {file: pages}
TWO_COLUMN_PAGES = {
    '1-dalmatinska-monografija.pdf': range(1, 5),  # 1. dalmatinska: the company commanders and commissars side by side
    '14-srednjobosanska.pdf': range(30, 65),     # the fallen in one column, the survivors in two
    'braciceva.pdf': range(25, 72),              # Bračičeva: the fallen in one column, the survivors in two
    '15-srpska.pdf': range(1, 13),               # 15. srpska: the roster in two columns, the fallen and wounded in one
    '1-konjicka.pdf': range(5, 12),              # 1. konjička: the fallen in one column, the war roster in two
    '13-hercegovacka.pdf': range(15, 33),              # 13. hercegovačka: the roster of names
    'hak-20-gospic-perusic.pdf': range(1, 61),   # Gospić i Perušić: the fallen in two columns, the spomenica in one
    'kosovelova.pdf': range(1, 18),              # Kosovelova: the fallen in two columns, the officers in one
}
# two-column books whose right column sets its entry numbers in the gutter, left of the column's text
NUMBERS_IN_GUTTER = {'hak-20-gospic-perusic.pdf'}
# pages whose gutter the words don't show (a title across it): the split's x
GUTTER = {('hak-20-gospic-perusic.pdf', 1): 188.0, ('moste-polje-spomenica-1941.pdf', 1): 225.0}


def page_columns(pdf_file: str, page: int | None = None) -> int:
    if pdf_file in TWO_COLUMN_PAGES:
        return 2 if page in TWO_COLUMN_PAGES[pdf_file] else 1
    return 2 if pdf_file in TWO_COLUMN else MULTI_COLUMN.get(pdf_file, 1)


def find_gutter(words: list[dict], width: float, lo_frac: float = 0.35, hi_frac: float = 0.65) -> float:
    """Middle of the widest band of x (between lo_frac and hi_frac of the page)
    that the fewest words cross."""
    lo, hi = int(width * lo_frac), int(width * hi_frac)
    cover = [0] * (hi - lo + 1)
    for w in words:
        a, b = max(lo, int(w['x0'] - 1)), min(hi, int(w['x1'] + 1))
        for x in range(a, b + 1):
            cover[x - lo] += 1
    least = min(cover)
    best, run_start = (0, lo), None
    for i, c in enumerate(cover + [least + 1]):
        if c == least and run_start is None:
            run_start = i
        elif c != least and run_start is not None:
            if i - run_start > best[0]:
                best = (i - run_start, lo + (run_start + i - 1) / 2)
            run_start = None
    return float(best[1])


def _cluster(words: list[dict], tol: float) -> list[list[dict]]:
    lines: list[list[dict]] = []
    for w in sorted(words, key=lambda w: w['top']):
        if lines and w['top'] - lines[-1][0]['top'] <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    for ws in lines:
        ws.sort(key=lambda w: w['x0'])
    return lines


def _alnum(w: dict) -> int:
    return sum(c.isalnum() for c in w['text'])


def _strip_specks(ws: list[dict], h: float) -> list[dict]:
    """Drop scan specks the OCR read as characters ('0', 'i', '>', '.:,') from
    the ends of a line, where they sit apart from the text in the margin."""
    def speck(w, neighbour):
        gap = max(neighbour['x0'] - w['x1'], w['x0'] - neighbour['x1'])
        return (_alnum(w) == 0 and gap > 0.8 * h) or (_alnum(w) <= 2 and gap > 1.2 * h)
    while len(ws) > 1 and speck(ws[-1], ws[-2]):
        ws = ws[:-1]
    while len(ws) > 1 and speck(ws[0], ws[1]):
        ws = ws[1:]
    return [] if all(_alnum(w) == 0 for w in ws) else ws


def group_lines(words: list[dict]) -> list[dict]:
    """Words → lines ({x0, x1, top, bottom, text}), top to bottom, without scan specks."""
    if not words:
        return []
    h = median(w['bottom'] - w['top'] for w in words)
    # blots read as one or two outsize letters
    words = [w for w in words if not (w['bottom'] - w['top'] > 1.6 * h and _alnum(w) <= 2)]
    kept = [w for ws in _cluster(words, 0.45 * h) for w in _strip_specks(ws, h)]
    out = []
    for ws in _cluster(kept, 0.45 * h):
        out.append({
            'x0': round(min(w['x0'] for w in ws), 1),
            'x1': round(max(w['x1'] for w in ws), 1),
            'top': round(min(w['top'] for w in ws), 1),
            'bottom': round(max(w['bottom'] for w in ws), 1),
            'text': ' '.join(w['text'] for w in ws),
        })
    return out


def read_page(page, columns: int = 1, numbers_in_gutter: bool = False, gutter: float | None = None) -> dict:
    """{'columns': [[line, ...], ...], 'split': x (or [x, ...] for more than two columns) or None,
    'width', 'height'} in viewer coordinates. numbers_in_gutter: the right column's entry numbers stand in the
    gutter (NUMBERS_IN_GUTTER), so the gutter is found without them; gutter: the split, where it is given (GUTTER)."""
    from pdf_coords import viewer_words
    words = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
    for w in words:     # pdfplumber versions differ in the last bits; don't let that flip a rounding
        for k in ('x0', 'x1', 'top', 'bottom'):
            w[k] = round(w[k], 2)
    width, height = float(page.width), float(page.height)
    if columns == 2 and words:
        split = gutter or find_gutter(
            [w for w in words if not (numbers_in_gutter and re.fullmatch(r'\d{1,3}[.,]?', w['text']))], width)
        cols = [[w for w in words if (w['x0'] + w['x1']) / 2 < split],
                [w for w in words if (w['x0'] + w['x1']) / 2 >= split]]
    elif columns > 2 and words:
        split = [find_gutter(words, width, k / columns - 0.1, k / columns + 0.1) for k in range(1, columns)]
        mid = lambda w: (w['x0'] + w['x1']) / 2
        cols = [[w for w in words if sum(mid(w) >= g for g in split) == c] for c in range(columns)]
    else:
        split, cols = None, [words]
    return {'columns': [group_lines(c) for c in cols], 'split': split,
            'width': round(width, 2), 'height': round(height, 2)}


def _read_pages(job) -> dict[str, dict]:
    import pdfplumber
    path, page_nos = job
    out = {}
    with pdfplumber.open(path) as pdf:
        for p in page_nos:
            if not 1 <= p <= len(pdf.pages):
                out[str(p)] = None
                continue
            page = pdf.pages[p - 1]
            name = Path(path).name
            out[str(p)] = read_page(page, page_columns(name, p), name in NUMBERS_IN_GUTTER, GUTTER.get((name, p)))
            # pdfplumber keeps every parsed page in memory otherwise (0.9 has no close())
            (getattr(page, 'close', None) or page.flush_cache)()
    return out


class PageCache:
    """Lines of each page read, per PDF, persisted under CACHE_DIR."""

    def __init__(self, pdf_dir: Path = PDF_DIR, cache_dir: Path = CACHE_DIR):
        self.pdf_dir, self.cache_dir = Path(pdf_dir), Path(cache_dir)
        self.books: dict[str, dict] = {}
        self.dirty: set[str] = set()

    def _stamp(self, pdf_file: str) -> list:
        st = (self.pdf_dir / pdf_file).stat()
        return [CACHE_VERSION, st.st_size, int(st.st_mtime)]

    def _book(self, pdf_file: str) -> dict:
        if pdf_file not in self.books:
            book = None
            path = self.cache_dir / (pdf_file + '.json')
            if path.exists():
                try:
                    with open(path, encoding='utf-8') as f:
                        book = json.load(f)
                except ValueError:
                    book = None
            if not book or book.get('stamp') != self._stamp(pdf_file):
                book = {'stamp': self._stamp(pdf_file), 'pages': {}}
            self.books[pdf_file] = book
        return self.books[pdf_file]

    def prefetch(self, wanted: dict[str, set[int]]):
        """Read every uncached page in wanted ({pdf_file: pages}), several PDFs at once."""
        jobs = []
        for pdf_file, page_nos in sorted(wanted.items()):
            book = self._book(pdf_file)
            missing = sorted(p for p in page_nos if str(p) not in book['pages'])
            for i in range(0, len(missing), 40):
                jobs.append((str(self.pdf_dir / pdf_file), missing[i:i + 40]))
        if not jobs:
            return
        print(f"  Reading {sum(len(j[1]) for j in jobs)} page(s) not in the cache...")
        if len(jobs) == 1:
            results = [_read_pages(jobs[0])]
        else:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=min(len(jobs), os.cpu_count() or 2)) as ex:
                results = list(ex.map(_read_pages, jobs))
        for (path, _), pages in zip(jobs, results):
            pdf_file = Path(path).name
            self.books[pdf_file]['pages'].update(pages)
            self.dirty.add(pdf_file)

    def pages(self, pdf_file: str, page_nos) -> dict[int, dict]:
        """{page_no: read_page(...)} for the requested 1-indexed pages (None past the end)."""
        self.prefetch({pdf_file: set(page_nos)})
        book = self.books[pdf_file]
        return {p: book['pages'][str(p)] for p in page_nos}

    def save(self):
        if not self.dirty:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for pdf_file in sorted(self.dirty):
            tmp = self.cache_dir / (pdf_file + '.json.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.books[pdf_file], f, ensure_ascii=False, separators=(',', ':'))
            os.replace(tmp, self.cache_dir / (pdf_file + '.json'))
        self.dirty.clear()


# ─────────────────────────────────────────────
# Entry boxes
# ─────────────────────────────────────────────

# Lists that give every soldier a single line with no space between them: there
# any line not known to start an entry still starts one (a soldier missing from
# the data), rather than continuing the entry above it.
ONE_LINE_ENTRIES = {
    'cazinska-krajina-pali-borci.pdf': range(1, 35),  # the fallen fighters of the Cazin region, a line each
    'susak-rijeka-spomenica.pdf': range(1, 3),        # the spomenica's holders of the Rijeka municipality
    'zascitna-enota-vpv.pdf': range(17, 19),          # the protection battalion's spomenica holders, a name a line
    '9-dalmatinska-divizija.pdf': range(1, 7),        # names only, a name a line
    'turopoljsko-posavski-odred.pdf': range(1, 5),    # a table, a row an entry
    '3-dalmatinska-poginuli.pdf': range(1, 4),
    '1-dalmatinska-monografija.pdf': range(1, 5),     # the company commanders and commissars, a name a line
    '6-istocnobosanska-dopuna.pdf': range(13, 14),    # those whose death was not established, a name a line
    '18-slavonska.pdf': range(30, 55),     # survivors
    '32-divizija.pdf': range(1, 42),       # the roster: one name a line, four columns
    '6-krajiska-prezivjeli.pdf': range(1, 17),   # survivors: one name a line, two columns
    '12-krajiska-prezivjeli.pdf': range(1, 71),  # 12. krajiška's survivors: a soldier a line, one column
    'dvanajsta.pdf': range(1, 41),         # XII. SNOUB: one soldier a line
    'skofjeloski-odred.pdf': range(1, 8),  # Škofjeloški odred: numbered names
    'tomsiceva-2.pdf': range(1, 33),       # Tomšičeva: a soldier a line
    'tomsiceva-3.pdf': range(1, 5),
    'tomsiceva-4.pdf': range(1, 107),
    'artilerija-9-korpusa.pdf': range(1, 9),     # Artilerija 9. korpusa: the roster, a soldier a line
    '14-hercegovacka.pdf': range(1, 33),         # 14. hercegovačka: everyone who served, a soldier a line
    '5-prekomorska.pdf': range(17, 20),          # 5. prekomorska: the officers, run on (the box is the name's line)
    '1-2-prekomorska.pdf': range(11, 15),        # 1. i 2. prekomorska: the officers, run on
    '9-srpska.pdf': range(1, 27),                # 9. srpska: the line-up (two names a line), the officers, the women
    '4-prekomorska.pdf': range(3, 8),            # 4. prekomorska: the officers, a name a line
    'novosadski-odred.pdf': range(1, 9),         # Novosadski odred: a member a line
    '3-diverzantski-odred.pdf': range(1, 5),     # Treći diverzantski odred: a name a line, two columns
    'kosovelova.pdf': range(18, 23),             # Kosovelova: the officers, a duty a line
    '15-srpska.pdf': range(1, 13),               # 15. srpska: the roster, names only
    '1-konjicka.pdf': range(5, 12),              # 1. konjička: the war roster, names only
    '13-hercegovacka.pdf': range(15, 33),              # 13. hercegovačka: the roster of names
    'hak-20-gospic-perusic.pdf': range(61, 77),  # Gospić i Perušić: the spomenica holders, a line each
    'vis-spomenica-1941.pdf': range(1, 2),       # Vis: the spomenica holders, a name a line
}


# Pages whose text layer puts part of the page below its bottom edge, by how much (pt) those lines lie below where
# the scan shows them: 6. krajiška p. 10, whose lower block (Čamber to Ćanković) the text layer sets 385.2 pt too low
TEXT_SHIFT = {('6-krajiska.pdf', 10): -385.2}


def _find_line(page: dict, x: float, y: float):
    """(column, line index) of the line an entry starting at (x, y) begins on, or
    None. The stored x can sit on a scan speck left of the name, so it only
    has to be near the line."""
    best = None
    for ci, col in enumerate(page['columns']):
        for li, ln in enumerate(col):
            dy = abs(ln['top'] - y)
            dx = max(ln['x0'] - x, x - ln['x1'], 0)
            if dy <= 6 and dx <= 80:
                key = (dy + 0.05 * dx, ci, li)
                if best is None or key < best:
                    best = key
    return best[1:] if best else None


def _layout(pitches: list[float], shifts: list[float]) -> dict:
    pitches = sorted(pitches)
    pitch, indent = median(pitches), median(shifts)
    gap = 1.5 * pitch
    # Some books set the name on a line of its own with space below it (Treća proleterska)
    first_gap = max(gap, 1.15 * pitches[int(0.95 * (len(pitches) - 1))])
    return {'pitch': pitch, 'indent': indent, 'gap': gap, 'first_gap': first_gap}


def book_layout(pages: dict[int, dict], starts: dict[int, set]) -> tuple[dict, dict[int, dict]]:
    """How a book sets its entries, measured on the lines that follow known entry
    starts: line pitch, and where continuation lines begin relative to the first
    line — right of it (hanging indent), left of it (only the first line is
    indented), or level with it (flush; entries are set apart by space).
    Returns the book's layout and, for pages with enough samples, the page's own
    (some books mix scans of different sizes)."""
    samples: dict[int, tuple[list, list]] = {}
    heights = []
    for pno, page in pages.items():
        if not page:
            continue
        pitches, shifts = samples.setdefault(pno, ([], []))
        for ci, col in enumerate(page['columns']):
            for li, ln in enumerate(col):
                heights.append(ln['bottom'] - ln['top'])
                if (ci, li) in starts[pno] and li + 1 < len(col) and (ci, li + 1) not in starts[pno]:
                    pitches.append(col[li + 1]['top'] - ln['top'])
                    shifts.append(col[li + 1]['x0'] - ln['x0'])
    all_pitches = [p for ps, _ in samples.values() for p in ps]
    if len(all_pitches) < 10:
        line_h = median(heights) if heights else 9.0
        return ({'style': 'flush', 'pitch': 1.1 * line_h, 'indent': 0.0,
                 'gap': 1.65 * line_h, 'first_gap': 1.65 * line_h}, {})
    book = _layout(all_pitches, [s for _, ss in samples.values() for s in ss])
    book['style'] = _style(book['indent'])
    per_page = {}
    for pno, (pitches, shifts) in samples.items():
        if len(pitches) >= 4:
            page = _layout(pitches, shifts)
            # a page's median can be thrown by space between name and bio (Treća proleterska)
            scale = min(1.25, max(0.85, page['pitch'] / book['pitch']))
            page.update(pitch=scale * book['pitch'], gap=scale * book['gap'], first_gap=scale * book['first_gap'])
            # appendices can indent differently (6. krajiška numbers its last pages
            # and indents their first lines)
            page['style'] = _style(page['indent']) if book['style'] != 'flush' else 'flush'
            # a page whose lines all start level is set flush even in a book that indents
            # (7. crnogorska: an unnumbered list before the numbered one, whose numbers hang left)
            level = sum(abs(s) <= 3 for s in shifts) / len(shifts)
            if page['style'] == 'flush' and level < 0.75:
                page['style'], page['indent'] = book['style'], book['indent']
            per_page[pno] = page
    return book, per_page


def _style(indent: float) -> str:
    return 'hanging' if indent > 4 else 'first_line' if indent < -4 else 'flush'


# the end of a sentence, before any closing bracket, quote or footnote mark
SENTENCE_END = re.compile(r"""[.!?][)\]"»“”*'’]*\s*$""")


def _starts_entry(ln: dict, first: dict, layout: dict, prev: dict, start_x: float | None = None) -> bool:
    """Does ln, the line after prev, begin a new entry, judged by the book's indentation? start_x is where the
    column's entries start (hanging indent): an entry whose first line starts right of it by more than half an
    indent (a scan that cuts or garbles the first letters, Borci Sutjeske) goes on as long as its lines start right
    of the others' starts. layout['col_indent'] is the column's own indent where it is clearly smaller."""
    half = abs(layout['indent']) / 2
    if layout['style'] == 'hanging':
        half = abs(layout.get('col_indent') or layout['indent']) / 2
        left = first['x0'] if start_x is None or first['x0'] <= start_x + half else start_x
        return ln['x0'] < left + half
    if layout['style'] == 'first_line':
        if ln['x0'] <= first['x0'] - half:
            return False
        # a line that goes on mid-sentence, or in lowercase, has lost its first characters to the text layer
        # (2. vojvođanska's "Čortanovci / — Inđija", whose dash is dropped); a line far right of the indent,
        # a page number or a heading, ends the entry all the same
        return (ln['x0'] > first['x0'] + abs(layout['indent'])
                or bool(SENTENCE_END.search(prev['text'])) and not ln['text'][:1].islower())
    return False


def entry_lines(col: list[dict], li: int, starts: set, layout: dict, one_line: bool = False) -> tuple[list[dict], str]:
    """The lines of the entry that begins at col[li], and why it ends there:
    'next' (a known entry start), 'one_line', 'gap', 'indent' or 'end' (of the column)."""
    first = col[li]
    # where the column's entries start: the median of its known starts (three at least)
    xs = sorted(col[lj]['x0'] for lj in starts)
    start_x = xs[len(xs) // 2] if len(xs) >= 3 else None
    lines = [first]
    for lj in range(li + 1, len(col)):
        ln, prev = col[lj], lines[-1]
        step = ln['top'] - prev['top']
        # a piece of the line above (skewed scan); in a list of one-line entries only if it overlaps that line,
        # since the pitch measured on such a book's few continuation lines can be twice its line spacing
        piece_step = 0.5 * (prev['bottom'] - prev['top']) if one_line else 0.5 * layout['pitch']
        if step < piece_step:
            lines.append(ln)
            continue
        if lj in starts:
            return lines, 'next'
        if one_line:
            return lines, 'one_line'
        if step > (layout['first_gap'] if len(lines) == 1 else layout['gap']):
            return lines, 'gap'
        if _starts_entry(ln, first, layout, prev, start_x):
            return lines, 'indent'
        lines.append(ln)
    return lines, 'end'


def _set_box(s: dict, page: dict | None, x0: float, x1: float, y1: float):
    # text past the edge of a cropped scan (a start off the page is a bad position; leave it be)
    if page and x0 < page['width']:
        x1 = min(x1, page['width'])
    if page and s['pdf_y'] < page['height']:
        y1 = min(y1, page['height'])
    s['pdf_x_end'] = round(x1, 1)
    s['pdf_y_end'] = round(y1, 1)
    if s.get('pdf_x') is None or abs(x0 - s['pdf_x']) > 1:
        s['pdf_x_left'] = round(x0, 1)
    else:
        s.pop('pdf_x_left', None)


def entries(soldiers: list[dict]):
    """Every printed entry of the records: each soldier's own, and those of other books merged into it
    (other_sources, see apply_corrections.apply_merge), which have the same position and box fields."""
    for s in soldiers:
        yield s
        # an entry from another unit's book (unit_file) is that unit's record, boxed in its own file; one from a book
        # across units (ref_book) is boxed with the book's entries (data-extraction/znaci/<book>-entries.json)
        yield from (o for o in s.get('other_sources', ()) if not o.get('unit_file') and not o.get('ref_book'))


def fill_boxes(soldiers: list[dict], cache: PageCache | None = None) -> dict:
    """Set pdf_x_end / pdf_y_end (and pdf_x_left) on every entry with a position (a record's own, and
    those in its other_sources), in place. Returns counts: boxed, unmatched (no text line at the stored start;
    given a one-line box), cleared (no position; stale box fields removed), what
    ended the boxed entries (see entry_lines), and the layout measured for each PDF."""
    own_cache = cache is None
    cache = cache or PageCache()
    stats = {'boxed': 0, 'unmatched': 0, 'cleared': 0, 'stops': Counter(), 'layouts': {}}
    by_page: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for s in entries(soldiers):
        if s.get('pdf_file') in INLINE_ENTRIES and s.get('pdf_y') is not None:
            stats['inline'] = stats.get('inline', 0) + 1
        elif s.get('pdf_file') and s.get('pdf_page') and s.get('pdf_y') is not None:
            by_page[s['pdf_file']][int(s['pdf_page'])].append(s)
        elif any(k in s for k in BOX_FIELDS):
            for k in BOX_FIELDS:
                s.pop(k, None)
            stats['cleared'] += 1

    for pdf_file in [f for f in by_page if not (cache.pdf_dir / f).is_file()]:
        stats['no_pdf'] = stats.get('no_pdf', 0) + sum(len(r) for r in by_page.pop(pdf_file).values())
    cache.prefetch({f: set(pages) for f, pages in by_page.items()})
    for pdf_file, recs_by_page in by_page.items():
        pages = cache.pages(pdf_file, list(recs_by_page))
        for pno, page in pages.items():
            dy = TEXT_SHIFT.get((pdf_file, pno))
            if page and dy:
                # the text layer's lines that lie below the page belong where the scan shows them
                pages[pno] = dict(page, columns=[[dict(ln, top=ln['top'] + dy, bottom=ln['bottom'] + dy)
                                                  if ln['top'] > page['height'] else ln for ln in col]
                                                 for col in page['columns']])
        # the line each record starts on, and every page's known entry starts
        at, starts = {}, defaultdict(set)
        for pno, recs in recs_by_page.items():
            for s in recs:
                hit = _find_line(pages[pno], s.get('pdf_x') or 0, s['pdf_y']) if pages[pno] else None
                at[id(s)] = hit
                if hit:
                    starts[pno].add(hit)
        book, per_page = book_layout(pages, starts)
        stats['layouts'][pdf_file] = book
        one_line_pages = ONE_LINE_ENTRIES.get(pdf_file, ())

        for pno, recs in recs_by_page.items():
            page = pages[pno]
            layout = per_page.get(pno, book)
            for s in recs:
                hit = at[id(s)]
                if hit is None:
                    # no text at the stored start (dropped from the text layer, or
                    # a stale position): one line, to the column's right edge
                    stats['unmatched'] += 1
                    x = s.get('pdf_x') or 0
                    cols = [c for c in (page or {}).get('columns', []) if c and min(ln['x0'] for ln in c) - 30 <= x]
                    col = cols[-1] if cols else []
                    right = sorted(ln['x1'] for ln in col)[int(0.9 * (len(col) - 1))] if col else x + 200
                    _set_box(s, page, x, max(right, x + 50), s['pdf_y'] + layout['pitch'])
                    continue
                ci, li = hit
                col = page['columns'][ci]
                col_starts = {lj for (c, lj) in starts[pno] if c == ci}
                entry_layout = layout
                if layout['style'] == 'hanging':
                    # an entry that starts where the others continue is set flush (7. crnogorska mixes
                    # unnumbered entries into the numbered list, whose numbers hang left of the text)
                    left = min(col[lj]['x0'] for lj in col_starts)
                    if 0.75 < (col[li]['x0'] - left) / layout['indent'] < 1.5:
                        entry_layout = dict(layout, style='flush')
                    else:
                        # the column's own indent, where it is clearly smaller than the page's (Borci Sutjeske,
                        # whose scans cut the left column's edge, indents it by 3 pt or not at all, the right by 10)
                        shifts = [col[lj + 1]['x0'] - col[lj]['x0'] for lj in col_starts
                                  if lj + 1 < len(col) and lj + 1 not in col_starts
                                  and 0.5 * layout['pitch'] < col[lj + 1]['top'] - col[lj]['top'] < 1.6 * layout['pitch']]
                        if len(shifts) >= 3 and abs(median(shifts)) < 1.5:
                            # a column whose lines all start level (a scan cut at that edge): only the known
                            # starts and gaps tell its entries apart
                            entry_layout = dict(layout, style='flush')
                        elif len(shifts) >= 3 and median(shifts) < 0.75 * layout['indent']:
                            entry_layout = dict(layout, col_indent=median(shifts))
                lines, why = entry_lines(col, li, col_starts, entry_layout, pno in one_line_pages)
                _set_box(s, page, min(ln['x0'] for ln in lines), max(ln['x1'] for ln in lines),
                         max(ln['bottom'] for ln in lines))
                stats['boxed'] += 1
                stats['stops'][why] += 1
    if own_cache:
        cache.save()
    return stats


def box_snapshot(soldiers: list[dict]) -> dict:
    """{soldier_id: box fields} (also of the entries merged into it), to count what fill_boxes changed."""
    return {s.get('soldier_id'): tuple(tuple(e.get(k) for k in BOX_FIELDS) for e in entries([s])) for s in soldiers}


def describe(stats: dict, changed: int) -> str:
    stops = ', '.join(f"{n} {why}" for why, n in stats['stops'].most_common())
    text = f"{stats['boxed']} boxed ({stops}), {changed} changed"
    if stats['unmatched']:
        text += f", {stats['unmatched']} with no text line at their start (one-line box)"
    if stats['cleared']:
        text += f", {stats['cleared']} without a position (box removed)"
    if stats.get('inline'):
        text += f", {stats['inline']} run-on names left as their parser boxed them"
    if stats.get('no_pdf'):
        text += f", {stats['no_pdf']} left alone (their PDF isn't in website/public/pdfs)"
    return text


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true', help='write the boxes (default: dry run)')
    ap.add_argument('--brigade', type=int, help='only this brigade code')
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT / 'scripts'))
    from name_utils import BRIGADE_CONFIGS
    from cleanup_text_fields import live_json_files

    live = live_json_files()
    cache = PageCache()
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if cfg['json_file'] not in live or (args.brigade and code != args.brigade):
            continue
        path = ROOT / 'website' / 'public' / cfg['json_file']
        text = path.read_text(encoding='utf-8')
        soldiers = json.loads(text)
        before = box_snapshot(soldiers)
        stats = fill_boxes(soldiers, cache)
        after = box_snapshot(soldiers)
        changed = sum(1 for sid, box in after.items() if before.get(sid) != box)
        print(f"  {cfg['name']} ({cfg['json_file']}): {describe(stats, changed)}")
        for pdf_file, lay in sorted(stats['layouts'].items()):
            print(f"      {pdf_file}: {lay['style']}, line pitch {lay['pitch']:.1f}, indent {lay['indent']:+.1f}")
        new_text = json.dumps(soldiers, ensure_ascii=False, indent=2)
        if args.apply and new_text != text:
            path.write_text(new_text, encoding='utf-8')
            print(f"    Written: {path}")
    cache.save()
    if not args.apply:
        print("\n  *** DRY RUN - use --apply to write the boxes ***")


if __name__ == '__main__':
    main()
