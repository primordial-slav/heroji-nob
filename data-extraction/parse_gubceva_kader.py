"""
Parser: Gubčeva brigada (SNOUB "Matija Gubec", brigade code 62) — its command, a second list.

Source: Lado Ambrožič-Novljan, "Gubčeva brigada" (Knjižnica NOV in POS, 1972; znaci.org 00003/782.pdf, PDF pp. 976-979,
        book pp. 975-978, just before its roster on the site)  →  website/public/pdfs/gubceva-kader.pdf:
        "Poveljniški kader", the brigade's commanders, political commissars, their deputies and chiefs of staff, and
        its four battalions' commanders and commissars, a name a line, surname first, with the days held:
    Komandanti brigade
    Mihevc Edo-Dore Trdina      od 4. 9. 1942 do 16. 9. 1942
The part after the hyphen is what he was called ("zvani Dore Trdina;"). A man in several posts is one record with
each. znaci re-typeset the book from its OCR, so the page shows its slips ("Stemad", "Keiržič", "®d", "12.1 943");
the names are read back from the brigade's roster and the lines that print them right (`NAMES`). The roster and the
fallen are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_cankarjeva_kader import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/gubceva-kader.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_782.pdf'   # znaci.org 00003/782.pdf
FIRST_PAGE, LAST_PAGE = 976, 979
TITLE = 'Poveljniški kader Gubčeve brigade'
HEADING = re.compile(r'^(Komandanti|Politični komisarji|Namestniki|Načelniki)\b')
NAMES = {'Cubrić': 'Čubrić', 'Cerne Zvone': 'Černe Zvone', 'Skrlj': 'Škrlj', 'Silih': 'Šilih', 'Stemad': 'Strnad',
         'Sali Karei': 'Sali Karel', 'Cmigoj': 'Čmigoj', 'Rađulović': 'Radulović', 'Zvondmir': 'Zvonimir',
         'Keiržič': 'Keržič', 'Frainc': 'Franc', 'Viktoir': 'Viktor', 'VipSKnik': 'Vipotnik', 'Sarli': 'Šarli',
         # one man under two forms of his name, as the roster has him
         'Vrečko Zvonimir': 'Vrečko Zvone', 'Gaberc Bogomil': 'Gaberc Bogomir', 'Zgonc Anton': 'Zgonc Tone'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def when_of(text: str) -> str:
    """'od 14. 7. 1943 do 17. 12.1 943' -> 'od 14. 7. 1943 do 17. 12. 1943'; days in words stay ('do aprila 1944')."""
    text = text.replace('®d', 'od').replace('\\5.', '5.').replace('Ì944', '1944')
    text = re.sub(r'(\d)\.(\d) (\d{3})\b', r'\1. \2\3', text)
    return re.sub(r'\s+', ' ', text).strip()


def unit_of(duty: str) -> str:
    m = re.search(r'\b([IV]+)\. bataljona', duty)
    return f"{['I', 'II', 'III', 'IV'].index(m.group(1)) + 1}. bataljon" if m else 'Štab brigade'


def read_posts(pdf_path: str) -> None:
    duty = ''
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for r in rows_of(viewer_words(page)):
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}|POVELJNIŠKI KADER|:|62 Gubčeva brigada \d{3}', text):
                    continue
                if HEADING.match(text) and not re.search(r'\d', text.replace('I.', '').replace('V.', '')):
                    duty = text
                    continue
                i = next(i for i, w in enumerate(r) if w['text'] in ('od', '®d'))
                POSTS.append({'duty': duty, 'name': ' '.join(w['text'] for w in r[:i]),
                              'when': when_of(' '.join(w['text'] for w in r[i:])), 'page': n, 'words': r[:i]})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        name = p['name']
        for a, b in NAMES.items():
            name = name.replace(a, b)
        title = 'dr.' if ' dr. ' in f' {name} ' else ''
        name = name.replace(' dr. ', ' ')
        last, _, rest = name.partition(' ')                                  # "Pečanac": no given name
        given, _, nick = rest.partition('-')
        p.update(last=last, given=given.strip(), nick=nick.strip(), title=title, unit=unit_of(p['duty']),
                 text=f"{p['duty'][:1].lower()}{p['duty'][1:]}, {p['when']}")
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
            s['_posts'], s['_nicks'], s['_rects'], s['_title'] = [], [], [], p['title']
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
        s['additional_info'] = '; '.join(([s['_title']] if s['_title'] else []) + [f'zvani {n}' for n in s['_nicks']]
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects', '_title'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=62, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/gubceva-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
