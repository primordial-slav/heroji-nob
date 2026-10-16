"""
Parser: Mosorski partizanski odred (brigade code 148) — "Pregled rukovodećeg kadra Mosorskog PO 1942—1944.", a third
list.

Source: Miroslav Velić, Ante V. Petrić, *Mosorski partizanski odred* (znaci.org 00003/794, the whole book's PDF pp.
        565-570, book pp. 563-568, after its list of the odred's fighters on the site)  →
        website/public/pdfs/mosorski-odred-kader.pdf: the odred's leaders 1942-1944 under each duty, from its
        commanders to its platoon commanders, platoon delegates and company nurses, a name each, surname first, three
        columns, alphabetical down each column:
    KOMANDANTI ODREDA
    Baučić Jakiša          Gazin Ferdo          Furdšić Ivo (CPO)
"(zamj.)" after a name is a deputy, "(CPO)" as the book prints it. A man in several posts is one record with each. znaci
re-typeset the book from its OCR, so the page shows its slips ("Re4ć Lovre", "&unko Josip", "Rad ano vi ć"): a name is
read back from the odred's own records where one record's surname and given name are that close to it (`read_back`).
The fighters are the unit's first list (IDs from 1), part II's from 10001; these get IDs from 20001.
"""
import difflib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_cankarjeva_kader import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/mosorski-odred-kader.pdf'
UNIT = 'website/public/mosorski-odred-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_794.pdf'   # znaci.org 00003/794.pdf
FIRST_PAGE, LAST_PAGE = 565, 570
TITLE = 'Pregled rukovodećeg kadra Mosorskog PO 1942—1944.'
MARKS = re.compile(r'\((zamj?\.|CPO)\)')
NAMES: dict = {}                                   # folded "surname given" -> the unit's spelling
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def fold(t: str) -> str:
    t = unicodedata.normalize('NFKD', t.lower().replace('đ', 'd'))
    return re.sub(r'[^a-z ]', '', ''.join(c for c in t if not unicodedata.combining(c)))


def load_names() -> None:
    """The odred's names as this list prints them: each surname of a double one ("Gugić-Eterović" for a woman's
    married name) with the given name before its nickname ("Balaban Petar-Pero" is Balaban Petar here)."""
    for s in json.load(open(UNIT, encoding='utf-8')):
        if s['soldier_id'][4:6] in ('00', '01'):
            for given in s['first_name'].split('-')[:2]:                     # "Roje Ivan-Ivo" is Roje Ivo here too
                for last in s['last_name'].split('-'):
                    NAMES.setdefault(fold(f'{last} {given}'), f'{last} {given}')


# the OCR's slips no record is close enough to read back, read from the page and the odred's records
FIXES = {'Bacd Eduard': 'Bacci Eduard', 'BuMć Ivo': 'Bulić Ivo', 'I«!as Spiro': 'Lelas Špiro', 'LeJas Spire': 'Lelas Špiro',
         'LeJas Ante': 'Lelas Ante', 'Kovaöiq Vuk': 'Kovačić Vuk', 'Kmić Anite': 'Krnić Ante', 'Smajić Pavie': 'Smajić Pavle',
         'Tafi\'a Božidar': 'Tafra Božidar', 'Sanie Jozo': 'Sanić Jozo', 'Miimica Miro': 'Mimica Miro'}


def read_back(name: str) -> str:
    """The odred's spelling of a name the OCR garbled ('Re4ć Lovre' = Reić Lovre), when one record is that close."""
    name = FIXES.get(name, name)
    key = fold(name).replace(' ', '')                                       # "Ai ji no vic Ilija": the OCR's spaces
    nospace = {k.replace(' ', ''): v for k, v in NAMES.items()}
    if key in nospace:
        return nospace[key]
    close = difflib.get_close_matches(key, list(nospace), n=2, cutoff=0.86)
    if len(close) == 1 or len(close) == 2 and difflib.SequenceMatcher(None, key, close[0]).ratio() > \
            difflib.SequenceMatcher(None, key, close[1]).ratio() + 0.05:
        return nospace[close[0]]
    return re.sub(r'\s+', ' ', name).strip()


