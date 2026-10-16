"""
Parser: 6. dalmatinska brigada (brigade code 103) — its command, a second list.

Source: Danilo Damjanović, "Šesta dalmatinska udarna brigada", Prilog I, "Spisak komandnog kadra 6. dalmatinske
        udarne brigade" (znaci.org 00001/105_7.pdf, PDF pp. 1-2, book pp. 257-258, just before its fallen on the
        site)  →  website/public/pdfs/6-dalmatinska-kadar.pdf. Two columns; under the brigade staff and each
        battalion's ("Štab 1. bataljona"), a duty with a colon and its holders run on, given name first, a nickname
        in brackets before the surname:
    komandanti:
    Sime Ivas, formirao brigadu, Danilo (Danćić) Damjanović, Dušan Bursać, Radica Repac;
A man in several posts is one record with each; his box is around his name at each post on his first post's page.
The fallen are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/6-dalmatinska-kadar.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_105_7.pdf'   # znaci.org 00001/105_7.pdf
FIRST_PAGE, LAST_PAGE = 1, 2
TITLE = 'Spisak komandnog kadra 6. dalmatinske udarne brigade'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# the text layer's slips, read from the page
WORDS = [('Stab ', 'Štab '), ('Duro ', 'Đuro '), ('Cedomlr', 'Čedomir'), ('Cedomir', 'Čedomir'), ('Luka Jai ić', 'Luka Jaić'),
         ('Kazimir Neki:', 'Kazimir Nekić;'), ('Ante Dukić;* »', 'Ante Dukić;'), ('Milan ćelić', 'Milan Celić'),
         ('Papo Mario', 'Mario Papo'), ('Sime ', 'Šime '), ('(Danćić)', '(Danić)')]
NAME = re.compile(rf'([{U}][{L}]+)(?:\s+\(([{U}][{L}]+)\))?\s+([{U}][{L}]+(?:-[{U}][{L}]+)?)')
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def columns(page) -> list[list[dict]]:
    """The page's two columns, each a list of words in reading order (split at the widest gap)."""
    ws = viewer_words(page)
    occ = set()
    for w in ws:
        occ.update(range(int(w['x0']), int(w['x1']) + 1))
    gaps, start = [], None
    for x in range(int(page.width * 0.3), int(page.width * 0.7)):
        if x not in occ and start is None:
            start = x
        if x in occ and start is not None:
            gaps.append((x - start, (start + x) / 2))
            start = None
    split = max(gaps)[1] if gaps else page.width / 2
    out = []
    for side in (lambda w: w['x0'] < split, lambda w: w['x0'] >= split):
        rows: list = []
        for w in sorted((w for w in ws if side(w)), key=lambda w: (w['top'], w['x0'])):
            row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
            (rows.append([w]) if row is None else row.append(w))
        out.append([w for r in sorted(rows, key=lambda r: r[0]['top']) for w in sorted(r, key=lambda w: w['x0'])])
    return out


def read_posts(pdf_path: str) -> None:
    unit, duty = 'Štab brigade', ''
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for col in columns(page):
                stream = []
                for w in col:
                    w['page'] = n
                    t = w['text']
                    if re.fullmatch(r'-?\d+|Prilog|I|SPISAK|KOMANDNOG|KADRA|6\.|DALMATINSKE|UDARNE|BRIGADE', t):
                        continue
                    if stream and stream[-1]['text'].endswith('-') and t[:1].islower():
                        stream[-1] = {**stream[-1], 'text': stream[-1]['text'][:-1] + t, 'x1': w['x1']}
                        continue
                    stream.append(w)
                text = ' '.join(w['text'] for w in stream)
                for a, b in WORDS:
                    text = text.replace(a, b)
                pos = 0
                if n == 2 and text.startswith('Krićković'):                    # "Iso" / "Krićković" over the page
                    text = 'Iso ' + text
                # a duty starts a word in small letters ("oficiri OZNE:"), never a name ("Ilija Gleda:")
                for m in re.finditer(rf'Štab \d\. bataljona|(?<![{U}{L}])([{L}][{L}]*(?:\s+(?:[{L}]+|[{U}]{{2,}}))*?)\s*:', text):
                    flush(text[pos:m.start()], unit, duty, stream, n)
                    if m.group(0).startswith('Štab'):
                        unit, duty = m.group(0), ''
                    else:
                        duty = m.group(1).strip()
                    pos = m.end()
                flush(text[pos:], unit, duty, stream, n)


def flush(seg: str, unit: str, duty: str, stream: list, page: int) -> None:
    names = list(NAME.finditer(seg))
    for i, m in enumerate(names):
        end = names[i + 1].start() if i + 1 < len(names) else len(seg)
        note = seg[m.end():end].strip(' ,;.i')
        if re.fullmatch(r'i', note):
            note = ''
        words = [w for w in stream if w['text'].strip(',;.()') in (m.group(1), m.group(3).split('-')[0])][:2] or stream[:1]
        POSTS.append({'unit': unit, 'duty': duty, 'given': m.group(1), 'nick': m.group(2) or '', 'last': m.group(3),
                      'note': note if re.match(rf'^[{L}]', note) else '', 'page': page, 'words': words})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        key = (s['last_name'], s['first_name'])
        man = seen.get(key)
        p = POSTS[s['_post']]
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_posts'].append(', '.join(x for x in (p['unit'], p['duty'], p['note']) if x))
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}"])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}"
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=103, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/6-dalmatinska-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
