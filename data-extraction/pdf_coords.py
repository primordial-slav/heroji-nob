"""
Map pdfplumber coordinates into the page space the website's PDF viewer draws in.

pdfminer reports positions relative to the page's MediaBox origin, which is
exactly what pdf.js (react-pdf) renders. pdfplumber 0.9 passes those through
unchanged, but pdfplumber >= 0.11 adds the MediaBox origin back (pdfplumber
#1181). The scanned books here often have origins like (-95, -123), so the two
versions disagree by up to ~320pt, and which one you get depends on which
Python runs the script (Python37 has 0.9.0, miniconda has 0.11.8).

Rather than rely on a version boundary, viewer_offset() measures what
pdfplumber added on the given page, so the result is the same on any version.
"""
from __future__ import annotations

from pdfminer.layout import LTChar


def _first_ltchar(objs):
    # Same depth-first order pdfplumber uses to build page.chars
    for o in objs:
        children = getattr(o, '_objs', None)
        if children is not None:
            found = _first_ltchar(children)
            if found is not None:
                return found
        elif isinstance(o, LTChar):
            return o
    return None


def viewer_offset(page) -> tuple[float, float]:
    """(dx, dy) to subtract from pdfplumber x / top to get viewer coordinates.
    (0, 0) on pdfplumber 0.9; the MediaBox origin on >= 0.11."""
    chars = page.chars
    lt = _first_ltchar(page.layout) if chars else None
    if lt is None:
        return 0.0, 0.0
    c = chars[0]
    return c['x0'] - lt.x0, c['top'] - (page.height - lt.y1)


def viewer_words(page, **kwargs) -> list[dict]:
    """page.extract_words(**kwargs) with x0/x1/top/bottom in viewer coordinates."""
    dx, dy = viewer_offset(page)
    words = page.extract_words(**kwargs)
    if dx or dy:
        for w in words:
            w['x0'] -= dx
            w['x1'] -= dx
            w['top'] -= dy
            w['bottom'] -= dy
    return words
