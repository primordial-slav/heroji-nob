"""
A small local page for answering the doubtful pairs scripts/find_identities.py found: the two entries side by side,
each with the scan of its book page cut around it, and three buttons (same man / different men / not sure). Every
answer is written at once to identity_decisions.json; find_identities.py --write turns them into corrections.

Usage:
    python scripts/find_identities.py              # first: find the pairs (writes the queue)
    python scripts/review_identities.py            # then open http://localhost:8765
    python scripts/review_identities.py --port 8766 --by Boris
Keys: S same, D different, U not sure, arrows or J/K to move, Z to take an answer back.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'data-extraction'))
import find_identities as FI  # noqa: E402

PDFS = ROOT / 'website' / 'public' / 'pdfs'
CROPS = FI.CACHE / 'crops'
PAGE = Path(__file__).with_name('review_identities.html')
SCALE = 2.2                     # pixels per PDF point in the crops
RENDER = threading.Lock()       # pdfium is not thread-safe
_open: dict[str, object] = {}


def pdf(name: str):
    import pdfplumber
    if name not in _open:
        if len(_open) > 6:
            _open.pop(next(iter(_open))).close()
        _open[name] = pdfplumber.open(PDFS / name)
    return _open[name]


def crop(name: str, page_no: int, box: list[float], rects: list | None) -> bytes:
    """The page cut around the entry: its column's width, some lines above and below, the entry tinted."""
    from PIL import Image, ImageDraw
    from pdf_coords import viewer_offset
    tag = re.sub(r'[^\w.-]', '_', f"{name}-{page_no}-{'-'.join(f'{v:g}' for v in box)}-{len(rects or [])}")
    cached = CROPS / f'{tag}.png'
    if cached.exists():
        return cached.read_bytes()
    with RENDER:
        page = pdf(name).pages[page_no - 1]
        ox, oy = viewer_offset(page)
        im = page.to_image(resolution=int(72 * SCALE)).original.convert('RGB')

        def px(x, y):
            return (x + ox - page.bbox[0]) * SCALE, (y + oy - page.bbox[1]) * SCALE
        x0, y0, x1, y1 = box
        rs = rects or [box]
        left = min([x0] + [r[0] for r in rs]) - 30
        right = max([x1] + [r[2] for r in rs]) + 30
        if right - left < 330:
            right = left + 330
        top = min([y0] + [r[1] for r in rs]) - 55
        bottom = max([y1] + [r[3] for r in rs]) + 55
        overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        for r in rs:
            (a, b), (c, e) = px(r[0] - 2, r[1] - 2), px(r[2] + 2, r[3] + 2)
            d.rectangle((a, b, c, e), fill=(255, 196, 0, 70), outline=(214, 40, 40, 255), width=3)
        im = Image.alpha_composite(im.convert('RGBA'), overlay).convert('RGB')
        (a, b), (c, e) = px(left, top), px(right, bottom)
        out = im.crop((max(0, int(a)), max(0, int(b)), min(im.width, int(c)), min(im.height, int(e))))
    buf = io.BytesIO()
    out.save(buf, 'PNG', optimize=True)
    CROPS.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(buf.getvalue())
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    by = 'Boris'

    def log_message(self, *args):
        pass

    def send(self, body: bytes, kind: str, code: int = 200):
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store' if kind.startswith(('application/json', 'text/html')) else 'max-age=86400')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        try:
            if url.path == '/':
                return self.send(PAGE.read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/api/queue':
                if not FI.QUEUE.exists():
                    return self.send(b'{"error": "no queue: run scripts/find_identities.py first"}', 'application/json')
                queue = json.loads(FI.QUEUE.read_text(encoding='utf-8'))
                # another's 'not sure' is no answer here: those pairs wait in the 'Not sure' tab for this reviewer
                queue['answers'] = {k: d['answer'] for k, d in FI.load_decisions().items()
                                    if not (d['answer'] == 'unsure' and d.get('by') != self.by)}
                queue.setdefault('unsure', [])
                queue['by'] = self.by
                return self.send(json.dumps(queue, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
            if url.path == '/crop':
                box = [float(v) for v in q['box'][0].split(',')]
                rects = json.loads(q['rects'][0]) if q.get('rects') else None
                return self.send(crop(q['file'][0], int(q['page'][0]), box, rects), 'image/png')
            if url.path.startswith('/pdfs/'):
                name = urllib.parse.unquote(url.path[len('/pdfs/'):])
                path = (PDFS / name).resolve()
                if path.parent != PDFS.resolve() or not path.exists():
                    return self.send(b'not found', 'text/plain', 404)
                return self.send(path.read_bytes(), 'application/pdf')
        except Exception as e:                                              # noqa: BLE001
            return self.send(f'{type(e).__name__}: {e}'.encode('utf-8'), 'text/plain; charset=utf-8', 500)
        self.send(b'not found', 'text/plain', 404)

    def do_POST(self):
        if self.path != '/api/answer':
            return self.send(b'not found', 'text/plain', 404)
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        try:
            d = FI.save_answer(body['key'], body['answer'], body.get('a_name', ''), body.get('b_name', ''),
                               body.get('by') or self.by, body.get('note', ''))
        except (ValueError, KeyError) as e:
            return self.send(json.dumps({'error': str(e)}).encode('utf-8'), 'application/json', 400)
        self.send(json.dumps(d, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--by', default='Boris', help='whose answers these are (kept with each)')
    args = ap.parse_args()
    Handler.by = args.by
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'http://localhost:{args.port}  (answers go to {FI.DECISIONS.name}; Ctrl+C to stop)')
    server.serve_forever()


if __name__ == '__main__':
    main()
