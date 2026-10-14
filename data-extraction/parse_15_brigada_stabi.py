"""
Mile Pavlin, *Petnajsta brigada* (Ljubljana 1982; znaci.org 00003/815, the whole book's PDF pp. 447-450 →
website/public/pdfs/15-brigada-stabi.pdf, book pp. 447-450): "Seznam komandantov brigade in namestnikov, političnih
komisarjev brigade ter njihovih namestnikov oziroma pomočnikov, načelnikov brigadnega štaba ter komandantov in
političnih komisarjev bataljonov" of the 15. SNOUB (Belokranjska), a book across units: its entries are added to the
records of the officers it names, the rest go to Ostali borci (the brigade is not on the site).

Under each duty of the brigade's staff and of each battalion, a man a line, given name first, what he was called after a
hyphen, the days he held the post and, where it ended so, why:
    Ludvik Vider— od 19. marca 1945 do 16. aprila 1945 (padel)
A man in several posts is one entry with each of them, in the book's order (the same given name and surname; "Ivan
Radman-Bosanac" and "Ivan Radman" are one). A post that ended "(padel)" gives his death, on its last day.

Output: data-extraction/znaci/15-brigada-stabi-entries.json (IDs 9073xxxxxx, by each man's first post).
Usage: python data-extraction/parse_15_brigada_stabi.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from statistics import median

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = '15-brigada-stabi.pdf'
OUT = HERE / 'znaci' / '15-brigada-stabi-entries.json'
PREFIX = '9073'
BOOK_PAGE = {p: 446 + p for p in range(1, 5)}
UNIT = '15. brigada'
DUTIES = {'KOMANDANTI': 'komandant', 'POLITIČNI KOMISARJI': 'politični komisar',
          'NAMESTNIKI KOMANDANTOV': 'namestnik komandanta',
          'NAMESTNIKI-POMOČNIKI POLITIČNIH KOMISARJEV': 'namestnik oziroma pomočnik političnega komisarja',
          'NAČELNIKI ŠTABA': 'načelnik štaba'}
MONTHS = 'januarja februarja marca aprila maja junija julija avgusta septembra oktobra novembra decembra'.split()
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def lines_of(page) -> list[dict]:
    words = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
    h = median(w['bottom'] - w['top'] for w in words)
    return [{'x0': min(w['x0'] for w in ws), 'x1': max(w['x1'] for w in ws), 'top': min(w['top'] for w in ws),
             'bottom': max(w['bottom'] for w in ws), 'text': ' '.join(w['text'] for w in ws)}
            for ws in entry_boxes._cluster(words, 0.45 * h)]


def read() -> list[dict]:
    posts, unit, duty, cur = [], UNIT, None, None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for ln in lines_of(page):
                t = re.sub(r'\s+', ' ', ln['text']).strip()
                if re.fullmatch(r'\d{3}|\d+ Petnajsta brigada(?: \d{3})?', t) or t.startswith('POVELJNIŠKI KADER'):
                    continue
                b = re.fullmatch(r'(\d)\. BATALJON', t)
                if b:
                    unit, cur = f'{UNIT}, {b.group(1)}. bataljon', None
                    continue
                d = DUTIES.get(t.rstrip(':').upper())
                if d:
                    duty, cur = d, None
                    continue
                if re.match(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+ [A-ZČĆŽŠĐ]', t):
                    cur = {'unit': unit, 'duty': duty, 'text': t, 'page': pno, 'x0': ln['x0'], 'x1': ln['x1'],
                           'top': ln['top'], 'bottom': ln['bottom']}
                    posts.append(cur)
                elif cur:
                    cur['text'] += ' ' + t                         # "1944)", "(ranjen)"
                    if pno == cur['page']:
                        cur['x1'], cur['bottom'] = max(cur['x1'], ln['x1']), ln['bottom']
    return posts


def iso(day: str) -> str:
    m = re.fullmatch(r'(\d{1,2})\. (\w+) (\d{4})', day.strip())
    return f'{m[3]}-{MONTHS.index(m[2]) + 1:02d}-{int(m[1]):02d}' if m and m[2] in MONTHS else ''


def main():
    posts = read()
    people: dict[str, dict] = {}
    for p in posts:
        m = re.match(r'^(.+?)\s*(?:—|-—|\()\s*(.*)$', p['text'])
        name, rest = m.group(1).strip(), m.group(2).strip().rstrip(')').strip()
        given, _, more = name.partition(' ')
        last, _, nick = more.partition('-')
        when = re.sub(r'\s*\)\s*\(', ', ', rest)                   # "(od ... 1944) (ranjen)" -> "od ... 1944, ranjen"
        when = re.sub(r'\s*\(', ', ', when).replace('(', '').replace(')', '')
        k = (given + ' ' + last).translate(FOLD).lower()
        e = people.setdefault(k, {'given': given, 'last': last, 'nick': '', 'posts': [], 'first': p, 'death': ''})
        e['nick'] = e['nick'] or nick
        if 'č' in last or 'ć' in last:
            e['last'] = last                                      # "Božic" and "Božič": the one with the caron
        e['posts'].append(f"{p['unit']}, {p['duty']} ({when})")
        if 'padel' in when:
            end = re.search(r'(\d{1,2}\. \w+ \d{4})\W*padel', when)
            e['death'] = iso(end.group(1)) if end else ''
    recs = []
    for no, e in enumerate(sorted(people.values(), key=lambda e: posts.index(e['first'])), 1):
        p = e['first']
        text = f"{'; '.join(e['posts'])}."
        recs.append({'soldier_id': f'{PREFIX}{no:06d}',
                     'name': f"{e['last']} {e['given']}" + (f" — {e['nick']}" if e['nick'] else ''),
                     'last_name': e['last'], 'first_name': e['given'], 'also': [], 'nick': e['nick'],
                     'fathers_name': '', 'birth_year': '', 'born_in': '', 'death_year': e['death'][:4],
                     'death_date': e['death'], 'death_type': 'poginuo' if e['death'] else '',
                     'survived': not e['death'], 'units': [], 'no': no, 'list': 'Poveljniški kader 15. brigade',
                     'additional_info': f'Poveljniški kader 15. brigade: {text}', 'source_page': BOOK_PAGE[p['page']],
                     'pdf_file': PDF, 'pdf_page': p['page'], 'pdf_x': round(p['x0'], 1), 'pdf_y': round(p['top'], 1),
                     # his first post's lines (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(p['x1'], 1), 'pdf_y_end': round(p['bottom'], 1)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(posts)} posts, {len(recs)} men -> {OUT.relative_to(HERE.parent)}')
    for r in recs:
        print(f"  {r['no']:3} {r['name']} {r['death_date']}: {r['additional_info'][29:190]}")


if __name__ == '__main__':
    main()
