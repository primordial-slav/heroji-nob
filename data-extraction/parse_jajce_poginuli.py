"""
*Jajačko područje u oslobodilačkom ratu i revoluciji 1941-1945. - Zbornik sjećanja*, knjiga I and II (znaci.org 00003/722
and 721): the fighters of the Jajce area who fell, a list in each volume, books across units (see
scripts/match_references.py):
    knj. I, "Spisak boraca sa jajačkog područja poginulih 1941. godine" (the chapter 722_1.pdf → jajce-1941-poginuli.pdf):
        "1. AĆIMOVIĆ Mitra JOVO — rođen 1924. godine u selu Majevcu, opština Šipovo, Srbin, zemljoradnik, poginuo u avgustu
        prilikom borbe za oslobođenje Šipova kao borac Pljevskog gerilskog bataljona."
    knj. II, "Spisak boraca i aktivista NOP-a sa jajačkog područja poginulih 1942. godine" (721_1.pdf →
        jajce-1942-poginuli.pdf): "1. ADEMOVIĆ Sulje HALIL, rođen 1900. godine u Jajcu, Musliman, stolarski radnik, borac
        Bataljona »Pelagić« III krajiškog NOP odreda, poginuo 25.10.1942. godine kod sela Popuža."
One column, numbered, each entry's first line indented; SURNAME, the father in the genitive, GIVEN. Every man of a list
fell in its year (`death_year`), the day where the entry gives it; the brigades the site has as `units` (1. krajiška =
123, 5. kozaračka = 12). The authors' note at the end of the 1941 list stays out.

Output: data-extraction/znaci/jajce-1941-poginuli-entries.json (IDs 9033xxxxxx) and jajce-1942-poginuli-entries.json
(9034xxxxxx), each entry with its place on the page and its box (entry_boxes).
Usage: python data-extraction/parse_jajce_poginuli.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

BOOKS = [('jajce-1941-poginuli', '9033', '1941', 'Spisak boraca sa jajačkog područja poginulih 1941. godine'),
         ('jajce-1942-poginuli', '9034', '1942', 'Spisak boraca i aktivista NOP-a sa jajačkog područja poginulih 1942. godine')]
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
START = re.compile(rf'^(\d{{1,3}})\s?[.,]\s*(?=[{U}][{U}lj(]{{2}})')
UNITS = [(r'\b(?:I|1\.)\s*krajišk\w*\s+(?:NOU\s+|proletersk\w*\s+|udarn\w*\s+)*brigad', 123),
         (r'\b(?:Prv\w+)\s+krajišk\w*\s+(?:NOU\s+|proletersk\w*\s+|udarn\w*\s+)*brigad', 123),
         (r'\b(?:V|5\.)\s*kozaračk', 12), (r'\b(?:II|2\.)\s*krajišk\w*\s+(?:NOU\s+|udarn\w*\s+)*brigad', 24)]
MONTHS = 'januar|februar|mart|april|maj|jun|jul|avgust|septemb|oktob|novemb|decemb'


def read(pdf_name: str) -> list[dict]:
    entries = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / f'{pdf_name}.pdf') as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lines = []
            for w in sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0'])):
                if lines and abs(w['top'] - lines[-1]['top']) < 3:
                    lines[-1]['words'].append(w)
                else:
                    lines.append({'top': w['top'], 'words': [w]})
            xs = sorted(min(w['x0'] for w in ln['words']) for ln in lines)
            text_x = xs[len(xs) // 4] if xs else 0                       # the column's edge (most lines start there)
            for ln in lines:
                ws = sorted(ln['words'], key=lambda w: w['x0'])
                if len(ws) > 1 and re.fullmatch(r'[■•·*^]+', ws[0]['text']):
                    ws = ws[1:]                                          # a speck before the number ("■ 95.")
                t = ' '.join(w['text'] for w in ws).strip()
                x0 = ws[0]['x0']
                if re.fullmatch(r'[\d\W]{1,5}', t) or re.match(r'^SPISAK\b|^NAPOMENA\b|^GODINE$|^POGINULIH\b', t):
                    if t.startswith('NAPOMENA'):
                        return entries                                  # the authors' note ends the list
                    continue
                m = START.match(t) if x0 > text_x + 8 else None         # an entry's first line is indented
                if m:
                    entries.append({'no': int(m.group(1)), 'lines': [t[m.end():]], 'pdf_page': pno,
                                    'pdf_x': round(x0, 1), 'pdf_y': round(ln['top'], 1)})
                elif entries:
                    entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[­-]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('­-') + ln                             # "opšti-" / "na", "Va­" / "kuf"
        else:
            text += (' ' if text else '') + ln
    text = re.sub(r'\s+', ' ', text).strip()
    return re.sub(r'(?<=\.)\s+\d{1,3}$', '', text)                      # the page number set on the last line's height


def caps(word: str) -> str:
    """A name in capitals as the OCR has it: l for I ("TOMlClĆ"), a stray bracket ("MAR(JANAC"), "LjUPKO"."""
    word = word.replace('(', '').replace(')', '')
    if sum(c.isupper() for c in word) >= 2:
        word = re.sub(r'l(?!j)', 'I', word)
    return word.upper()


def parse(e: dict, prefix: str, year: str, title: str, n: int) -> dict:
    text = join(e['lines'])
    m = re.match(rf'^(.+?)\s*(?:[—–-]+\s*|,\s*|\s+)(?=ro[đd]en|bio\b|poginu|ubijen|strijeljan)', text, re.I)
    head, info = (m.group(1), text[m.end():]) if m else (text.split(',')[0], text[len(text.split(',')[0]) + 1:].strip())
    words = re.sub(r'(?<=\s)lie(?=\s)', 'Ilije', head).replace(',', ' ').split()      # "LAKETIĆ lie MILAN": Ilije
    # SURNAME (a double one: "BOŠNJAK-MARIĆ"), Father in small letters, GIVEN (and a second, what he was called)
    fi = next((i for i, w in enumerate(words) if i > 0 and re.fullmatch(rf'[{U}][{L}]+|[{U}]\.', w)), None)
    if fi is not None:
        last, father, given = words[:fi], words[fi], words[fi + 1:]
    else:
        last, father, given = words[:1], '', words[1:]
    last = '-'.join(kl.spelled(caps(p), 'last') for p in '-'.join(last).split('-') if p)
    last = re.sub(r'ič$', 'ić', last)                                   # "LAKETIČ": no name here ends in -ič
    z = next((i for i, w in enumerate(given) if w.lower() in ('zvani', '—zvani')), None)
    given = [w for w in given if w not in ('—', '–', '-')]
    if z is not None:                                                   # "SIMO — zvani Rus"
        given = [w for w in given if w.lower() not in ('zvani', '—zvani')]
    given = [kl.spelled(caps(w), 'first') for w in given]
    first, nick = (given[0] if given else ''), ' '.join(given[1:])
    rec = {'soldier_id': f'{prefix}{n:06d}', 'name': ' '.join(x for x in (last, father, first, nick) if x),
           'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father}
    born = re.search(r'ro[đd]en\w*\s+(1[89]\d\d)\.?\s*(?:godine\s*)?,?\s*(?:s?u\s+)?(?:(?:selu|s\.)\s+)?([^,]+?)'
                     r'(?:,\s*opštin\w*\s+([^,]+))?(?:,|$)', info, re.I)
    rec['birth_year'] = born.group(1) if born else ''
    rec['born_in'] = ', '.join(x.strip() for x in (born.group(2), born.group(3) or '') if x and x.strip()) if born else ''
    rec['death_year'] = year
    when = re.search(rf'\b(\d{{1,2}})\s?\.\s?(\d{{1,2}}|(?:{MONTHS})\w*)\.?\s*({year})', info)
    parsed = parse_when(re.sub(r'\s+', ' ', when.group(0))) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = sorted({code for pat, code in UNITS if re.search(pat, info, re.I)})
    rec['additional_info'] = f'{title}: {info}'
    rec['list'] = title
    rec.update(pdf_file=e['pdf'], pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main() -> None:
    ofz.corpus()
    for name, prefix, year, title in BOOKS:
        raw = read(name)
        for e in raw:
            e['pdf'] = f'{name}.pdf'
        recs = [parse(e, prefix, year, title, i) for i, e in enumerate(raw, 1)]
        stats = entry_boxes.fill_boxes(recs)
        out = HERE / 'znaci' / f'{name}-entries.json'
        out.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
        nos = [e['no'] for e in raw]
        gaps = [(a, b) for a, b in zip(nos, nos[1:]) if b != a + 1]
        print(f"{name}: {len(recs)} entries, numbers {nos[0]}-{nos[-1]}, gaps {gaps}; boxes: "
              f"{entry_boxes.describe(stats, stats['boxed'])}")
        print(f"  no birth year: {sum(not r['birth_year'] for r in recs)}, no father: {sum(not r['fathers_name'] for r in recs)}, "
              f"no birthplace: {sum(not r['born_in'] for r in recs)}, day of death: {sum(bool(r['death_date']) for r in recs)}, "
              f"units: {Counter(u for r in recs for u in r['units'])}")
        if '--sample' in sys.argv:
            random.seed(4)
            for r in random.sample(recs, min(len(recs), int(sys.argv[sys.argv.index('--sample') + 1]))):
                print(f"   {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} {r['units']}")
                print(f"      {r['additional_info'][:150]}")


if __name__ == '__main__':
    main()
