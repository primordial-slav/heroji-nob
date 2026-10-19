"""
OCR a scanned book's pages that have no text layer, and keep the words with their boxes, so a parser reads the
saved result and never runs the OCR itself.

The engine is Tesseract 5 with the tessdata_best models (srp for Cyrillic, hrv or srp_latn for Latin, slv), run
locally; no page leaves the machine. Its place is set by the environment: TESSERACT (the executable, default
E:\\envs\\ocr\\Library\\bin\\tesseract.exe, a conda env: `conda create -p E:\\envs\\ocr -c conda-forge tesseract`)
and TESSDATA_PREFIX (default E:\\envs\\ocr\\tessdata_best, the models from github.com/tesseract-ocr/tessdata_best).

Each page of the site's PDF is rendered at --dpi, split into its columns where asked (--columns N: the N-1 widest
white bands down the page's middle; or --split 0.5,... as fractions of the width), and each column read as one block
of lines (--psm 6, which keeps a table's row together). The words are written in the page space the site's viewer
draws in (points, the top left corner the origin), with Tesseract's line and its confidence:

    data-extraction/ocr/<pdf name without .pdf>.json
    {"pdf": ..., "engine": "tesseract 5.5.3", "lang": "srp", "dpi": 300, "psm": 6,
     "pages": {"1": {"width": 357.0, "height": 498.2,
                     "lines": [{"col": 0, "x0": .., "top": .., "x1": .., "bottom": ..,
                                "words": [[x0, top, x1, bottom, "text", conf], ...]}, ...]}}}

Usage:
    python data-extraction/ocr_scan.py niksicki-odred-pali-borci.pdf --lang srp
    python data-extraction/ocr_scan.py lovcenski-odred-pali-borci.pdf --lang srp --columns 2 --pages 3-5
    (--pages re-reads those pages and keeps the others already saved)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
PDF_DIR = HERE.parent / 'website' / 'public' / 'pdfs'
OUT_DIR = HERE / 'ocr'
TESSERACT = os.environ.get('TESSERACT', r'E:\envs\ocr\Library\bin\tesseract.exe')
TESSDATA = os.environ.get('TESSDATA_PREFIX', r'E:\envs\ocr\tessdata_best')


def tesseract_version() -> str:
    out = subprocess.run([TESSERACT, '--version'], capture_output=True, text=True)
    return (out.stdout or out.stderr).split('\n')[0].strip()


def gutters(img: np.ndarray, n: int) -> list[int]:
    """The n widest bands of white columns in the middle of the page (between 20% and 80% of its width), each band's
    middle: where a page of n+1 columns divides."""
    h, w = img.shape
    ink = (img < 128)[int(h * 0.08):int(h * 0.94)].sum(axis=0)     # running heads and page numbers left out
    white = ink <= max(1, int(0.002 * h))
    bands, start = [], None
    for x in range(int(w * 0.2), int(w * 0.8)):
        if white[x] and start is None:
            start = x
        elif not white[x] and start is not None:
            bands.append((x - start, start, x))
            start = None
    if not bands:
        return []
    # of the wide bands (half the widest or more), those nearest to where the page's ink divides evenly: a table's
    # own white band (its names after a column of dittos) can be wider than the gutter between two tables
    cols = np.nonzero(ink > max(1, int(0.002 * h)))[0]
    left, right = (cols[0], cols[-1]) if len(cols) else (0, w)
    widest = max(b[0] for b in bands)
    wide = [b for b in bands if b[0] >= 0.5 * widest]
    marks = [left + (right - left) * k / (n + 1) for k in range(1, n + 1)]
    chosen = []
    for m in marks:
        b = min((x for x in wide if x not in chosen), key=lambda x: abs((x[1] + x[2]) / 2 - m), default=None)
        if b:
            chosen.append(b)
    return sorted((a + b) // 2 for _, a, b in chosen)


def read_image(img: Image.Image, lang: str, psm: int) -> list[dict]:
    """Tesseract's words of one image, grouped into its lines: [{words: [[x0, top, x1, bottom, text, conf]]}] in pixels."""
    env = dict(os.environ, TESSDATA_PREFIX=TESSDATA, OMP_THREAD_LIMIT='1')
    tmp = OUT_DIR / f'.tmp_{os.getpid()}_{id(img)}.png'
    img.save(tmp)
    try:
        out = subprocess.run([TESSERACT, str(tmp), 'stdout', '-l', lang, '--psm', str(psm),
                              '-c', 'preserve_interword_spaces=1', 'tsv'],
                             capture_output=True, env=env)
    finally:
        tmp.unlink(missing_ok=True)
    rows = out.stdout.decode('utf-8', errors='replace').splitlines()
    if not rows:
        raise RuntimeError(out.stderr.decode('utf-8', errors='replace'))
    head = rows[0].split('\t')
    lines: dict[tuple, list] = {}
    for row in rows[1:]:
        f = dict(zip(head, row.split('\t')))
        if f.get('level') != '5' or not f.get('text', '').strip():
            continue
        x, y, w, h = (int(f[k]) for k in ('left', 'top', 'width', 'height'))
        key = (int(f['block_num']), int(f['par_num']), int(f['line_num']))
        lines.setdefault(key, []).append([x, y, x + w, y + h, f['text'], round(float(f['conf']))])
    return [{'words': ws} for _, ws in sorted(lines.items())]


