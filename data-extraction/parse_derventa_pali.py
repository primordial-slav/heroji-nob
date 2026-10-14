"""
Midhat Dizdarević, *Radnički pokret i NOR Dervente – dokumenti i sjećanja* (znaci.org 00003/827, the whole book's
PDF pp. 257-266, book pp. 257-266: "Pali borci narodnooslobodilačkog rata sa područja opštine Derventa") →
website/public/pdfs/derventa-pali-borci.pdf: a book across units. The book's next list, the victims of the terror by
place (pp. 267 on), stays out.

One column, numbered, a short bio each, its later lines flush:
    "4. Asentić Ranko rođen 1927. u Miškovcima, borac 14. srednjo-bosanske brigade, poginuo na Tromeđi."
    "44 .Durmiš M. Martin rođ. 1918. u Vrhovima borac 14. srednjo bosanske brigade poginuo u Prnjavoru."
The unit gives the site's unit code where the site has it (`units`), and the place he fell `death_place`.
Output: data-extraction/znaci/derventa-pali-borci-entries.json, IDs 9041xxxxxx, each with its box.
Usage: python data-extraction/parse_derventa_pali.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402

BOOK = 'derventa-pali-borci'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9041'
TITLE = 'Pali borci narodnooslobodilačkog rata sa područja opštine Derventa'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NUMBER_LOST = re.compile(rf'^[{U}][{L}]+\s+(?:[{U}]\.\s*)?[{U}][{L}]+,?\s+r(?:o[dđ]|\.)')
SLIPS = {'Dušan, 192,2.': 'Dušan, 1922.'}                  # Miličić Dušan (p. 6)
START = re.compile(r'^(\d{1,3})\s?(?:\.\s*\.?\s*(?=[A-ZČĆŽŠĐčćžšđ2]|$)|\s*(?=[A-ZČĆŽŠĐčćžšđ2]))')   # "2." alone too
# the site's units, by the words the book names them with ("14. srednjo-bosanske", "5. kozar. brig"); the 14., 18. and
# 19. srednjobosanska were the 53. division's (unit 33, whose records name them)
UNITS = [
    (r'\b14\.\s*s[re]+dnj\w*[\s-]*bos', 56), (r'\b1[489]\.\s*s[re]+dnj\w*[\s-]*bos', 33), (r'\b5\.\s*kozar', 12), (r'\b1\.\s*proleter', 1), (r'\b12\.\s*slavon', 146),
    (r'\b14\.\s*srpsk', 27), (r'\b8\.\s*krajišk', 14), (r'\b(?:II|2)\.\s*krajišk', 24), (r'\b7\.\s*vojvo', 22),
    (r'\b1\.\s*dalm', 36), (r'\b17\.\s*majev', 29), (r'\b15\.\s*majev', 49), (r'\b18\.\s*slavon', 17),
    (r'\b21\.\s*slavon', 34), (r'\b17\.\s*slavon', 16), (r'\b4\.\s*krajišk', 11), (r'\b6\.\s*krajišk', 13),
    (r'\b1\.\s*krajišk', 123), (r'\b11\.\s*krajišk', 107), (r'\b13\.\s*krajišk', 124), (r'\b3\.\s*krajišk', 10),
    (r'\b16\.\s*omlad', 37), (r'\b25\.\s*brodsk', 30), (r'\b21\.\s*tuzlan', 32), (r'\b18\.\s*hrvat', 52),
]


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_827.pdf'), fitz.open()
        out.insert_pdf(src, from_page=256, to_page=265)
        out.save(PDF, garbage=4, deflate=True)


def read() -> list[dict]:
    entries = []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for ln in entry_boxes.read_page(page)['columns'][0]:
                t = re.sub(r'^[^\w]+', '', ln['text'].strip())                 # specks before a number ("' 83.")
                for slip, read_as in SLIPS.items():
                    t = t.replace(slip, read_as)
                if re.fullmatch(r'\d{1,3}|\d+\s*arak\s*\d*|PALI BORCI.*|SA PODRUČJA OPŠTINE DERVENTA', t):
                    continue
                s = START.match(t)
                if s and (not entries or abs(int(s.group(1)) - entries[-1]['no'] - 1) <= 2):
                    entries.append({'no': int(s.group(1)), 'lines': [t[s.end():]], 'pdf_page': pno,
                                    'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1)})
                elif entries and NUMBER_LOST.match(t):
                    # the text layer lost the number ("6." set apart from "Asentić Tošo rođen 1920. ..."): the next one
                    entries.append({'no': entries[-1]['no'] + 1, 'lines': [t], 'pdf_page': pno,
                                    'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1)})
                elif entries:
                    entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[\xad-]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('\xad-') + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text.replace('\xad', '')).strip()


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    text = re.sub(r'(?<![\w])2(?=[a-zčćžšđ]{2})', 'Ž', text)            # "Babić 2ivko"
    text = text[:1].upper() + text[1:]                                    # "ćorić Petar"
    head = re.split(r'(?:\s+r(?:o[dđ](?:en[a]?)?|\.)?\.?\s*|,\s*)(?=1[89]\d\d|u\s)', text, maxsplit=1)   # "rod.", ", 1922." too
    name, rest = (head[0], head[1]) if len(head) == 2 else (text.split(' borac')[0], '')
    words = name.split()
    initial = [w for w in words if re.fullmatch(rf'[{U}]\.', w)]          # "Durmiš M. Martin", "H. Cehajić Hasan"
    words = [w for w in words if w not in initial]
    last = words[0] if words else ''
    father = initial[0] if initial else ''
    first = words[-1] if len(words) > 1 else ''
    by = re.match(r'(1[89]\d\d)', rest)
    # the village, in the locative as printed (the matcher compares the first letters): "u Miškovcima", "1925.U Potočanima"
    born = re.search(rf'^(?:1[89]\d\d[.,]?\s*)?(?:[uU]\s+)?((?:[{U}][{L}]*\.?\s?)+?)(?=[,\s]+(?:\d|borac|boarc|bor\.|komandir|komesar|politkomesar|zamjenik|desetar|vodnik|kurir|bolničar|Terenski)|,|$)', rest)
    # how and where he fell: "poginuo u Odžaku", "pog. u Jelahu", "pogonio u Šivši", "poqinuo na Srebreniku"
    fate = re.search(rf'\b(po[gq]\w*\.?|koginu\w*|ubijen\w*|umr\w+|strijelj\w+|nesta\w+|zaklan\w*)\s+(?:je\s+)?(?:u|na|kod)?\s*(.+?)\.?$', rest)
    death_place = fate.group(2).strip(' .,') if fate else ''
    units = sorted({code for pat, code in UNITS if re.search(pat, rest, re.I)})
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {first}'.strip(), 'last_name': last, 'also': [],
           'first_name': first, 'nick': '', 'fathers_name': father, 'birth_year': by.group(1) if by else '',
           'born_in': (born.group(1).strip() + ', Derventa') if born else '', 'death_place': death_place,
           'units': units, 'no': e['no'], 'additional_info': f'{TITLE}: {text}', 'list': TITLE,
           'pdf_file': PDF.name, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']}
    return rec


def main() -> None:
    build_pdf()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} fallen fighters -> {OUT.relative_to(HERE.parent)}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    gaps = [f"{a['no']}->{b['no']} (p{b['pdf_page']})" for a, b in zip(raw, raw[1:]) if b['no'] != a['no'] + 1]
    print(f'number gaps: {len(gaps)}', gaps[:20])
    print(f"birth year: {sum(bool(r['birth_year']) for r in recs)}, born in: {sum(bool(r['born_in']) for r in recs)}, "
          f"death place: {sum(bool(r['death_place']) for r in recs)}, a unit on the site: {sum(bool(r['units']) for r in recs)}")
    print(Counter(c for r in recs for c in r['units']).most_common())
    if '--sample' in sys.argv:
        random.seed(4)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} {r['birth_year']} [{r['born_in']}] "
                  f"{r['units']} † {r['death_place']!r} | {r['additional_info'][len(TITLE) + 2:][:90]}")


if __name__ == '__main__':
    main()
