"""
Mile Pavlin, *Jeseniško-bohinjski odred* (znaci.org 00003/771, the whole book's PDF pp. 354-356 →
website/public/pdfs/jb-odred-stabi.pdf, book pp. 354-356): "Seznam štabov", the commanders, political commissars, their
assistants and deputies and the chief of staff of the odred, of its three battalions and of its school camp
(August 1944 - May 1945), a book across units: its entries are added to the records of the officers it names, the rest
go to Ostali borci (the odred is not on the site).

The name on one line, given name first and what he was called after a hyphen, the days on the next, and why the post
ended where it says ("od 4. decembra 1944 do 6. decembra 1944 (ujet)"). A man in several posts is one entry with each of
them; the text layer's slips are mended (`FIX`).

Output: data-extraction/znaci/jb-odred-stabi-entries.json (IDs 9075xxxxxx, by each man's first post).
Usage: python data-extraction/parse_jb_odred_stabi.py
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

PDF = 'jb-odred-stabi.pdf'
OUT = HERE / 'znaci' / 'jb-odred-stabi-entries.json'
PREFIX = '9075'
BOOK_PAGE = {1: 354, 2: 355, 3: 356}
ODRED = 'Jeseniško-bohinjski odred'
UNITS = {'odredni Stab': f'{ODRED}, štab odreda', 'ŠOLSKO TABORIŠCE': f'{ODRED}, šolsko taborišče'}
DUTIES = {'komandanti': 'komandant', 'komandant': 'komandant', 'politična komisarja': 'politični komisar',
          'politični komisarji': 'politični komisar', 'politični komisar': 'politični komisar',
          'pomoćnika političnih komisarjev': 'pomočnik političnega komisarja',
          'namestnik komandanta': 'namestnik komandanta', 'načelnik štaba': 'načelnik štaba'}
FIX = {'Anton Znidar': 'Anton Žnidar', 'Karei Rozman': 'Karel Rozman', 'Anton Turk:': 'Anton Turk'}
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def read() -> list[dict]:
    posts, unit, duty, pending = [], None, None, None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            ws = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
            for ln in entry_boxes._cluster(ws, 4):
                t = ' '.join(w['text'] for w in ln).strip()
                for a, b in FIX.items():
                    t = t.replace(a, b)
                x0, x1 = ln[0]['x0'], max(w['x1'] for w in ln)
                top, bottom = min(w['top'] for w in ln), max(w['bottom'] for w in ln)
                if re.fullmatch(r'\d{3}', t):
                    continue
                b = re.fullmatch(r'(\d)\. BATALJON', t)
                if t in UNITS or b:
                    unit, duty = (UNITS[t] if t in UNITS else f'{ODRED}, {b.group(1)}. bataljon'), None
                    continue
                d = DUTIES.get(re.sub(r'\s*:$', '', t).lower())
                if d:
                    duty = d
                    continue
                if t.startswith('od ') and pending:
                    posts.append({**pending, 'when': t.replace('(', '').replace(')', ''), 'x1': max(pending['x1'], x1),
                                  'bottom': bottom})
                    pending = None
                elif unit and duty:
                    pending = {'unit': unit, 'duty': duty, 'name': t, 'page': pno, 'x0': x0, 'x1': x1, 'top': top}
    return posts


def main():
    posts = read()
    people: dict[str, dict] = {}
    for p in posts:
        given, _, more = p['name'].partition(' ')
        last, _, nick = more.partition('-')
        k = (given + ' ' + last).translate(FOLD).lower()
        e = people.setdefault(k, {'given': given, 'last': last, 'nick': nick, 'posts': [], 'first': p})
        e['posts'].append(f"{p['unit']}, {p['duty']} ({p['when']})")
    recs = []
    for no, e in enumerate(sorted(people.values(), key=lambda e: posts.index(e['first'])), 1):
        p = e['first']
        recs.append({'soldier_id': f'{PREFIX}{no:06d}',
                     'name': f"{e['last']} {e['given']}" + (f" — {e['nick']}" if e['nick'] else ''),
                     'last_name': e['last'], 'first_name': e['given'], 'also': [], 'nick': e['nick'],
                     'fathers_name': '', 'birth_year': '', 'born_in': '', 'death_year': '', 'death_date': '',
                     'survived': True, 'units': [], 'no': no, 'list': 'Seznam štabov Jeseniško-bohinjskega odreda',
                     'additional_info': f"Štabi Jeseniško-bohinjskega odreda: {'; '.join(e['posts'])}.",
                     'source_page': BOOK_PAGE[p['page']], 'pdf_file': PDF, 'pdf_page': p['page'],
                     'pdf_x': round(p['x0'], 1), 'pdf_y': round(p['top'], 1),
                     # his name and his first post's days (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(p['x1'], 1), 'pdf_y_end': round(p['bottom'], 1)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(posts)} posts, {len(recs)} men -> {OUT.relative_to(HERE.parent)}')
    for r in recs:
        print(f"  {r['no']:3} {r['name']}: {r['additional_info'][36:220]}")


if __name__ == '__main__':
    main()
