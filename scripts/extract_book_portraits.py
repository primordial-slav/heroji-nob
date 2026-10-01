"""
Soldiers' own photographs from the books that print one in the soldier's entry, for the record popup and the
memorial card. Only certain matches: the portrait printed in the entry's own cell, beside its first line.

  Tuzlanski NOP odred (Tuzla 1988): each cell of the list may hold a portrait, left of the stacked name. A page's
  images can hold two portraits stacked in one strip, so each portrait is found on the page itself: in the band
  left of the entry, the run of dark rows and columns around the entry's first lines, between white gaps.
  Portraits the shape test doesn't pass (a cut-off or pale print, ~50) are left out rather than guessed.

Writes website/public/portreti/<soldier id>.jpg (grey, 240 px high) and website/app/data/portrait-index.json
({soldier id: {f: file, c: credit}}), which website/app/data/portraits.ts reads.

    python scripts/extract_book_portraits.py [--sheet OUT.jpg]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'website' / 'public'
OUT = PUBLIC / 'portreti'
INDEX = ROOT / 'website' / 'app' / 'data' / 'portrait-index.json'
DPI = 200
S = DPI / 72
HEIGHT = 240

BOOKS = [
    # unit data file, PDF, credit shown under the name
    ('tuzlanski-odred-soldiers.json', 'tuzlanski-odred.pdf', 'Tuzlanski NOP odred (Tuzla, 1988)'),
]


def portrait_box(pg: fitz.Page, rects: list[fitz.Rect], x: float, y: float) -> list[float] | None:
    """The portrait left of an entry whose first line starts at (x, y), or None."""
    band = fitz.Rect(x - 100, y - 30, x - 2, y + 110)
    hits = [r for r in rects if r.intersects(band) and r.x1 <= x + 2]
    if not hits:
        return None
    clip = fitz.Rect(min(r.x0 for r in hits), band.y0, max(r.x1 for r in hits), band.y1) & band
    pix = pg.get_pixmap(clip=clip, dpi=DPI, colorspace=fitz.csGRAY)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    dark_rows = (a < 225).mean(1) > 0.35
    start = int((y + 25 - clip.y0) * S)                      # inside the photo: a little below the first line
    if not dark_rows[min(start, len(dark_rows) - 1)]:
        near = np.nonzero(dark_rows)[0]
        if not len(near):
            return None
        start = int(near[np.argmin(np.abs(near - start))])
    gap = int(3 * S)
    top = start
    while top > 0 and dark_rows[max(0, top - gap):top].any():
        top -= 1
    bot = start
    while bot < len(dark_rows) - 1 and dark_rows[bot + 1:bot + 1 + gap].any():
        bot += 1
    cols = np.nonzero((a[top:bot + 1] < 225).mean(0) > 0.35)[0]
    if not len(cols):
        return None
    left, right = int(cols.min()), int(cols.max())
    h, w = (bot - top) / S, (right - left) / S
    if h < 60 or not 0.55 < w / h < 1.0:                      # cut off, or two prints run together
        return None
    return [clip.x0 + left / S, clip.y0 + top / S, clip.x0 + right / S, clip.y0 + bot / S]


def main():
    OUT.mkdir(exist_ok=True)
    index, sheet = {}, []
    for data_file, pdf, credit in BOOKS:
        soldiers = json.loads((PUBLIC / data_file).read_text(encoding='utf-8'))
        doc = fitz.open(PUBLIC / 'pdfs' / pdf)
        rects: dict[int, list[fitz.Rect]] = {}
        n = 0
        for s in soldiers:
            if s.get('pdf_file') != pdf or not s.get('pdf_page'):
                continue
            pg = doc[s['pdf_page'] - 1]
            if s['pdf_page'] not in rects:
                rects[s['pdf_page']] = [fitz.Rect(r) for img in pg.get_images(full=True)
                                        for r in pg.get_image_rects(img[0]) if r.width > 30]
            box = portrait_box(pg, rects[s['pdf_page']], s['pdf_x'], s['pdf_y'])
            if not box:
                continue
            pix = pg.get_pixmap(clip=fitz.Rect(box), dpi=DPI, colorspace=fitz.csGRAY)
            im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
            im = im.resize((round(im.width * HEIGHT / im.height), HEIGHT), Image.LANCZOS)
            name = f"{s['soldier_id']}.jpg"
            im.save(OUT / name, quality=80, optimize=True, progressive=True)
            index[s['soldier_id']] = {'f': name, 'c': credit}
            sheet.append((s['full_name'], im))
            n += 1
        print(f'{data_file}: {n} portraits')
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=0, sort_keys=True), encoding='utf-8')
    print(f'{len(index)} portraits → {OUT}')
    if '--sheet' in sys.argv:
        tiles = sheet[:80]
        out = Image.new('L', (10 * 130, 8 * 170), 255)
        for k, (_, im) in enumerate(tiles):
            t = im.copy()
            t.thumbnail((120, 160))
            out.paste(t, ((k % 10) * 130, (k // 10) * 170))
        out.save(sys.argv[sys.argv.index('--sheet') + 1])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
