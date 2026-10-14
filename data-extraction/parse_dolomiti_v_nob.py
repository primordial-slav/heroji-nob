"""
Rudolf Hribernik - Svarun, *Dolomiti v NOB* 3 (Knjižnica NOV in POS, Ljubljana 1974; znaci.org 00003/1079.pdf, PDF
pp. 126-130) → website/public/pdfs/dolomiti-v-nob-3.pdf (book pp. 667-671): three lists at the end of the history of
the Dolomiti, the hills west of Ljubljana, and their Dolomitski odred, a book across units:
    "Narodni heroji" (16), "Nosilci spominskega znaka 1941" (the Partizanska spomenica 1941, 114) and "Padli
    prvoborci" (the first fighters who fell, 13), one column, a line each: "Bukovec Franc, 14. 3. 1910, Šmartno"
A man in two or three lists is one entry, the lists he is in named in its text, each line as printed (Dolničar
Vladimir's birth is 1919 among the heroes, 1900 among the fallen); two men of one name in one list stay two ("Miklavc
Justin, st." and his son), as do a nickname's two men (Voljč Ignac-Fric, the hero, and Voljč Ignac-Drčar). The
spomenica's list gets its other name in the text, so the record shows the medal. The OCR's l and J for 1 in the
dates are read back; one year it lost ("27. l. UHO") is left out.
Output: data-extraction/znaci/dolomiti-v-nob-3-entries.json, IDs 9056xxxxxx in the book's order, each with its box.
Usage: python data-extraction/parse_dolomiti_v_nob.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pdf_coords import viewer_words  # noqa: E402

BOOK = 'dolomiti-v-nob-3'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
SOURCE = HERE / '.cache' / 'dolomiti' / '1079.pdf'                  # znaci.org/00003/1079.pdf
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9056'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LISTS = {'NARODNI HEROJI': ('heroj', 'Narodni heroji'),
         'NOSILCI SPOMINSKEGA ZNAKA 1941': ('spomenica', 'Nosilci spominskega znaka 1941 (Partizanske spomenice 1941)'),
         'PADLI PRVOBORCI': ('padli', 'Padli prvoborci')}
BOOK_PAGE = {1: 667, 2: 668, 3: 669, 4: 670, 5: 671}
LINE = re.compile(rf'^([{U}][{L}]+(?:-[{U}][{L}]+)?)\s+(?:(?:dr|ing)\.\s+)?([{U}][{L}]+)(?:-([{U}][{L}]+))?(?:,\s*|\s+)(.*)$')


def build_pdf() -> None:
    if not PDF.exists():
        out = fitz.open()
        out.insert_pdf(fitz.open(SOURCE), from_page=125, to_page=129)
        out.save(PDF, garbage=4, deflate=True)


def date_fix(s: str) -> str:
    """"l. 6. 1920" = 1. 6. 1920; "8. J. 1913"; "lf)09" = 1909"""
    s = re.sub(r'\blf\)(\d\d)\b', r'19\1', s)
    return re.sub(r'(?<![A-Za-zčšž])[lJ](?=\.)', '1', s)


def lines() -> list[dict]:
    out, kind = [], None
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            rows: list[list[dict]] = []
            for w in sorted(viewer_words(page, keep_blank_chars=False), key=lambda w: (round(w['top']), w['x0'])):
                if rows and abs(rows[-1][0]['top'] - w['top']) < 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            for r in rows:
                r.sort(key=lambda w: w['x0'])
                t = ' '.join(w['text'] for w in r).strip()
                if t in LISTS:
                    kind = LISTS[t]
                    continue
                if re.fullmatch(r'\d{3}', t) or not kind:
                    continue
                out.append({'kind': kind, 'text': t, 'page': pno, 'x0': r[0]['x0'], 'top': min(w['top'] for w in r),
                            'x1': r[-1]['x1'], 'bottom': max(w['bottom'] for w in r)})
    return out


def main() -> None:
    build_pdf()
    entries: list[dict] = []
    seen: dict[tuple, dict] = {}
    for ln in lines():
        m = LINE.match(ln['text'])
        if not m:
            print('  not read:', ln['text'])
            continue
        last, given, nick, rest = m.groups()
        rest = date_fix(rest.strip())
        kind, title = ln['kind']
        senior = bool(re.match(r'st\.', rest))
        key = (last, given, nick, senior)
        born = re.search(r'\b\d{1,2}\.\s?\d{1,2}\.\s?((?:18|19)\d\d)\b|\b((?:18|19)\d\d)\b', rest)
        year = (born.group(1) or born.group(2)) if born else ''
        place = re.sub(r'^(?:st\.|iz)\s*', '', re.sub(r'^.*?\b(?:18|19)\d\d\b,?\s*', '', rest) if born else rest).strip(' ,')
        place = {'Vrhnike': 'Vrhnika'}.get(place, place)                 # "Popit Franc iz Vrhnike"
        if not born and re.search(r'\d', place):
            place = re.sub(r'^[^,]*,\s*', '', place)                     # "27. 1. UHO, Notranje Gorice"
        printed = f"{title}: {date_fix(ln['text'])}"
        e = seen.get(key)
        if e and kind not in e['_kinds']:
            e['_kinds'].add(kind)
            e['additional_info'] += f' {printed}.'
            if kind == 'padli':
                e['death_type'] = 'poginuo'
            continue
        name = f'{last} {given}' + (f'-{nick}' if nick else '')
        e = {'soldier_id': '', 'name': name, 'last_name': last, 'first_name': given, 'nick': nick or '',
             'fathers_name': '', 'birth_year': year, 'born_in': place, '_kinds': {kind},
             'additional_info': f'Dolomiti v NOB: {printed}.', 'source_page': BOOK_PAGE[ln['page']],
             'pdf_file': PDF.name, 'pdf_page': ln['page'], 'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1),
             'pdf_x_end': round(ln['x1'], 1), 'pdf_y_end': round(ln['bottom'], 1)}
        if kind == 'padli':
            e['death_type'] = 'poginuo'
        if kind == 'spomenica':
            e['survived'] = True                                          # a holder of the spomenica lived to have it
        seen[key] = e
        entries.append(e)
    for i, e in enumerate(entries, 1):
        e['soldier_id'] = f'{PREFIX}{i:06d}'
        kinds = e.pop('_kinds')
        if 'padli' in kinds or 'heroj' in kinds and 'spomenica' not in kinds:
            e.pop('survived', None)
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(entries)} entries -> {OUT.relative_to(HERE.parent)}')
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']:28} {e['birth_year']:5} {e['born_in']:24} | {e['additional_info'][13:110]}")


if __name__ == '__main__':
    main()
