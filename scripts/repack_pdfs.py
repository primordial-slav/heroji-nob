"""
Repack the site's PDFs so the viewer can show a page without reading most of the book.

The viewer (PDF.js, website/app/components/PdfViewer.tsx) loads a book by range requests in 64 KB pieces, but to
open it, it reads the page tree and every page object. In a scan as printed by most tools those small objects lie
between the page images, all through the file, so opening a book read 60-100% of it (Prva lička: 11 of 18 MB).
Saved with object streams (PyMuPDF, as in commit 36d1331) they sit together and opening reads a few per cent.

A file is replaced only if every object the new file keeps is the same as in the old one (its definition, and its
stream's raw bytes), the pages' boxes and rotation are the same, and it opens with less. So the page images, the
text layer and its coordinates (pdf_x/pdf_y, the entry boxes) are untouched. MuPDF writes each /Length directly
and drops the length objects; that is the only difference allowed.

After adding a book's PDF to website/public/pdfs:
    python scripts/repack_pdfs.py                     # every PDF that opens with more than 30% (and 150 KB)
    python scripts/repack_pdfs.py 51-divizija.pdf     # only these
    python scripts/repack_pdfs.py --dry-run           # what each PDF reads to open, nothing written
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import fitz
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
PDFS = ROOT / 'website' / 'public' / 'pdfs'
CHUNK = 65536  # PDF.js's rangeChunkSize
WORTH_IT = 0.3  # repack a file that reads more than this share of itself to open ...
MIN_READ = 150_000  # ... and more than this many bytes
LENGTH_REF = re.compile(r'/Length (\d+) 0 R')


def open_cost(path):
    """Bytes the viewer reads to open the file: the 64 KB pieces holding the cross-reference data, the trailer,
    the catalog, the page tree and every page object."""
    size = os.path.getsize(path)
    r = PdfReader(path)
    chunks = set(range(max(0, (size - 1024) // CHUNK), (size - 1) // CHUNK + 1))

    def span(start, length):
        chunks.update(range(start // CHUNK, (start + max(length, 1) - 1) // CHUNK + 1))

    offsets = {num: off for table in r.xref.values() for num, off in table.items()}
    in_stream = dict(r.xref_objStm)

    def touch(num):
        if num in in_stream:
            stream = in_stream[num][0]
            span(offsets.get(stream, 0), int(r.get_object(stream).get('/Length', 0)) + 200)
        elif num in offsets:
            span(offsets[num], 512)

    startxref = getattr(r, '_startxref', None)
    if startxref is not None:
        span(startxref, 20 * len(offsets) + 200)
    touch(r.trailer.raw_get('/Root').idnum)
    seen = set()

    def walk(ref):
        if ref.idnum in seen:
            return
        seen.add(ref.idnum)
        touch(ref.idnum)
        for kid in ref.get_object().get('/Kids', []) or []:
            walk(kid)

    walk(r.trailer['/Root'].raw_get('/Pages'))
    return sum(min(CHUNK, size - c * CHUNK) for c in chunks)


def differences(old_path, new_path):
    """None if the new file keeps every object of the old one as it was, else what differs."""
    a, b = fitz.open(old_path), fitz.open(new_path)
    try:
        if a.page_count != b.page_count:
            return f'page count {a.page_count} != {b.page_count}'
        for i in range(a.page_count):
            pa, pb = a[i], b[i]
            if (pa.mediabox, pa.cropbox, pa.rotation, pa.xref) != (pb.mediabox, pb.cropbox, pb.rotation, pb.xref):
                return f'page {i + 1}: boxes, rotation or object number differ'

        def old_definition(x):
            text = a.xref_object(x, compressed=True)
            return LENGTH_REF.sub(lambda m: '/Length ' + a.xref_object(int(m.group(1)), compressed=True).strip(), text)

        kept = {}
        for x in range(1, b.xref_length()):
            if b.xref_get_key(x, 'Type')[1] in ('/ObjStm', '/XRef'):
                continue
            new = b.xref_object(x, compressed=True)
            if new.strip() != 'null':
                kept[x] = new
        # an object the new file dropped must be one nothing it keeps (or the trailer) refers to
        references = ' '.join(kept.values()) + ' ' + b.xref_object(-1, compressed=True)
        for x in range(1, min(a.xref_length(), b.xref_length())):
            if x not in kept and a.xref_object(x, compressed=True).strip() != 'null' \
                    and re.search(rf'(?<!\d){x} 0 R', references):
                return f'object {x} dropped but still referred to'
        for x, new in kept.items():
            if x >= a.xref_length() or old_definition(x) != new:
                return f'object {x} differs'
            if b.xref_is_stream(x) and a.xref_stream_raw(x) != b.xref_stream_raw(x):
                return f'stream {x} differs'
        return None
    finally:
        a.close()
        b.close()


def repack(path):
    """Repack one file in place; returns (bytes read to open before, after) or the reason it was left as it is."""
    tmp = path.with_name(path.name + '.repack.tmp')
    # deflate also compresses the new object stream; if it compresses anything else (an uncompressed page), the
    # check rejects it and the file is saved again without it
    for options in (dict(use_objstms=1, garbage=1, deflate=True), dict(use_objstms=1, garbage=1)):
        doc = fitz.open(path)
        doc.save(tmp, **options)
        doc.close()
        problem = differences(path, tmp)
        if not problem:
            break
    before, after = open_cost(path), open_cost(tmp)
    if problem or after >= before:
        tmp.unlink()
        return problem or 'opens no cheaper'
    for _ in range(10):
        try:
            os.replace(tmp, path)
            return before, after
        except PermissionError:  # open in the dev server or another process for a moment
            time.sleep(3)
    tmp.unlink()
    return 'file in use'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', nargs='*', help='PDF names in website/public/pdfs (default: all that need it)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    paths = [PDFS / f for f in args.files] if args.files else sorted(PDFS.glob('*.pdf'))
    total_before = total_after = 0
    for path in paths:
        size, read = os.path.getsize(path), open_cost(path)
        if not args.files and (read <= WORTH_IT * size or read <= MIN_READ):
            continue
        if args.dry_run:
            print(f'{path.name:44s} {size / 1e6:6.2f} MB, opens with {read / 1e6:5.2f} MB ({100 * read / size:.0f}%)')
            continue
        result = repack(path)
        if isinstance(result, str):
            print(f'left   {path.name}: {result}', flush=True)
            continue
        total_before += result[0]
        total_after += result[1]
        print(f'packed {path.name:44s} opens with {result[0] / 1e6:5.2f} -> {result[1] / 1e6:5.2f} MB', flush=True)
    if total_before:
        print(f'Read to open the repacked files: {total_before / 1e6:.1f} MB -> {total_after / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
