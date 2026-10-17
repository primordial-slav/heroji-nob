"""The lines the parsers lost after an entry that ends in a word broken at the line's end ("Kamije-" / "vo"): for each
such record, the row after the one its text ends with, in its column on its page (or the next column's or page's
first row), if that row is not another entry's start. Writes a review table (json) of proposals: status 'ok' where
the row starts in lowercase (the syllable to join; check it holds no word in capitals, the next entry in a flush
list), 'check' where it doesn't, 'end row not found' where the text layer lacks the cut line. See CLAUDE.md, "Lost
continuation lines" (the corrections of 2026-10-17 were written from these tables).
Usage: python scripts/find_lost_lines.py website/public/<unit>-soldiers.json <out.json> [--from-git]"""
import json
import re
import subprocess
import sys

sys.path.insert(0, 'data-extraction')
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber  # noqa: E402

from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from parse_2_dalmatinska_stabovi import rows_of  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

CUT = re.compile(r'([A-Za-zČĆŽŠĐčćžšđ]+)-$')
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def fold(s: str) -> str:
    return re.sub(r'[^a-z]', '', cyrillic_to_latin(s).lower().translate(FOLD))


_pages: dict = {}


def rows(pdf_file: str, page: int) -> list[dict]:
    key = (pdf_file, page)
    if key not in _pages:
        with pdfplumber.open(f'website/public/pdfs/{pdf_file}') as pdf:
            if page > len(pdf.pages):
                _pages[key] = []
                return []
            ws = viewer_words(pdf.pages[page - 1])
        out = []
        for r in rows_of(ws):
            out.append({'x0': r[0]['x0'], 'x1': r[-1]['x1'], 'top': min(w['top'] for w in r),
                        'bottom': max(w['bottom'] for w in r), 'words': r,
                        'text': ' '.join(w['text'] for w in r)})
        _pages[key] = out
    return _pages[key]


def column_rows(pdf_file: str, page: int, x_lo: float, x_hi: float) -> list[dict]:
    """The page's rows cut to the words between x_lo and x_hi, in reading order"""
    out = []
    for r in rows(pdf_file, page):
        ws = [w for w in r['words'] if x_lo - 2 <= w['x0'] < x_hi]
        if ws:
            out.append({'x0': ws[0]['x0'], 'top': min(w['top'] for w in ws), 'bottom': max(w['bottom'] for w in ws),
                        'text': ' '.join(w['text'] for w in ws)})
    return sorted(out, key=lambda r: r['top'])


def main():
    unit_file, out_path = sys.argv[1], sys.argv[2]
    if '--from-git' in sys.argv:
        raw = subprocess.run(['git', 'show', f'HEAD:{unit_file}'], capture_output=True, encoding='utf-8').stdout
        recs = json.loads(raw)
    else:
        recs = json.load(open(unit_file, encoding='utf-8'))
    cut = [s for s in recs if CUT.search(s.get('additional_info') or '') and s.get('pdf_file')]
    # each page's columns: the starts of the records on it
    starts: dict = {}
    for s in recs:
        if s.get('pdf_file'):
            starts.setdefault((s['pdf_file'], s['pdf_page']), []).append(s['pdf_x'])
    props = []
    for s in cut:
        info = s['additional_info']
        stem = CUT.search(info).group(1)
        f, p = s['pdf_file'], s['pdf_page']
        x0 = s.get('pdf_x_left', s['pdf_x'])
        xs = sorted(set(round(x) for x in starts[(f, p)]))
        right = [x for x in xs if x > s['pdf_x'] + 60]
        x_hi = (min(right) - 8) if right else 10 ** 4
        col = column_rows(f, p, x0 - 4, x_hi)
        # the row the entry's text ends on: at or below the entry's start, ending with the stem
        at = None
        for i, r in enumerate(col):
            if r['top'] < s['pdf_y'] - 3:
                continue
            if fold(r['text']).endswith(fold(stem)) and r['text'].rstrip().endswith(('-', '—', '–', '\xad')):
                at = i
                break
        prop = {'id': s['soldier_id'], 'name': s['full_name'], 'info': info, 'stem': stem, 'page': p, 'file': f}
        if at is None:
            prop['status'] = 'end row not found'
        else:
            nxt = col[at + 1] if at + 1 < len(col) else None
            where = 'below'
            if nxt is None:
                where = 'next column or page'
                if right:                                                     # the right column's first row
                    nc = column_rows(f, p, min(right) - 4, 10 ** 4)
                    nxt = nc[0] if nc else None
                else:
                    nc = rows(f, p + 1)
                    nxt = min(nc, key=lambda r: (r['x0'] > 150, r['top'])) if nc else None
            prop['where'] = where
            if nxt is None:
                prop['status'] = 'no row after'
            else:
                t = cyrillic_to_latin(nxt['text']).strip()
                prop['next'] = t
                prop['next_x'] = round(nxt['x0'], 1)
                prop['start_x'] = round(s['pdf_x'], 1)
                prop['status'] = 'ok' if t[:1].islower() else 'check'
        props.append(prop)
    json.dump(props, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(recs), 'records,', len(cut), 'cut;', dict(Counter(p['status'] for p in props)),
          dict(Counter(p.get('where') for p in props)))


if __name__ == '__main__':
    main()
