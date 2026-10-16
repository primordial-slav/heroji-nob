"""
Parser: 1. slovenska artilerijska brigada (brigade code 71) — "Seznam starešin", a second list in the same PDF.

Source: Borivoj Lah-Boris, "Prva slovenska artilerijska brigada" (znaci.org 00003/826.pdf, PDF pp. 389-392, book pp.
        388-391)  →  website/public/pdfs/1-slovenska-artilerijska.pdf, its pages 1-4, before the gunners' roster (the
        unit's first list, from page 5): the commanders, political commissars and their deputies, and the chiefs of
        staff of the artillery of the XV. divizija, of the brigade, of its three divizioni and of its protection
        battalion, a name a line under each staff and duty, surname first, with the days held:
    STAB I. SLOVENSKE ARTILERIJSKE BRIGADE
    Komandanti:
    Mišič Miha 6. 5. 1944—28. 3. 1945
A name after a hyphen is what he was called ("Hržič Ivan-Dušan", as the roster writes it). A man in several posts is
one record with each. These get IDs from 10001.
"""
import re
import sys

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/1-slovenska-artilerijska.pdf'
FIRST_PAGE, LAST_PAGE = 1, 4
TITLE = 'Seznam starešin 1. slovenske artilerijske brigade'
UNITS = {'STAB ARTILERIJE XV. DIVIZIJE': 'Artilerija XV. divizije', 'STAB I. SLOVENSKE ARTILERIJSKE BRIGADE': 'Štab brigade',
         'STAB 1. DIVIZIONA': '1. divizion', 'STAB 2. DIVIZIONA': '2. divizion', 'STAB 3. DIVIZIONA': '3. divizion',
         'STAB ZAŠČITNEGA BATALJONA': 'Zaščitni bataljon'}
NAMES = {'Dolič Emil': 'Dolčič Emil', 'Sava Konvalinka': 'Konvalinka Sava'}   # the one line that drops the č; given name first
POSTS: list = []


def rows_of(words: list[dict]) -> list[list[dict]]:
    rows: list = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if rows and w['top'] - rows[-1][-1]['top'] <= 3:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def dates_of(text: str) -> tuple[str, str]:
    """'15. 9. 194,3— 3. 1. 1944' -> ('15. 9. 1943', '3. 1. 1944'); '15.1 0. 1943' is 15. 10. 1943."""
    text = re.sub(r'(19\d)[.,](\d)\b', r'\1\2', text)
    text = re.sub(r'(\d) (\d)\.', r'\1\2.', text)
    n = re.findall(r'\d+', text)
    return '. '.join(n[0:3]), '. '.join(n[3:6])


def read_posts(pdf_path: str) -> None:
    unit = heading = duty = ''
    with pdfplumber.open(pdf_path) as pdf:
        for p in range(FIRST_PAGE, LAST_PAGE + 1):
            for r in rows_of(viewer_words(pdf.pages[p - 1])):
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}|SEZNAM STAREŠIN', text):
                    continue
                if text in UNITS:
                    heading = 'Š' + text[1:].lower().replace(' xv. ', ' XV. ').replace(' i. ', ' I. ')
                    unit = UNITS[text]
                    continue
                if text.rstrip().endswith(':'):
                    duty = text.rstrip(' :').replace('polit,', 'polit.')
                    duty = duty[:1].lower() + duty[1:]
                    continue
                m = re.search(r'\s\d', text)
                name = text[:m.start()].strip()
                name = NAMES.get(name, name)
                frm, to = dates_of(text[m.start():])
                words = [w for w in r if not re.match(r"['\d]", w['text'])]
                POSTS.append({'unit': unit, 'text': f'{heading}, {duty}, od {frm} do {to}', 'name': name, 'page': p,
                              'words': words})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        last, _, rest = p['name'].partition(' ')
        given, _, nick = rest.partition('-')
        p.update(last=last, given=given.strip(), nick=nick.strip())
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
        p = POSTS[s['_post']]
        key = (p['last'], p['given'])
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = p['unit']
            out.append(s)
        man['_posts'].append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
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
    run_parser(pdf_path=PDF, brigade_code=71, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/1-slovenska-artilerijska-soldiers.json',
               start_page=FIRST_PAGE, end_page=LAST_PAGE, extract_fn=extract, entry_start_re=re.compile(r'^§§'),
               parse_entry_fn=parse, post_fn=men, id_start=10001, keep_other_sources=True)
