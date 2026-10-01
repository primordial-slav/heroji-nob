"""
Soldiers' own photographs, for the record popup and the memorial card. Only certain matches:

- from the books that print one in the soldier's entry: the portrait in the entry's own cell, beside its first line;
- from the znaci.org gallery (GALLERY): a photo of one person whose caption names the soldier and agrees with our
  record on more than the name (unit, duty, place or date of death, birthplace), each checked by hand.

  Tuzlanski NOP odred (Tuzla 1988): each cell of the list may hold a portrait, left of the stacked name. A page's
  images can hold two portraits stacked in one strip, so each portrait is found on the page itself: in the band
  left of the entry, the run of dark rows and columns around the entry's first lines, between white gaps.
  Portraits the shape test doesn't pass (a cut-off or pale print, ~50) are left out rather than guessed.

Writes website/public/portreti/<soldier id>.jpg (grey, 240 px high) and website/app/data/portrait-index.json
({soldier id: {f: the print, v: the large photo, c: credit, h: source page}}), which website/app/data/portraits.ts reads. Gallery photos are
downloaded once into data-extraction/.cache/znaci_photos/full/.

    python scripts/extract_book_portraits.py [--sheet OUT.jpg]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'website' / 'public'
OUT = PUBLIC / 'portreti'
INDEX = ROOT / 'website' / 'app' / 'data' / 'portrait-index.json'
DPI = 200
S = DPI / 72
HEIGHT = 240          # the print in the record
LARGE = 900           # the photo opened from it, at most (never enlarged)

BOOKS = [
    # unit data file, PDF, credit shown under the name
    ('tuzlanski-odred-soldiers.json', 'tuzlanski-odred.pdf', 'Tuzlanski NOP odred (Tuzla, 1988)'),
]

GALLERY = [
    # soldier, znaci.org photo, head and shoulders in it (fractions of the photo), what the caption and record share
    ('0039000807', 11685, (0.30, 0.02, 0.75, 0.41), 'komesar 2. bataljona 2. proleterske, poginuo u Bijelim Brdima marta 1944'),
    ('0010000433', 11864, (0.05, 0.0, 0.95, 0.876), 'komandir čete 3. krajiške, poginuo kod Vrbovca maja 1945'),
    ('0026000738', 14608, (0.08, 0.0, 0.75, 0.62), 'stolar, rođen 1899. u Virovu, član Sreskog komiteta KPJ'),
    ('0001003638', 13283, (0.32, 0.06, 0.72, 0.42), 'hodža iz Slatine kod Foče, verski referent'),
    ('0002008648', 10342, (0.1, 0.0, 0.9, 0.70), 'komandant bataljona (drugi Milan Tankosić je rođen 1928)'),
    ('0006008279', 12072, (0.30, 0.06, 0.58, 0.66), 'komandant 13. proleterske; rođen 1917. u Srbu'),
    ('0005000433', 12431, (0.1, 0.02, 0.9, 0.715), 'rukovodilac SKOJ-a 3. sandžačke; jedina Desa Bulatović u brigadi'),
    ('0002000133', 11472, (0.25, 0.06, 0.75, 0.49), 'borac 1. ličkog odreda, "Primorac", rodom iz Novigrada kod Zadra'),
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


def save(im: Image.Image, sid: str) -> dict:
    """The print (HEIGHT high) and, where the source is much bigger, the large photo (up to LARGE high)."""
    small = im.resize((round(im.width * HEIGHT / im.height), HEIGHT), Image.LANCZOS)
    small.save(OUT / f'{sid}.jpg', quality=80, optimize=True, progressive=True)
    if im.height < 1.5 * HEIGHT:                         # a book's small print: the print is all there is
        (OUT / f'{sid}-v.jpg').unlink(missing_ok=True)
        return {'f': f'{sid}.jpg'}
    if im.height > LARGE:
        im = im.resize((round(im.width * LARGE / im.height), LARGE), Image.LANCZOS)
    im.save(OUT / f'{sid}-v.jpg', quality=84, optimize=True, progressive=True)
    return {'f': f'{sid}.jpg', 'v': f'{sid}-v.jpg'}


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
            index[s['soldier_id']] = {**save(im, s['soldier_id']), 'c': credit}
            sheet.append((s['full_name'], im))
            n += 1
        print(f'{data_file}: {n} portraits')
    sys.path.insert(0, str(ROOT / 'scripts'))
    import find_unit_photos as F
    for sid, pid, (a, b, c, d), _why in GALLERY:
        path = F.CACHE / 'full' / f'{pid}.jpg'
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(F._get(f'{F.BASE}/images/{pid}.jpg'))
        im = Image.open(path).convert('L')
        w, h = im.size
        im = im.crop((int(a * w), int(b * h), int(c * w), int(d * h)))
        index[sid] = {**save(im, sid), 'c': f'znaci.org, br. {pid}', 'h': f'https://znaci.org/fotografija.php?br={pid}'}
    print(f'gallery: {len(GALLERY)} portraits')
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
