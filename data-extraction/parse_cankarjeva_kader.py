"""
Parser: Cankarjeva brigada (brigade code 61) — its command, a second list.

Source: Lado Ambrožič-Novljan, "Cankarjeva brigada" (Knjižnica NOV in POS, 1975; znaci.org 00003/767.pdf, PDF pp.
        812-816, book pp. 810-814, before its roster on the site)  →  website/public/pdfs/cankarjeva-kader.pdf:
        "Poveljniški kader", the brigade's commanders, political commissars, their deputies and chiefs of staff, and
        each battalion's commanders and commissars, a name a line with the days held:
    Komandanti brigade
    Predrag Jevtič-Dragan          od 28. 12. 1942 do 13. 7. 1943
A name too long for its line runs on to the next ("Jože Borštnar-Tone" / "Gabrovčan od ..."); the part after the
hyphen is what he was called ("zvani Tone Gabrovčan;", as the roster writes it). A man in several posts is one record
with each. znaci re-typeset the book from its OCR, so the page shows its slips ("Hija Badovinac", "Bemot-2ivko",
"12.1 942"); the names are read back from the brigade's roster (`NAMES`). The roster and the fallen are the unit's
first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/cankarjeva-kader.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_767.pdf'   # znaci.org 00003/767.pdf
FIRST_PAGE, LAST_PAGE = 812, 816
TITLE = 'Poveljniški kader Cankarjeve brigade'
HEADING = re.compile(r'^\*?\s*(Komandant|Komandanti|Politični komisarji|Politična komisarja|Namestniki|Načelniki)\b')
# the OCR's slips, read back from the brigade's roster (and the line that prints the name right)
NAMES = {'Borštn ar': 'Borštnar', 'BorStnar': 'Borštnar', 'Marj anovič': 'Marjanovič', 'Piceij': 'Picelj',
         'Picélj': 'Picelj', 'Moj škerc': 'Mojškerc', 'JerK-Drugi': 'Jerič-Drugi', 'Seveir': 'Sever',
         'Dolčdč': 'Dolčič', 'Bemot-2ivko': 'Bernot-Živko', 'Miiič-Maifco': 'Milič-Marko', 'Hija ': 'Ilija ',
         'MiSica': 'Mišica', 'Stefan ': 'Štefan ', 'Lovno ': 'Lovro ', 'Viljemi ': 'Viljem ', '2okalj': 'Žokalj',
         'Tončka Sobar': 'Tončka Šobar', 'Koc j ančič': 'Kocjančič', 'Dur j ava': 'Durjava', 'Ilij a': 'Ilija',
         'Štehlaj': 'Šteblaj'}
DATES = {('Pelko', 'Florjan'): ('15. 12. 1944', '15. 12. 1942')}   # "do 15. 12. 1944", the next from 16. 12. 1942
TITLES = {'Dr.': 'dr.', 'Ing.': 'ing.'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def rows_of(words: list[dict]) -> list[list[dict]]:
    """Lines by the words' tops, chained: a day set a little high ("6" at 235 in a line at 238) stays in its line."""
    rows: list = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if rows and w['top'] - rows[-1][-1]['top'] <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def dates_of(text: str) -> tuple[str, str]:
    """'od 28. 9. 1942 do 27. 12.1 942' -> ('28. 9. 1942', '27. 12. 1942')."""
    text = re.sub(r'(\d) (\d{3})\b', r'\1\2', text.replace('od L ', 'od 1. '))
    halves = re.split(r'\bdo\b', text, 1)
    out = []
    for h in halves:
        n = re.findall(r'\d+', h)
        out.append('. '.join(n[:2]) + '. ' + n[2] if len(n) >= 3 else ' '.join(n))
    return out[0], out[1] if len(out) > 1 else ''


def read_posts(pdf_path: str) -> None:
    heading, pending = '', []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for r in rows_of(viewer_words(page)):
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}|POVELJNIŠKI KADER', text):
                    continue
                if HEADING.match(text):
                    heading, pending = text.lstrip('* ').replace('HI.', 'III.'), []
                    continue
                m = re.search(r'\bod\b', text)
                if not m:                                                     # a name that runs on to the next line
                    pending.append(r)
                    continue
                od_x = next(w['x0'] for w in r if w['text'] == 'od')
                name_words = [w for w in r if w['x0'] < od_x]
                name = ''
                for p in pending + [name_words]:
                    t = ' '.join(w['text'] for w in p)
                    name = name + t if name.endswith('-') else (name + ' ' + t).strip()
                POSTS.append({'heading': heading, 'name': name, 'dates': dates_of(text[m.start():]), 'page': n,
                              'rows': [p for p in pending + [name_words] if p]})
                pending = []


def name_of(name: str) -> tuple[str, str, str, str]:
    """'Dr. Marjan Dermastia-Urban Velikonja' -> ('Dermastia', 'Marjan', 'Urban Velikonja', 'dr.')."""
    for a, b in NAMES.items():
        name = name.replace(a, b)
    words = name.split()
    title = TITLES.get(words[0], '')
    if title:
        words = words[1:]
    given, rest = words[0], ' '.join(words[1:])
    last, _, nick = rest.partition('-')
    return last.strip(), given, nick.strip(), title


def unit_of(heading: str) -> str:
    m = re.search(r'([IV]+\. bataljona?(?: \(avstrijski\))?)', heading)
    if not m:
        return 'Štab brigade'
    return m.group(1).replace('bataljona', 'bataljon')


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        p['last'], p['given'], p['nick'], p['title'] = name_of(p['name'])
        frm, to = p['dates']
        old, new = DATES.get((p['last'], p['given']), ('', ''))
        to = new if to == old and old else to
        p['text'] = f"{p['heading']}, od {frm} do {to}"
        p['unit'] = unit_of(p['heading'])
    return [{'text': '§§post' + str(i), 'x': round(p['rows'][0][0]['x0'], 1), 'y': round(p['rows'][0][0]['top'], 1),
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
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], p['title']
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_posts'].append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            for row in p['rows']:
                man['_rects'].append([round(min(w['x0'] for w in row), 1), round(min(w['top'] for w in row), 1),
                                      round(max(w['x1'] for w in row), 1), round(max(w['bottom'] for w in row), 1)])
    for s in out:
        s['additional_info'] = '; '.join(([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = f"{s['last_name']} {s['first_name']}"
        for k in ('_post', '_posts', '_nicks', '_rects', '_title'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=61, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/cankarjeva-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
