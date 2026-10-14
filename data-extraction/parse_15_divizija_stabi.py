"""
Lado Ambrožič-Novljan, *Petnajsta divizija* (znaci.org 00003/770, the whole book's PDF pp. 576-577 →
website/public/pdfs/15-divizija-stabi.pdf, book pp. 583-584): "Seznam poveljniške sestave 15. divizije", the 15.
divizija NOV in POS's commanders, political commissars, deputies and chiefs of staff, after Klanjšček's list of the NOV
in POS's command, a book across units: its entries are added to the records of the officers it names, the rest go to
Ostali borci (the division is not on the site).

A table: the name on the left, given name first and what he was called after a hyphen ("Franc Kočevar-Ciril"), the
days on the right of the same row; a long name breaks over two or three rows ("Aleksandar / Maijanovič- / Leko") and a
second span of days continues on the next ("... in od / 12. oktobra 1944 do konca januarja 1945"). A man in several
posts is one entry with each of them. The text layer's slips are mended (`FIX`).

Output: data-extraction/znaci/15-divizija-stabi-entries.json (IDs 9074xxxxxx, by each man's first post).
Usage: python data-extraction/parse_15_divizija_stabi.py
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
from pdf_coords import viewer_words  # noqa: E402

PDF = '15-divizija-stabi.pdf'
OUT = HERE / 'znaci' / '15-divizija-stabi-entries.json'
PREFIX = '9074'
BOOK_PAGE = {1: 583, 2: 584}
DUTIES = {'Komandanti': 'komandant', 'Politični komisarji': 'politični komisar',
          'Namestniki komandanta': 'namestnik komandanta',
          'Namestnika političnega komisarja': 'namestnik političnega komisarja',
          'Pomočnik političnega komisarja': 'pomočnik političnega komisarja', 'Načelniki štaba': 'načelnik štaba'}
# (the page prints the Serbs' and Montenegrins' -ić, which the text layer reads as -ič)
FIX = {'julya': 'julija', 'juljja': 'julija', 'junya': 'junija', 'Maijanovič': 'Marjanović', 'Jevtic': 'Jevtić',
       'Tanaskovič': 'Tanasković', 'Božovič': 'Božović', 'Vojnovič': 'Vojnović'}
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def fix(t: str) -> str:
    for a, b in FIX.items():
        t = t.replace(a, b)
    return t


def read() -> list[dict]:
    posts, duty, name, start = [], None, '', None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            ws = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
            for ln in entry_boxes._cluster(ws, 4):
                t = fix(' '.join(w['text'] for w in ln)).rstrip('*').strip()
                x0, x1 = ln[0]['x0'], max(w['x1'] for w in ln)
                top, bottom = min(w['top'] for w in ln), max(w['bottom'] for w in ln)
                if t in DUTIES:
                    duty, name = DUTIES[t], ''
                    continue
                if not duty or re.fullmatch(r'\d{3}', t) or t.startswith(('*', 'vojne na Slovenskem')):
                    continue
                if re.match(r'\d', t) and posts:                  # the second span of days
                    posts[-1]['when'] += ' ' + t
                    continue
                m = re.match(r'^(.*?)\s*\b(od .*)$', t)
                if not m:                                         # a name broken over rows
                    name, start = (name + (' ' if name and not name.endswith('-') else '') + t), start or (pno, x0, top)
                    continue
                full = name + (' ' if name and not name.endswith('-') else '') + m.group(1)
                where = start or (pno, x0, top)
                posts.append({'duty': duty, 'name': full.strip(), 'when': m.group(2), 'page': where[0], 'x0': where[1],
                              'top': where[2], 'x1': x1, 'bottom': bottom})
                name, start = '', None
    return posts


def main():
    posts = read()
    people: dict[str, dict] = {}
    for p in posts:
        given, _, more = p['name'].partition(' ')
        last, _, nick = more.partition('-')
        k = (given + ' ' + last).translate(FOLD).lower()
        e = people.setdefault(k, {'given': given, 'last': last, 'nick': nick, 'posts': [], 'first': p})
        e['posts'].append(f"15. divizija, {p['duty']} ({p['when']})")
    recs = []
    for no, e in enumerate(sorted(people.values(), key=lambda e: posts.index(e['first'])), 1):
        p = e['first']
        recs.append({'soldier_id': f'{PREFIX}{no:06d}',
                     'name': f"{e['last']} {e['given']}" + (f" — {e['nick']}" if e['nick'] else ''),
                     'last_name': e['last'], 'first_name': e['given'], 'also': [], 'nick': e['nick'],
                     'fathers_name': '', 'birth_year': '', 'born_in': '', 'death_year': '', 'death_date': '',
                     'survived': True, 'units': [], 'no': no, 'list': 'Seznam poveljniške sestave 15. divizije',
                     'additional_info': f"Poveljniška sestava 15. divizije: {'; '.join(e['posts'])}.",
                     'source_page': BOOK_PAGE[p['page']], 'pdf_file': PDF, 'pdf_page': p['page'],
                     'pdf_x': round(p['x0'], 1), 'pdf_y': round(p['top'], 1),
                     # his first post's row (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(p['x1'], 1), 'pdf_y_end': round(p['bottom'], 1)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(posts)} posts, {len(recs)} men -> {OUT.relative_to(HERE.parent)}')
    for r in recs:
        print(f"  {r['no']:3} {r['name']}: {r['additional_info'][34:200]}")


if __name__ == '__main__':
    main()