def retry_words(page: fitz.Page, lines: list[dict], args) -> int:
    """Read again, one by one at a higher resolution, the words Tesseract was unsure of (conf below --retry): blurred
    or doubled print gives it "дДОоКкнНИЋ" for ДОКНИЋ in a line, which alone it reads right. The better reading wins;
    the first one is kept as the word's seventh item."""
    weak = [w for ln in lines for w in ln['words'] if w[5] < args.retry]
    if not weak:
        return 0
    zoom = args.retry_dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    img = Image.frombytes('L', (pix.width, pix.height), pix.samples)
    changed = 0
    for w in weak:
        box = (max(0, int((w[0] - 2) * zoom)), max(0, int((w[1] - 2) * zoom)),
               min(pix.width, int((w[2] + 2) * zoom)), min(pix.height, int((w[3] + 2) * zoom)))
        crop = img.crop(box)
        pad = Image.new('L', (crop.width + 40, crop.height + 40), 255)      # a white margin round the word
        pad.paste(crop, (20, 20))
        best = None
        for psm in (8, 7):
            got = read_image(pad, args.lang, psm)
            words = [x for ln in got for x in ln['words']]
            if words:
                text = ' '.join(x[4] for x in words)
                conf = min(x[5] for x in words)
                if best is None or conf > best[1]:
                    best = (text, conf)
        if best and best[1] > w[5] + 5 and ' ' not in best[0]:
            w.append(w[4])
            w[4], w[5] = best
            changed += 1
    return changed


def read_page(doc: fitz.Document, pno: int, args) -> dict:
    page = doc[pno - 1]
    zoom = args.dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    img = Image.frombytes('L', (pix.width, pix.height), pix.samples)
    arr = np.asarray(img)
    if args.split:
        cuts = [int(float(f) * pix.width) for f in args.split.split(',')]
    elif args.columns > 1:
        cuts = gutters(arr, args.columns - 1)
    else:
        cuts = []
    edges = [0, *cuts, pix.width]
    lines = []
    for col, (a, b) in enumerate(zip(edges, edges[1:])):
        for ln in read_image(img.crop((a, 0, b, pix.height)), args.lang, args.psm):
            words = [[round((w[0] + a) / zoom, 1), round(w[1] / zoom, 1), round((w[2] + a) / zoom, 1),
                      round(w[3] / zoom, 1), w[4], w[5]] for w in ln['words']]
            lines.append({'col': col, 'x0': min(w[0] for w in words), 'top': min(w[1] for w in words),
                          'x1': max(w[2] for w in words), 'bottom': max(w[3] for w in words), 'words': words})
    lines.sort(key=lambda ln: (ln['col'], ln['top']))
    retried = retry_words(page, lines, args) if args.retry else 0
    return {'width': round(page.rect.width, 1), 'height': round(page.rect.height, 1),
            'cuts': [round(c / zoom, 1) for c in cuts], 'retried': retried, 'lines': lines}


def parse_pages(spec: str | None, count: int) -> list[int]:
    if not spec:
        return list(range(1, count + 1))
    out = []
    for part in spec.split(','):
        a, _, b = part.partition('-')
        out += list(range(int(a), int(b or a) + 1))
    return out


def load(pdf_name: str) -> dict:
    """The saved OCR of a site PDF (for parsers)."""
    return json.loads((OUT_DIR / (Path(pdf_name).stem + '.json')).read_text(encoding='utf-8'))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf', help="the site's PDF, in website/public/pdfs/")
    ap.add_argument('--lang', default='srp')
    ap.add_argument('--psm', type=int, default=6)
    ap.add_argument('--dpi', type=int, default=300)
    ap.add_argument('--columns', type=int, default=1)
    ap.add_argument('--split', help='column cuts as fractions of the width, e.g. 0.5')
    ap.add_argument('--pages', help='e.g. 1-5,9 (default: every page)')
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--retry', type=int, default=70, help='read words below this confidence again, alone (0: never)')
    ap.add_argument('--retry-dpi', type=int, default=450)
    args = ap.parse_args()
    doc_path = PDF_DIR / args.pdf
    doc = fitz.open(doc_path)
    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / (doc_path.stem + '.json')
    data = json.loads(out_path.read_text(encoding='utf-8')) if out_path.exists() and args.pages else {'pages': {}}
    data.update(pdf=args.pdf, engine=tesseract_version(), lang=args.lang, dpi=args.dpi, psm=args.psm,
                retry=args.retry, retry_dpi=args.retry_dpi)
    pages = parse_pages(args.pages, doc.page_count)

    def one(pno):
        return pno, read_page(fitz.open(doc_path), pno, args)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for pno, res in pool.map(one, pages):
            data['pages'][str(pno)] = res
            print(f"  page {pno}: {len(res['lines'])} lines, cuts {res['cuts']}, {res['retried']} words read again")
    data['pages'] = dict(sorted(data['pages'].items(), key=lambda kv: int(kv[0])))
    out_path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('Written', out_path, f'({out_path.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
