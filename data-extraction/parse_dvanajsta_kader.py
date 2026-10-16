"""
Parser: Dvanajsta brigada (XII. SNOUB, brigade code 63) — its command, a second list.

Source: Lado Ambrožič-Novljan, "Dvanajsta brigada" (Knjižnica NOV in POS 16, 1976; znaci.org 00003/814.pdf, PDF pp.
        573-576, book pp. 571-574, before its lists on the site)  →  website/public/pdfs/dvanajsta-kader.pdf:
        "Poveljniški kader", the brigade's commanders, political commissars, their deputies and chiefs of staff, and
        its five battalions' commanders and commissars, a name a line with the days held, as the Cankarjeva's
        (parse_cankarjeva_kader); then, names only, two to a line, the heads of its intelligence centre, its
        quartermasters, its medical officers and its SKOJ secretaries.
The part after a hyphen is what he was called ("zvani Raco;", as the roster writes it). A man in several posts is one
record with each. The text layer sets a line's days a point or three below its name, so a line is built from the words
of the name column and the days nearest below them (two lines on p. 2 run into one otherwise). znaci re-typeset the
book from its OCR, so the page shows its slips ("rranc", "\\lfonz", "San Mavrin" = Žan): the names are read back from
the brigade's roster (`NAMES`). "Danilo", whose surname the book doesn't give, is a record under that name, as the
roster's Danilo is. The roster and the fallen are the unit's first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/dvanajsta-kader.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_814.pdf'   # znaci.org 00003/814.pdf
FIRST_PAGE, LAST_PAGE = 573, 576
TITLE = 'Poveljniški kader Dvanajste brigade'
HEADING = re.compile(r'^(Komandanti|Politični komisarji|Namestniki|Načelniki|Šefi|Intendanti|Sanitetni referenti|Sekretarji SKOJ)')
NAMES_ONLY = re.compile(r'^(Šefi|Intendanti|Sanitetni referenti|Sekretarji SKOJ)')
# the OCR's slips, read back from the brigade's roster
NAMES = {'Zokalj': 'Žokalj', 'Niko Silih': 'Niko Šilih', 'Stefan Gebert': 'Štefan Gebert', 'Znidaršič-Stefan': 'Žnidaršič-Štefan',
         'žnidaršič-Stefan': 'Žnidaršič-Štefan', 'Teršelič-Zagar': 'Teršelič-Žagar', 'Pacek-Platim': 'Pacek-Platin',
         'lulij ': 'Julij ', '[van ': 'Ivan ', 'rranc ': 'Franc ', '\\lfonz ': 'Alfonz ', 'stefan Slosar': 'Štefan Šlosar',
         '«tarija': 'Marija', 'Vnton ': 'Anton ', 'ranez ': 'Janez ', 'San Mavrin': 'Žan Mavrin', "'osip ": 'Josip ',
         'Tumer-Kostj a': 'Turner-Kostja', 'Merlak-Marjam': 'Merlak-Marjan', 'Karl Krautberger': 'Karel Krautberger'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def lines_of(page) -> list[list[dict]]:
    """Lines anchored on the name column: a word right of it joins the nearest line above it within 5 points."""
    ws = sorted(viewer_words(page, y_tolerance=1), key=lambda w: (w['top'], w['x0']))
    od = sorted(w['x0'] for w in ws if w['text'] == 'od')
    od_x = od[len(od) // 2] if od else page.width
    lines: list = []
    for w in ws:                                                             # the name column's lines first
        if w['x0'] < od_x - 8:
            line = next((l for l in lines if abs(l[0]['top'] - w['top']) <= 1.5), None)
            (lines.append([w]) if line is None else line.append(w))
    for w in ws:                                                             # then the days, to the nearest above
        if w['x0'] >= od_x - 8:
            near = [l for l in lines if -1.5 <= w['top'] - l[0]['top'] <= 5]
            if near:
                min(near, key=lambda l: abs(w['top'] - l[0]['top'] - 1)).append(w)
            elif re.search(r'\w\w', w['text']):                              # not a stray "." of the text layer
                lines.append([w])
    return [sorted(l, key=lambda w: w['x0']) for l in sorted(lines, key=lambda l: l[0]['top'])]


def when_of(text: str) -> str:
    """'od 24. 9. 1943 d.o 26. 11. 1943', 'od 26. 7. 1944 d 0 5. 5. 1945', 'od 1. 3. 1944 konec 3. 1944'."""
    text = re.sub(r'\bd\.o\b|\bd 0\b|\bd(?= \d)', 'do', text.replace("'", ''))
    out = []
    for word, half in zip(('od', 'do'), re.split(r'\b(?:do|konec)\b', text.replace('od ', '', 1), 1)):
        n = re.findall(r'\d+', half)
        out.append(f"{word} {'. '.join(n)}" if n else '')
    if 'konec' in text:
        out[1] = out[1].replace('do ', 'konec ')
    return ' '.join(x for x in out if x)


def unit_of(duty: str) -> str:
    m = re.search(r'\b([1-5I])\. bataljona', duty)
    return f"{'1' if m.group(1) == 'I' else m.group(1)}. bataljon" if m else 'Štab brigade'


def read_posts(pdf_path: str) -> None:
    duty, names_only = '', False
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            mid = page.width / 2
            for line in lines_of(page):
                text = ' '.join(w['text'] for w in line)
                if re.fullmatch(r'\d{3}|POVELJNIŠKI KADER|0', text):
                    continue
                if HEADING.match(text):
                    duty, names_only = text, bool(NAMES_ONLY.match(text))
                    continue
                if names_only:                                               # two names a line
                    for side in ([w for w in line if w['x0'] < mid - 20], [w for w in line if w['x0'] >= mid - 20]):
                        if side:
                            POSTS.append({'duty': duty, 'name': ' '.join(w['text'] for w in side), 'when': '',
                                          'page': n, 'words': side})
                    continue
                i = next(i for i, w in enumerate(line) if w['text'] == 'od')
                POSTS.append({'duty': duty, 'name': ' '.join(w['text'] for w in line[:i]),
                              'when': when_of(' '.join(w['text'] for w in line[i:])), 'page': n, 'words': line[:i]})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    seen = set()
    kept = []
    for p in POSTS:
        name = p['name']
        for a, b in NAMES.items():
            name = name.replace(a, b)
        note = ''
        if name.startswith('medicinec '):                                    # "medicinec Dušan Grom"
            note, name = 'medicinec', name[len('medicinec '):]
        title = 'dr.' if name.startswith('dr. ') else ''
        name = name[len('dr. '):] if title else name
        words = name.split()
        if len(words) == 1:                                                  # "Danilo", "dr. Kolar": one name
            last, given, nick = words[0], '', ''
        else:
            last, _, nick = ' '.join(words[1:]).partition('-')
            given = words[0]
        key = (p['duty'], last, given)
        if key in seen:                                                      # "Stane Ulčar-Jurček" in both columns
            continue
        seen.add(key)
        duty = p['duty'][:1].lower() + p['duty'][1:]
        p.update(last=last, given=given, nick=nick, title=title, unit=unit_of(p['duty']),
                 text=', '.join(x for x in (duty, note, p['when']) if x))
        kept.append(p)
    POSTS[:] = kept
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
    run_parser(pdf_path=PDF, brigade_code=63, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/dvanajsta-soldiers.json',
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
