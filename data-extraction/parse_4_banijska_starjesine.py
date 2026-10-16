"""
Parser: 4. banijska brigada (brigade code 20) — its officers, a second list.

Source: "Četvrta banijska NOU brigada — Zbornik sjećanja" (znaci.org 00001/188, chapter 188_1.pdf, its pp. 52-53, book
        pp. 52-53)  →  website/public/pdfs/4-banijska-starjesine.pdf: the author, "u želji da se sačuva od zaborava
        starješinski kadar naše brigade", names the officers of the brigade staff and of the staffs of its four
        battalions, who led them to the end of the war, run on under each duty, surname first:
    Štab brigade:
    komandanti: Maljković Petar, Zebić Janko, Miočinović Sava i Babić Branko;
A third name is what he was called ("Joka Milan Budo"). A man in several posts is one record with each; his box is
around his name at each post on his first post's page. The roster is the unit's first list (IDs from 1); these get
IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/4-banijska-starjesine.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_188_1.pdf'   # znaci.org 00001/188_1.pdf
FIRST_PAGE, LAST_PAGE = 52, 53
TITLE = 'Starješine štabova 4. banijske brigade'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
START = 'U želji da se sačuva'
WORDS = [('Zivko', 'Živko'), ('Zivković', 'Živković'), ('Stab ', 'Štab ')]
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def stream_of(pdf) -> list[dict]:
    """The list's words in reading order, from the sentence that brings it to the end of the 4. bataljon's."""
    words, on = [], False
    for n, page in enumerate(pdf.pages, 1):
        rows: list = []
        for w in sorted(viewer_words(page), key=lambda w: (w['top'], w['x0'])):
            if rows and abs(w['top'] - rows[-1][0]['top']) <= 3:
                rows[-1].append(w)
            else:
                rows.append([w])
        for r in rows:
            text = ' '.join(w['text'] for w in sorted(r, key=lambda w: w['x0']))
            if text.startswith(START):
                on = True
            if on and not re.fullmatch(r'\d{2}', text):
                for w in sorted(r, key=lambda w: w['x0']):
                    words.append({**w, 'page': n})
            if on and text.startswith('omladinski rukovodioci: Kaurić'):
                return words
    return words


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        ws = stream_of(pdf)
    text = ''
    for w in ws:
        t = w['text']
        text = text[:-1] + t if text.endswith('-') and t[:1].islower() else (text + ' ' + t).strip()   # "Sa-" / "va"
    for a, b in WORDS:
        text = text.replace(a, b)
    text = text[text.index('Štab brigade:'):]
    unit, cursor = '', 0
    for m in re.finditer(rf'(Štab (?:brigade|\d\. bataljona)(?: \([^)]*\))?):|([{L}][{L} ]+):\s*([^;:]+?)(?:;|\.(?=\s*Štab)|\.$|$)', text):
        if m.group(1):
            unit = m.group(1)
            continue
        duty, names = m.group(2).strip(), m.group(3)
        for name in re.split(r',\s*|\s+i\s+', names.strip(' .')):
            parts = name.split()
            if len(parts) < 2:
                continue
            last, given, nick = parts[0], parts[1], ' '.join(parts[2:])
            # the surname's word, the next after the last post's: a name is printed again under another post
            folded = last.replace('Ž', 'Z')
            i = next(i for i in range(cursor, len(ws))
                     if ws[i]['text'].strip(',;.') in (last, folded) or ws[i]['text'].endswith('-') and last.startswith(ws[i]['text'][:-1]))
            cursor = i + 1
            POSTS.append({'unit': unit, 'duty': duty, 'last': last, 'given': given, 'nick': nick, 'first': ws[i]})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        p['page'] = p['first']['page']
        p['text'] = f"{p['unit']}, {p['duty']}"
    return [{'text': '§§post' + str(i), 'x': round(p['first']['x0'], 1), 'y': round(p['first']['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = (p['last'], p['given'])
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit'] if p['unit'] == 'Štab brigade' else p['unit'][5:].split(' (')[0].replace('bataljona', 'bataljon')
            out.append(s)
        man['_posts'].append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        f = p['first']
        if f['page'] == man['pdf_page']:
            man['_rects'].append([round(f['x0'], 1), round(f['top'], 1), round(f['x1'], 1), round(f['bottom'], 1)])
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}: {'; '.join(s['_posts'])}."])
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
    run_parser(pdf_path=PDF, brigade_code=20, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/4-banijska-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
