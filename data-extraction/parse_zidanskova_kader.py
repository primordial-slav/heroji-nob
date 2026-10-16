"""
Parser: Zidanškova brigada (brigade code 65) — its command, a second list.

Source: Mirko Fajdiga, "Zidanškova brigada" II (Knjižnica NOV in POS, 1975; znaci.org 00003/776.pdf, PDF pp. 730-731,
        book pp. 729-730, just before its roster on the site)  →  website/public/pdfs/zidanskova-kader.pdf:
        "Poveljniški kader", the brigade's commanders, political commissars, their deputies (or assistants) and chiefs
        of staff, and its SKOJ secretaries, a name a line with the days held, which some give in words ("od konca
        aprila 1944", "do druge polovice novembra 1944", run on to the next line):
    Komandanti:
    Andrej Cetinski-Lev          od 27. 3. 1944 do 28. 10. 1944
The part after the hyphen is what he was called ("zvani Lev;", as the roster writes it). A man in several posts is one
record with each. znaci re-typeset the book from its OCR, so the page shows its slips ("CižmeknBor", "Fame Sever");
the names are read back from the brigade's roster (`NAMES`). The roster is the unit's first list (IDs from 1); these
get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_cankarjeva_kader import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/zidanskova-kader.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_776.pdf'   # znaci.org 00003/776.pdf
FIRST_PAGE, LAST_PAGE = 730, 731
TITLE = 'Poveljniški kader Zidanškove brigade'
HEADING = re.compile(r'^(Komandanti|Politični komisarji|Namestniki|Načelniki štaba|SEKRETARJI SKOJ)')
# the OCR's slips, read back from the brigade's roster
NAMES = {'CižmeknBor': 'Cižmek-Bor', 'Vdncenc': 'Vincenc', 'Fame Sever': 'Franc Sever', 'Stajner': 'Štajner',
         'Aleksanda Vojinović': 'Aleksandar Vojinović', 'Skolski': 'Školski', 'Stefan Gerhold': 'Štefan Gerhold',
         'Sircelj': 'Šircelj', 'Hilda Turk (Vojinović)-Dunja': 'Hilda Vojinović-Dunja'}
MAIDEN = {('Vojinović', 'Hilda'): 'roj. Turk'}                        # "Hilda Turk (Vojinović)", the roster's "roj. Turk"
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def when_of(text: str) -> str:
    """The days as printed, the OCR's slips mended: 'cd 8. 1. 1944', 'do 27 2. 1944', 'srede j/ulij a 1944'."""
    text = re.sub(r'^cd\b', 'od', text).replace('j/ulij a', 'julija')
    text = re.sub(r'\b(\d{1,2}) (\d{1,2})\. (19\d\d)', r'\1. \2. \3', text)
    return re.sub(r'\s+', ' ', text).strip()


def read_posts(pdf_path: str) -> None:
    duty, post, pending = '', None, []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for r in rows_of(viewer_words(page)):
                text = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}|POVELJNI[SŠ]KI KADER', text):
                    continue
                if HEADING.match(text):
                    duty = text.rstrip(' :')
                    duty = 'sekretarji SKOJ' if duty.startswith('SEKRETARJI') else duty[:1].lower() + duty[1:]
                    post = None
                    continue
                od = next((i for i, w in enumerate(r) if w['text'] in ('od', 'cd')), None)
                if od is None and (post is None or text.endswith('-')):      # "Aleksanda Vojinović-" / "Vojin od ..."
                    pending += r
                    continue
                if od is None:                                                # the name or the days run on
                    for w in r:
                        (post['name'] if w['x0'] < post['date_x'] - 3 else post['when']).append(w['text'])
                        if w['x0'] < post['date_x'] - 3 and post['page'] == n:
                            post['words'].append(w)
                    continue
                post = {'duty': duty, 'name': [w['text'] for w in pending + r[:od]], 'when': [w['text'] for w in r[od:]],
                        'date_x': r[od]['x0'], 'page': n, 'words': pending + r[:od]}
                POSTS.append(post)
                pending = []


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        name = ' '.join(p['name']).replace('- ', '-')
        for a, b in NAMES.items():
            name = name.replace(a, b)
        given, _, rest = name.partition(' ')
        last, _, nick = rest.partition('-')
        p.update(last=last.strip(), given=given, nick=nick.strip())
        p['text'] = f"{p['duty']}, {when_of(' '.join(p['when']))}"
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
            s['unit_detail'] = 'Štab brigade'
            out.append(s)
        man['_posts'].append(p['text'])
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        if p['page'] == man['pdf_page']:
            for line in sorted({round(w['top']) for w in p['words']}):
                ws = [w for w in p['words'] if round(w['top']) == line]
                man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                      round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        key = (s['last_name'], s['first_name'])
        word = 'zvana' if key in MAIDEN else 'zvani'
        s['additional_info'] = '; '.join([f'{word} {n}' for n in s['_nicks']] + ([MAIDEN[key]] if key in MAIDEN else [])
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}."])
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
    run_parser(pdf_path=PDF, brigade_code=65, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/zidanskova-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