def columns_of(rows: list[list[dict]]) -> list[float]:
    """The three columns' left edges: the x where most names start."""
    xs = Counter(round(w['x0'] / 4) * 4 for r in rows for w in r)
    starts = []
    for x, _ in xs.most_common():
        if all(abs(x - s) > 60 for s in starts):
            starts.append(x)
        if len(starts) == 3:
            break
    return sorted(starts)


def read_posts(pdf_path: str) -> None:
    duty = ''
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            rows = rows_of(viewer_words(page))
            text_of = lambda r: ' '.join(w['text'] for w in r)
            body = [r for r in rows if re.search(r'[a-zčćžšđ]', text_of(r)) and not re.fullmatch(r'\d{3}', text_of(r))]
            cols = columns_of(body)
            for r in rows:
                text = text_of(r)
                if re.fullmatch(r'\d{3}|PREGLED|RUKOVODEĆEG KADRA MOSORSKOG PO|1942—1944\.?', text):
                    continue
                if not re.search(r'[a-zčćžšđ]{2}', text.replace('OZN-e', 'OZN').replace('SKOJ-a', 'SKOJ')):
                    duty = text.replace('CETA', 'ČETA').strip()
                    continue
                # the names two words each, surname and given name: a piece the OCR broke off in small letters
                # ("Haj der", "Rad ano vi ć") joins the word before; a mark ("(zamj.)") goes with the name before
                tokens: list = []
                for w in r:
                    if tokens and (w['text'][:1].islower() or len(w['text']) == 1 and w['text'].isupper() is False) \
                            and not MARKS.fullmatch(w['text']):
                        tokens[-1] = {**tokens[-1], 'text': tokens[-1]['text'] + w['text'], 'x1': w['x1']}
                    else:
                        tokens.append(dict(w))
                name: list = []
                for t in tokens:
                    if MARKS.fullmatch(t['text']):
                        if POSTS and POSTS[-1]['page'] == n:
                            POSTS[-1]['marks'].append(MARKS.fullmatch(t['text']).group(1))
                        continue
                    name.append(t)
                    if len(name) == 2 or '-' in t['text'] and len(name) == 2:
                        POSTS.append({'duty': duty, 'name': ' '.join(x['text'] for x in name), 'marks': [], 'page': n,
                                      'words': name})
                        name = []
                if name:                                                      # one word left: a name the OCR split
                    POSTS.append({'duty': duty, 'name': ' '.join(x['text'] for x in name), 'marks': [], 'page': n,
                                  'words': name})


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    load_names()
    read_posts(pdf_path)
    for p in POSTS:
        name = read_back(p['name'])
        last, _, given = name.partition(' ')
        duty = p['duty'].lower().replace('ozn-e', 'OZN-e').replace('skoj-a', 'SKOJ-a')
        note = ', '.join('zamjenik' if m.startswith('zam') else m for m in p['marks'])
        p.update(last=last, given=given, text=duty + (f' ({note})' if note else ''))
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'] or '', '', '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = fold(f"{p['last']} {p['given']}").replace(' ', '')             # "Perišin" and "PeriSin", "Dorđe" and "Đorđe"
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_rects'] = [], []
            out.append(s)
        if p['text'] not in man['_posts']:
            man['_posts'].append(p['text'])
        if p['page'] == man['pdf_page']:
            ws = p['words']
            man['_rects'].append([round(min(w['x0'] for w in ws), 1), round(min(w['top'] for w in ws), 1),
                                  round(max(w['x1'] for w in ws), 1), round(max(w['bottom'] for w in ws), 1)])
    for s in out:
        s['additional_info'] = f"{TITLE}: {'; '.join(s['_posts'])}."
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=148, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=20001, keep_other_sources=True)
