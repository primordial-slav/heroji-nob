"""
*Prilog u krvi* (Opštinski odbor SUBNOR-a Pljevlja; znaci.org 00001/109, the chapter 109_4.pdf →
website/public/pdfs/prilog-u-krvi-pali-borci.pdf): the fallen fighters of the NOR of the Pljevlja srez, April 1941 -
15 May 1945 (book pp. 141-216), a book across units: its entries are added to the records of the soldiers it describes
(scripts/match_references.py), the rest go to Ostali borci.

Cyrillic, one column, numbered, each entry's first line indented: "1. АДИЛОВИЋ Реџа ХИЛМО, рођен 1918, Ковачевићи,
Пљевља, земљорадник. Члан КПЈ. У НОБ-у од фебруара 1942. Борац 2. златарског (нововарошког) ударног батаљона. ...
Погинуо, као десетар, у борби против четника код Челебића, 15. априла 1943." The book counts among its fallen fighters
also the party and SKOJ workers, the members of the liberation committees and the collaborators of the NOP who were
killed (its foreword, p. 136); only the fighters go in, by the rule of `parse_mosorski_odred_2.fighter` (borac, a
military duty, an army unit), the user's decision of 2026-10-14 for lists of fighters and others together. Fighters of
other regions who fell near Pljevlja are not in the book (p. 137). An entry names the site's brigades its bio names
(`units`: the 3. proleterska sandžačka = 5, the 4. sandžačka = 98, ...).

Output: data-extraction/znaci/prilog-u-krvi-pali-borci-entries.json (IDs 9060xxxxxx, by the book's number).
Usage: python data-extraction/parse_prilog_u_krvi.py [--sample N] [--dropped]
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
import entry_boxes  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'prilog-u-krvi-pali-borci.pdf'
OUT = HERE / 'znaci' / 'prilog-u-krvi-pali-borci-entries.json'
PREFIX = '9060'
TITLE = 'Pali borci NOR-a pljevaljskog sreza'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
START = re.compile(rf'^(\d{{1,3}})\s?[.,]\s*(?=[{U}][{U}J]{{2}})')
UNITS = [(r'\b(?:3\.|III|treć\w+)\s*proletersk\w*\s*(?:\(?\s*sandžačk|sandžačk|narodnooslobodilačk\w*\s+udarn\w*\s+brigad\w*\s*\(sandžačk)', 5),
         (r'\b(?:3\.|III)\s*proletersk\w*\s+(?:\w+\s+){0,3}brigad\w*\s*\(sandžačk', 5),
         (r'\b(?:4\.|IV)\s*sandžačk', 98),
         (r'\b(?:3\.|III)\s*krajišk\w*\s+proletersk', 10),
         (r'\b(?:1\.|I|prv\w+)\s*proletersk\w*\s+(?:\w+\s+){0,2}brigad', 1),
         (r'\b(?:2\.|II|drug\w+)\s*proletersk\w*\s+(?:\w+\s+){0,2}brigad', 39),
         (r'\b(?:4\.|IV)\s*proletersk\w*\s+(?:\(?\s*)?crnogorsk', 40),
         (r'\b(?:5\.|V)\s*proletersk\w*\s+(?:\(?\s*)?crnogorsk', 41),
         (r'\b(?:6\.|VI)\s*(?:istočnobosansk|proletersk\w*\s+istočnobosansk)', 42),
         (r'\b(?:10\.|X)\s*hercegovačk', 43),
         (r'Prateć\w*\s+bataljon\w*\s+Vrhovnog\s+štaba', 112)]   # the Vrhovni štab's escort
# an entry's first line without its number: SURNAME Father GIVEN at the indent ("DAMJANOVIĆ Stevana BRANKO")
NO_NUMBER = re.compile(rf'^.{{0,7}}?([{U}][{U}0]{{3,}}[{U}0-]*)\s+((?:[{U}][{L}]+|[{U}]\.)\s+[{U}]{{2,}}.*)$')     # "C8. DAJEVIĆ", "<{33)DESP0T0VIĆ"
MONTHS = 'januar|februar|mart|april|maj|jun|jul|avgust|septemb|oktob|novemb|decemb'


def read() -> list[dict]:
    entries = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
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
                t = cyrillic_to_latin(' '.join(w['text'] for w in ws)).strip()
                t = t.replace('J1', 'L').replace('j1', 'l')             # the OCR's Л: "J1EOVAC" = LEOVAC, "PJ1ISKA"
                x0 = ws[0]['x0']
                if re.fullmatch(r'[\d\W]{1,5}', t):
                    continue                                             # the page number
                indented = x0 > text_x + 12                              # an entry's first line is indented
                m = START.match(re.sub(r"^[.'•·*\"„]+\s*", '', t)) if indented else None   # ".147.", "'176.", "•323."
                if m:
                    t = re.sub(r"^[.'•·*\"„]+\s*", '', t)
                    entries.append({'no': int(m.group(1)), 'lines': [t[m.end():]], 'pdf_page': pno,
                                    'pdf_x': round(x0, 1), 'pdf_y': round(ln['top'], 1)})
                elif indented and entries and NO_NUMBER.match(t):         # the OCR lost the number: the next one
                    nm = NO_NUMBER.match(t)
                    t = nm.group(1).replace('0', 'O') + ' ' + nm.group(2)
                    entries.append({'no': entries[-1]['no'] + 1, 'lines': [t], 'pdf_page': pno,
                                    'pdf_x': round(x0, 1), 'pdf_y': round(ln['top'], 1)})
                elif entries:
                    entries[-1]['lines'].append(t)
    # a number read as the next one ("313" for 312, then 313 itself): the first of the two takes the one missing
    for i in range(1, len(entries) - 1):
        if entries[i]['no'] == entries[i + 1]['no'] and entries[i - 1]['no'] == entries[i]['no'] - 2:
            entries[i]['no'] -= 1
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[­-]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('­-') + ln                             # "Pljev-" / "lja"
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def title_case(word: str) -> str:
    return '-'.join(p[:1] + p[1:].lower() for p in word.split('-'))


def parse(e: dict) -> dict:
    text = re.sub(r'\bVor(ac|kinja)\b', r'Bor\1', join(e['lines']))     # the OCR's В for Б: "Vorac"
    m = re.match(r'^(.+?),\s*(?=ro[đd]en|bio\b|poginu|ubijen|strijeljan)', text, re.I)
    head, info = (m.group(1), text[m.end():]) if m else (text.split(',')[0], text[len(text.split(',')[0]) + 1:].strip())
    words = head.replace('0', 'O').replace('—', '-').replace(',', ' ').split()      # "M0MČIL0", "JOVIĆ—PAVLOVIĆ"
    if words:
        words[0] = words[0].rstrip('.;:')                                 # "ŠLJUKIĆ. Novice MANOJLE"
    # SURNAME, the father in small letters, GIVEN ("ŠĆEPANOVIĆ Milije DARINKA"); an initial for the father ("Ž.")
    fi = next((i for i, w in enumerate(words) if i > 0 and re.fullmatch(rf'[{U}][{L}]+|[{U}][{L}]?\.', w)), None)
    if fi is not None:
        last, father, given = words[:fi], words[fi], words[fi + 1:]
    else:
        last, father, given = words[:1], '', words[1:]
    last = title_case('-'.join(last))
    given = [title_case(w) for w in given if w not in ('—', '–', '-')]
    first, nick = (given[0] if given else ''), ' '.join(given[1:])
    rec = {'soldier_id': f"{PREFIX}{e['no']:06d}", 'name': ' '.join(x for x in (last, father, first, nick) if x),
           'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father, 'no': e['no']}
    born = re.search(r'ro[đd]en[ae]?\s+(1[89]\d\d)\.?\s*,?\s*([^,.]+?)(?:,\s*([^,.]+?))?(?:,|\.|$)', info, re.I)
    rec['birth_year'] = born.group(1) if born else ''
    places = [born.group(2)] + ([born.group(3)] if born and born.group(3) and born.group(3).strip()[:1].isupper() else []) if born else []
    rec['born_in'] = ', '.join(x.strip() for x in places if x and x.strip())        # "Pljevlja, radnik": a trade
    # the death: the last sentence that says he fell, died or was killed, and its date
    death = None
    for d in re.finditer(r'(?:Poginu\w*|Umr\w*|Ubijen\w*|Strijelja\w*|Strelja\w*|Nesta\w*|podlega\w*|Zaklan\w*|Obješen\w*)[^.]*?'
                         r'(?:(\d{1,2})\.\s*)?(' + MONTHS + r')?\w*\s*(19[45]\d)', info, re.I):
        death = d
    rec['death_year'] = death.group(3) if death else ''
    if not rec['death_year'] and re.search(r'(?:Poginu|Umr|podlega)\w*[^.]*?u bici na Sutjesci', info, re.I):
        rec['death_year'] = '1943'                                    # the battle of the Sutjeska, May-June 1943
    when = parse_when(re.sub(r'\s+', ' ', f"{death.group(1) + '. ' if death.group(1) else ''}{death.group(2) or ''} {death.group(3)}".strip())) if death and death.group(2) else None
    rec['death_date'] = iso(when[0]) if when and when[0][2] else ''
    rec['units'] = sorted({code for pat, code in UNITS if re.search(pat, info, re.I)})
    rec['additional_info'] = f'{TITLE}: {info}'
    rec['list'] = TITLE
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


INSURGENT = re.compile(r"\bu napadu ustanik", re.I)   # "Poginuo u napadu ustanika iz Bobova na ustašku posadu"


def fighter(rec: dict) -> bool:
    return mos.fighter(rec) or bool(INSURGENT.search(rec['additional_info']))


def main() -> None:
    raw = read()
    every = [parse(e) for e in raw]
    recs = [r for r in every if fighter(r)]
    dropped = [r for r in every if not fighter(r)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    nos = [e['no'] for e in raw]
    gaps = [(a, b) for a, b in zip(nos, nos[1:]) if b != a + 1]
    print(f"{len(raw)} entries (numbers {nos[0]}-{nos[-1]}, gaps {gaps}); {len(recs)} fighters kept, {len(dropped)} left out; "
          f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    print(f"  no birth year: {sum(not r['birth_year'] for r in recs)}, no father: {sum(not r['fathers_name'] for r in recs)}, "
          f"no birthplace: {sum(not r['born_in'] for r in recs)}, year of death: {sum(bool(r['death_year']) for r in recs)}, "
          f"day of death: {sum(bool(r['death_date']) for r in recs)}, units: {Counter(u for r in recs for u in r['units'])}")
    if '--dropped' in sys.argv:
        for r in dropped:
            print(f"  OUT {r['no']}. {r['name']}: {r['additional_info'][len(TITLE) + 2:][:170]}")
    if '--sample' in sys.argv:
        random.seed(4)
        for r in random.sample(recs, min(len(recs), int(sys.argv[sys.argv.index('--sample') + 1]))):
            print(f"   {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} {r['units']}")
            print(f"      {r['additional_info'][:160]}")


if __name__ == '__main__':
    main()
