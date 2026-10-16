"""
Parser: Deveta brigada (IX. SNOUB "Kočevska", brigade code 167) — its command, a second list.

Source: Velimir Kraševec-Igor, "Deveta brigada" II (Knjižnica NOV in POS, 1991; znaci.org 00003/2850.pdf, PDF pp.
        179-182, book pp. 401-404, before its roster on the site)  →  website/public/pdfs/deveta-kader.pdf:
        "Poveljniški kader", the brigade's commanders, political commissars, their deputies and chiefs of staff, and
        its battalions' commanders and commissars (the 5., Russian battalion's in March 1944), a name a line with the
        days held, in words:
    Komandanti brigade
    Alojz Bele-Tičko, od 30. aprila do 26. avgusta 1944
A mark after the days ("*", "•") is the footnote "padel tega dne": he fell on the post's last day. The part after
the hyphen is what he was called ("zvani Tičko;", as the roster writes it). A man in several posts is one record with
each. znaci re-typeset the book from its OCR, so the page shows its slips ("J-Iostnik", "Marjanovi<:", "1O ."); the
names are read back from the brigade's roster (`NAMES`). The roster is the unit's first list (IDs from 1); these get
IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_cankarjeva_kader import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/deveta-kader.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_2850.pdf'   # znaci.org 00003/2850.pdf
FIRST_PAGE, LAST_PAGE = 179, 182
TITLE = 'Poveljniški kader Devete brigade'
HEADING = re.compile(r'^(Komandanti?|Politični komisarj?i?|Namestniki|Načelniki)\b')
# the OCR's slips, read back from the brigade's roster
NAMES = {'J-Iostnik': 'Hostnik', 'C~bric': 'Čubrić', 'Anton Cerne': 'Anton Černe', 'Marjanovi<:': 'Marjanović',
         "Marjanovi<':": 'Marjanović', "Popovi<':": 'Popović', 'Ostojic': 'Ostojić', 'Radulovic': 'Radulović',
         'Vujnovic': 'Vujnović', 'Vojnovic': 'Vojnović'}
WHEN = [('1O .', '10.'), (' l. ', ' 1. '), (' so sredine', ' do sredine')]
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def unit_of(duty: str) -> str:
    m = re.search(r'(\d)\. bataljona', duty)
    if 'Ruskega' in duty:
        return '5. (ruski) bataljon'
    return f'{m.group(1)}. bataljon' if m else 'Štab brigade'


def read_posts(pdf_path: str) -> None:
    duty = ''
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for r in rows_of(viewer_words(page)):
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}|POVELJNIŠKI KADER', text) or text.startswith(('• padel', '* padel')):
                    continue
                if HEADING.match(text) and not re.search(r'\bod\b|19\d\d', text):     # "Komandant 5., Ruskega bataljona"
                    duty = text
                    continue
                name, _, when = text.partition(', ')
                fell = bool(re.search(r'[*•]\s*$', when))
                when = re.sub(r'\s*[*•]\s*$', '', when)
                for a, b in WHEN:
                    when = f' {when} '.replace(a, b).strip()
                k = len(name.split())                                         # the name's words, for its box
                POSTS.append({'duty': duty, 'name': name, 'when': when, 'fell': fell, 'page': n, 'words': r[:k]})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        name = p['name']
        for a, b in NAMES.items():
            name = name.replace(a, b)
        given, _, rest = name.partition(' ')
        last, _, nick = rest.partition('-')
        p.update(last=last.strip(), given=given, nick=nick.strip(), unit=unit_of(p['duty']))
        p['text'] = f"{p['duty'][:1].lower()}{p['duty'][1:]}, {p['when']}" + ('; padel tega dne' if p['fell'] else '')
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
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=167, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/deveta-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
