"""
Radovan Vukanović, *Drugi udarni korpus* (Beograd 1982; znaci.org 00001/61, its last chapter 61_10.pdf, PDF pp. 35-37
→ website/public/pdfs/2-korpus-stabovi.pdf, book pp. 463-465): Prilog br. 1, "Spisak komandnog sastava štabova
divizija i štaba 2. udarnog korpusa", a book across units. Cyrillic, re-typeset by znaci: under each staff (the corps,
the 2. proleterska, 3. udarna, 29. and 37. udarna divizija, the Primorska operativna grupa, the Italian division
»Garibaldi« and the corps' artillery brigade) its commanders, political commissars, deputies for the military area and
chiefs of staff, a name a line, given name first, with the months held ("Пеко Дапчевић (септембар 1943—јул 1944)").
A man in several posts is one entry with each of them. The book names no fate; the pairs are chosen by hand
(rematch_references.HAND).

Output: data-extraction/znaci/2-korpus-stabovi-entries.json (IDs 9103xxxxxx, by each man's first post).
Usage: python data-extraction/parse_2_korpus_stabovi.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = '2-korpus-stabovi.pdf'
OUT = HERE / 'znaci' / '2-korpus-stabovi-entries.json'
PREFIX = '9103'
TITLE = 'Spisak komandnog sastava štabova divizija i štaba 2. udarnog korpusa'
BOOK_PAGE = {1: 463, 2: 464, 3: 465}
STAFFS = [('Штаб 2. корпуса', 'Štab 2. udarnog korpusa'), ('2. пролетерске', 'Štab 2. proleterske divizije'),
          ('3. ударне', 'Štab 3. udarne divizije'), ('29.', 'Štab 29. divizije'), ('37.', 'Štab 37. udarne divizije'),
          ('Приморска', 'Primorska operativna grupa'), ('Гарибалди', 'Štab italijanske divizije »Garibaldi«'),
          ('Артиљеријске', 'Štab artiljerijske brigade korpusa')]
DUTIES = {'команданти': 'komandant', 'командант': 'komandant', 'политички комесари': 'politički komesar',
          'политички комесар': 'politički komesar', 'начелници штаба': 'načelnik štaba',
          'замјеник команданта за корпусну војну област': 'zamjenik komandanta za korpusnu vojnu oblast',
          'замјеници команданата за дивизијску војну област': 'zamjenik komandanta za divizijsku vojnu oblast',
          'замјеник команданта за дивизијску војну област': 'zamjenik komandanta za divizijsku vojnu oblast'}
# the re-typeset page's slips ("Ђурнчковић", "Перућида", "11945")
FIX = {'Ђурнчковић': 'Ђуричковић', 'Перућида': 'Перуничић', '11945': '1945', '((': '('}
# names the book sets in a foreign order or form: the Italians' "Сесићо Марчело" is Marcello Sessico
SURNAME_FIRST = {'Сесићо Марчело'}


def lines() -> list[dict]:
    out = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            rows = {}
            for w in viewer_words(page):
                rows.setdefault(round(w['top'] / 4), []).append(w)
            for key in sorted(rows):
                ws = sorted(rows[key], key=lambda w: w['x0'])
                t = ' '.join(w['text'] for w in ws).strip()
                for a, b in FIX.items():
                    t = t.replace(a, b)
                out.append({'text': t, 'page': pno, 'x': round(ws[0]['x0'], 1), 'y': round(ws[0]['top'], 1)})
    return out


def main():
    people, order = {}, []
    staff, duty = '', ''
    for ln in lines():
        t = ln['text']
        squeezed = t.replace(' ', '')                                           # "Ш т а б 3. у д а р н е"
        head = next((v for k, v in STAFFS if k.replace(' ', '') in squeezed), None) \
            if re.match(r'^\d\s*\.\s*(?:Ш\s*т\s*а\s*б|П\s*р\s*и\s*м)', t) else None
        if head:
            staff = head
            continue
        if re.match(r'^[а-ж]\)', t):
            duty = DUTIES.get(re.sub(r'^[а-ж]\)\s*', '', t).rstrip(':').strip().lower(), duty)
            continue
        m = re.match(r'^([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)\s+([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)\s*(\(([^)]*)\))?\s*$', t)
        if not m or not staff:
            continue
        name = f'{m.group(1)} {m.group(2)}'
        given, last = (m.group(2), m.group(1)) if name in SURNAME_FIRST else (m.group(1), m.group(2))
        key = latin(f'{last} {given}')
        post = f"{staff}, {duty}" + (f" ({latin(m.group(4))})" if m.group(4) else '')
        if key not in people:
            people[key] = {'last': latin(last), 'first': latin(given), 'posts': [], 'page': ln['page'], 'x': ln['x'],
                           'y': ln['y']}
            order.append(key)
        people[key]['posts'].append(post)
    recs = []
    for no, key in enumerate(order, 1):
        p = people[key]
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f"{p['last']} {p['first']}", 'last_name': p['last'],
                     'first_name': p['first'], 'also': [], 'nick': '', 'fathers_name': '', 'birth_year': '',
                     'born_in': '', 'death_year': '', 'survived': False, 'units': [], 'no': no, 'list': TITLE,
                     'additional_info': f"{TITLE}: {p['first']} {p['last']}: {'; '.join(p['posts'])}.",
                     'pdf_file': PDF, 'pdf_page': p['page'], 'pdf_x': p['x'], 'pdf_y': p['y']})
    stats = entry_boxes.fill_boxes(recs)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} men, {sum(len(people[k]["posts"]) for k in order)} posts -> {OUT.name}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    for r in recs:
        print(f"  {r['no']:3} {r['name']}: {r['additional_info'][len(TITLE) + 2:][:160]}")


if __name__ == '__main__':
    main()
