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
    lines are indented (hanging indent, numbered entries), or indented like the
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
INLINE_ENTRIES = {'druga-proleterska.pdf', '12-dalmatinska.pdf', '12-vojvodjanska.pdf'}   # the last: its parser's boxes (a layout this module misreads)


# ─────────────────────────────────────────────
# Page reading
# ─────────────────────────────────────────────

# Books printed in two columns; the gutter is found on every page, since it
# moves between odd and even pages.
TWO_COLUMN = {
    '13-proleterska-spisak.pdf',
    '7-krajiska-spisak.pdf',
    '11-dalmatinska.pdf',
    'kalnicki-odred.pdf',
    '8-kordunaska-divizija.pdf',
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
    # Viktor Kučan, Borci Sutjeske: one chapter per brigade
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
}
# Books printed in more columns: {file: columns}; gutter k is looked for around k/columns of the width
MULTI_COLUMN = {
    '32-divizija.pdf': 4,           # a roster, names only
    'gradnikova.pdf': 3,            # Gradnikova: the fallen and the others, three columns
    'zapadnodolenjski-odred.pdf': 3,  # Zapadnodolenjski odred: roster and fallen, three columns
}


# Books two columns on some pages only: {file: pages}
TWO_COLUMN_PAGES = {
    '14-srednjobosanska.pdf': range(30, 65),     # the fallen in one column, the survivors in two
    'braciceva.pdf': range(25, 72),              # Bračičeva: the fallen in one column, the survivors in two
}


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


def read_page(page, columns: int = 1) -> dict:
    """{'columns': [[line, ...], ...], 'split': x (or [x, ...] for more than two columns) or None,
    'width', 'height'} in viewer coordinates."""
    from pdf_coords import viewer_words
    words = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
    for w in words:     # pdfplumber versions differ in the last bits; don't let that flip a rounding
        for k in ('x0', 'x1', 'top', 'bottom'):
            w[k] = round(w[k], 2)
    width, height = float(page.width), float(page.height)
    if columns == 2 and words:
        split = find_gutter(words, width)
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
            out[str(p)] = read_page(page, page_columns(Path(path).name, p))
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
    '18-slavonska.pdf': range(30, 55),     # survivors
    '32-divizija.pdf': range(1, 42),       # the roster: one name a line, four columns
    '6-krajiska-prezivjeli.pdf': range(1, 17),   # survivors: one name a line, two columns
    'dvanajsta.pdf': range(1, 41),         # XII. SNOUB: one soldier a line
    'skofjeloski-odred.pdf': range(1, 8),  # Škofjeloški odred: numbered names
    'tomsiceva-2.pdf': range(1, 33),       # Tomšičeva: a soldier a line
    'tomsiceva-3.pdf': range(1, 5),
    'tomsiceva-4.pdf': range(1, 107),
    'artilerija-9-korpusa.pdf': range(1, 9),     # Artilerija 9. korpusa: the roster, a soldier a line
}


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


def _starts_entry(ln: dict, first: dict, layout: dict, prev: dict) -> bool:
    """Does ln, the line after prev, begin a new entry, judged by the book's indentation?"""
    half = abs(layout['indent']) / 2
    if layout['style'] == 'hanging':
        return ln['x0'] < first['x0'] + half
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
        if _starts_entry(ln, first, layout, prev):
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
        # an entry from another unit's book (unit_file) is that unit's record, boxed in its own file
        yield from (o for o in s.get('other_sources', ()) if not o.get('unit_file'))


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
