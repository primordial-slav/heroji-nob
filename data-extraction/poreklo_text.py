"""Pages of a book from biblioteka.poreklo.rs, as lines of text.

The library (ResCarta) keeps an OCR text layer for every page and serves it word by word with its box
(RcWebTextData: x1, y1 at the bottom left of the word... y grows upward, in the scan's pixels). Only the
pages of a book that hold its soldier list are kept, in data-extraction/poreklo/<book>.json:
{"id": <the library's document id>, "title": ..., "pages": {<scan page>: [[text, x1, y1, x2, y2, point size], ...]}}.
They were fetched through a member's login (the library is for poreklo.rs members), so the parsers read
these files and never the library.

A book's records link to the page in the library's viewer (VIEWER_URL), which opens for members only.
"""
import json
import re
from collections import Counter
from pathlib import Path
from statistics import median

HERE = Path(__file__).parent / 'poreklo'
VIEWER_URL = 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id={id}&pg_seq={page}'


class Word:
    __slots__ = ('text', 'x0', 'x1', 'top', 'bottom', 'size')

    def __init__(self, raw):
        text, x1, y1, x2, y2, size = raw
        self.text = text
        self.x0, self.x1 = min(x1, x2), max(x1, x2)
        # y grows upward in the library's boxes; top/bottom here grow downward, as in pdfplumber
        self.top, self.bottom = -max(y1, y2), -min(y1, y2)
        self.size = size

    @property
    def middle(self):
        return (self.top + self.bottom) / 2

    @property
    def height(self):
        return self.bottom - self.top


class Line:
    def __init__(self, words):
        self.words = sorted(words, key=lambda w: w.x0)
        self.text = ' '.join(w.text for w in self.words)
        self.x0 = self.words[0].x0
        self.x1 = max(w.x1 for w in self.words)
        self.top = min(w.top for w in self.words)
        self.bottom = max(w.bottom for w in self.words)

    def __repr__(self):
        return f'<{self.x0:.0f} {self.top:.0f} {self.text[:60]!r}>'


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def viewer_url(book: dict, page: int) -> str:
    return VIEWER_URL.format(id=book['id'], page=page)


def printed_page(book: dict, page: int) -> int | None:
    """The book's page number of a scan page: from the numbers printed alone on a line at the foot or head of the
    pages kept, as the offset most of them agree on"""
    if '_offset' not in book:
        offsets = Counter()
        for p in book['pages']:
            lines = lines_of(page_words(book, int(p)))
            for line in lines[-2:] + lines[:1]:
                if re.fullmatch(r'\d{1,4}', line.text.strip()):
                    offsets[int(p) - int(line.text.strip())] += 1
        book['_offset'] = offsets.most_common(1)[0][0] if offsets else None
    return None if book['_offset'] is None else page - book['_offset']


def lines_of(words: list[Word]) -> list[Line]:
    """Words into lines: a word joins the line whose middle is within half a word's height of its own"""
    if not words:
        return []
    h = median(w.height for w in words) or 1
    lines: list[list[Word]] = []
    for w in sorted(words, key=lambda w: w.middle):
        if lines and abs(median(x.middle for x in lines[-1]) - w.middle) < 0.5 * h:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [Line(ws) for ws in lines]


def page_words(book: dict, page: int) -> list[Word]:
    return [Word(r) for r in book['pages'].get(str(page), []) if r[0].strip()]


def page_lines(book: dict, page: int, columns: int = 1) -> list[list[Line]]:
    """The page's lines, per column; with two columns the page is split at the widest gap in the middle"""
    words = page_words(book, page)
    if columns == 1 or not words:
        return [lines_of(words)]
    left, right = min(w.x0 for w in words), max(w.x1 for w in words)
    lo, hi = left + (right - left) * 0.35, left + (right - left) * 0.65
    # the x in the middle third that the fewest words cross
    best, split = None, (left + right) / 2
    for x in range(int(lo), int(hi), 5):
        n = sum(1 for w in words if w.x0 < x < w.x1)
        if best is None or n < best:
            best, split = n, x
    return [lines_of([w for w in words if w.x1 <= split or (w.x0 + w.x1) / 2 < split]),
            lines_of([w for w in words if not (w.x1 <= split or (w.x0 + w.x1) / 2 < split)])]


def dump(name: str, columns: int = 1) -> str:
    book = load(name)
    out = []
    for page in sorted(map(int, book['pages'])):
        for c, col in enumerate(page_lines(book, page, columns)):
            out.append(f'=== page {page}' + (f' column {c + 1}' if columns > 1 else ''))
            out += [f'{l.x0:6.0f} {l.text}' for l in col]
    return '\n'.join(out)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(dump(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1))
