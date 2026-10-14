"""
Radojica Nenezić et al., *Dvadeset osma slavonska NO udarna divizija u sjeverozapadnoj Hrvatskoj i u dvije borbe za
oslobođenje Ludbrega* (Grubišno Polje 1990; znaci.org 00001/189, the chapters 189_2.pdf, PDF pp. 47-49, and 189_3.pdf,
PDF pp. 198-200) → website/public/pdfs/ludbreg-poginuli.pdf: the fighters who fell in the two battles for Ludbreg, a
book across units. Three lists:
    book pp. 84-85   the 17. slavonska's fighters killed in Ludbreg and at Šemovec on 3 October 1943 (15; the book
                     says ten fell in the town and five at Šemovec, and doesn't know which): "BUBAN MILAN, 1924." with
                     the birthplace and općina set apart on the right ("Zrinjska, Grubišno Polje,"), a line a man
    book p. 85       the Brigada »Braća Radić«'s fighters killed at Šemovec the same day (39, from the 32. division's
                     monograph, p. 381): "Barbarić Franjo, Vrapče, Zagreb,"
    book pp. 287-289 the 17. slavonska's fighters killed in the second battle for Ludbreg, 6 July 1944 (66), as the
                     first list
znaci.org re-typeset the book from its OCR, so the page shows its slips ("KUNDAD2IJA", "STO JAN", lost carons): the
names are read back (WORDS; a lost caron from the corpus, -IC as -IĆ) and the text gives the name so read.
The right column's lines drift a few points from their names and wrap ("Grubišno / Polje,"): a place goes to the
nearest name on its height that has none yet, else it continues the place before. One name of each page has none
(DOMIJANKO DRAGUTIN, LISAK STJEPAN). Each entry has the unit (16, or 35 for the Braća Radić, a brigade of the
32. division), the day and the place of death for the matcher; its box covers the name and the place.
Output: data-extraction/znaci/ludbreg-poginuli-entries.json, IDs 9055xxxxxx in the book's order.
Usage: python data-extraction/parse_ludbreg_poginuli.py
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
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

BOOK = 'ludbreg-poginuli'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
CACHE = HERE / '.cache' / 'ludbreg'                       # znaci.org/00001/189_2.pdf, 189_3.pdf
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9055'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'

# the site PDF's pages: (list, where its names end and the places begin)
LIST_1943, RADIC, LIST_1944 = (
    ('Spisak boraca 17. slavonske NO udarne brigade koji su poginuli u Ludbregu i Šemovcu 3. 10. 1943', [16],
     '1943-10-03', ''),
    ('Spisak boraca Brigade »Braća Radić« koji su poginuli u borbi kod Šemovca 3. 10. 1943', [35], '1943-10-03',
     'Šemovec'),
    ('Spisak boraca 17. slavonske NO udarne brigade koji su poginuli u Ludbregu 6. jula 1944', [16], '1944-07-06',
     'Ludbreg'),
)
PAGES = {1: (LIST_1943, 300), 2: (RADIC, None), 4: (LIST_1944, 295), 5: (LIST_1944, 320), 6: (LIST_1944, 290)}
BOOK_PAGE = {1: 84, 2: 85, 3: 86, 4: 287, 5: 288, 6: 289}
HEADING = re.compile(r'\b(?:SPISKOVI|SPISAK|UTVRĐENIH|BRIGADE|LUDBREGA|GODINE|PRILOZI)\b')
# the OCR's slips in names, read from the page images
WORDS = {'DRA2IC': 'DRAŽIC', 'KUNDAD2IJA': 'KUNDADŽIJA', 'KOPL.TAR': 'KOPLJAR', 'VR4ČARIĆ': 'VRAČARIĆ',
         'IŽIVKIC': 'ŽIVKIĆ', 'Bobinac.': 'Bobinac'}
# Braća Radić's lines whose words the rule can't part: (surname, given name)
NAMES = {'Novak Miško Pekar': ('Novak', 'Miško'), 'Barbarić Hajnić Jelica': ('Barbarić-Hajnić', 'Jelica'),
         'Rudi': ('', 'Rudi')}


def build_pdf() -> None:
    if not PDF.exists():
        out = fitz.open()
        out.insert_pdf(fitz.open(CACHE / '189_2.pdf'), from_page=46, to_page=48)
        out.insert_pdf(fitz.open(CACHE / '189_3.pdf'), from_page=197, to_page=199)
        out.save(PDF, garbage=4, deflate=True)


def lines_of(page) -> list[dict]:
    """The page's words in lines: each line's words left and right of the list's split are kept apart"""
    words = sorted(viewer_words(page, keep_blank_chars=False, x_tolerance=1.5), key=lambda w: (round(w['top']), w['x0']))
    rows: list[list[dict]] = []
    for w in words:
        if rows and abs(rows[-1][0]['top'] - w['top']) < 2.5:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [{'words': sorted(r, key=lambda w: w['x0']), 'top': min(w['top'] for w in r),
             'bottom': max(w['bottom'] for w in r)} for r in rows]


def spell(word: str, part: str) -> str:
    """A name in capitals in the site's spelling: the OCR's -IC and -IČ are -IĆ ("KRISTOVIČ", "ROMANIC"), a lost
    caron comes back from the corpus, and a printed Đ stays (the corpus would fold "ĐAKIC" into Dakić)"""
    w = re.sub(r'I[CČ]$', 'IĆ', word.upper())
    c = ofz._spell[part].get(w.translate(ofz.FOLD), {})
    # the spelling the site uses most that the page's letters allow (the site has slips like "Kovacević" too)
    fits = [s for s, n in sorted(c.items(), key=lambda x: -x[1]) if n >= 3 and len(s) == len(w)
            and all(a == b or (a != 'Đ' and b in ofz.LOST.get(a, '')) for a, b in zip(w, s))]
    return kl.title(fits[0]) if fits else kl.title(w)


def name_parts(text: str) -> tuple[str, str, str, str, str]:
    """'BOSNIC M. ADAM, 1928.' -> ('Bosnić', 'M.', 'Adam', '', '1928')"""
    t = ' '.join(WORDS.get(w, w) for w in text.replace('—', ' — ').split())
    t = re.sub(r'\s+—\s+(?=[' + U + '])', '-', t)                      # "UZUR — ŽESTIĆ" = Uzur-Žestić
    t = re.sub(r'\bSTO JAN\b', 'STOJAN', t)
    m = re.match(rf'^([{U}][{U}-]+)\s+(?:([{U}]{{1,2}})\.\s+)?([{U}]+(?:\s+[{U}]+)*?)'
                 rf'(?:\s+»([^«]+)«)?[,.]?\s*(?:(\d{{4}})\.?)?[\s—-]*$', t)
    if not m:
        raise ValueError(text)
    last, father, given, nick, year = m.groups()
    last = '-'.join(spell(p, 'last') for p in last.split('-'))
    given = ' '.join(spell(p, 'first') for p in given.split())
    return last, (father.title() + '.') if father else '', given, (nick or '').title(), year or ''


def read() -> list[dict]:
    out = []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            if pno not in PAGES:
                continue
            (title, units, died, place), split = PAGES[pno]
            rows = lines_of(page)
            if split is None:                                          # Braća Radić: "Surname Given, Place, ...,"
                for r in rows:
                    t = ' '.join(WORDS.get(w['text'], w['text']) for w in r['words'])
                    if not 190 < r['words'][0]['x0'] < 210 or r['top'] < 250 or not re.match(rf'[{U}][{L}]', t):
                        continue
                    t = re.sub(r'\s+,', ',', t).rstrip(',.')
                    head, _, rest = t.partition(',')
                    last, given = NAMES.get(head, (' '.join(head.split()[:-1]), head.split()[-1]))
                    out.append(dict(list=title, units=units, died=died, place=place, pno=pno, last=last, father='',
                                    given=given, nick='', year='', born=rest.strip(), printed=t,
                                    box=[r['words'][0]['x0'], r['top'], r['words'][-1]['x1'], r['bottom']]))
                continue
            names, places = [], []
            for r in rows:
                left = [w for w in r['words'] if w['x0'] < split]
                right = [w for w in r['words'] if w['x0'] >= split and w['text'] not in ('—', '-')]
                while left and left[-1]['text'] in ('—', '-'):        # the dash between the name and the place
                    left.pop()
                lt = ' '.join(w['text'] for w in left)
                rt = ' '.join(w['text'] for w in right)
                if HEADING.search(lt + ' ' + rt) or re.fullmatch(r'\d{2,3}|\d+ Dvadeset osma divizija \.?', lt):
                    continue
                if re.fullmatch(r'\d{2,3}', rt):
                    right = []                                         # the page's number
                if left and re.match(rf'^[{U}][{U}0-9.]+[ ,]', lt):
                    names.append({'text': lt, 'top': r['top'], 'tops': [r['top']], 'bottom': r['bottom'], 'x0': left[0]['x0'],
                                  'x1': left[-1]['x1'], 'place': [], 'pbox': None})
                elif left and names and r['top'] - names[-1]['bottom'] < 6 and re.match(r'^(\d{4}\.?|»)', lt):
                    # "1916." or "»BRACO«, 1924." under its name
                    names[-1]['text'] += ' ' + lt
                    names[-1]['bottom'] = r['bottom']
                    names[-1]['tops'].append(r['top'])
                    names[-1]['x1'] = max(names[-1]['x1'], left[-1]['x1'])
                elif left:
                    continue                                           # the notes before and after the list
                if right:
                    places.append({'text': ' '.join(w['text'] for w in right), 'top': r['top'], 'bottom': r['bottom'],
                                   'x0': right[0]['x0'], 'x1': right[-1]['x1']})
            last_with = None
            for p in places:
                gap = lambda n: min(abs(t - p['top']) for t in n['tops'])                      # noqa: E731
                near = [n for n in names if gap(n) < 5 and not n['place']]
                target = min(near, key=gap) if near else last_with
                if target is None:
                    continue
                target['place'].append(p['text'])
                b = target['pbox'] or [p['x0'], p['top'], p['x1'], p['bottom']]
                target['pbox'] = [min(b[0], p['x0']), min(b[1], p['top']), max(b[2], p['x1']), max(b[3], p['bottom'])]
                last_with = target
            for n in names:
                last, father, given, nick, year = name_parts(n['text'])
                born = re.sub(r'\s+', ' ', ' '.join(n['place'])).strip().rstrip(',.')
                born = re.sub(r'^\((\w+)\)\s*', '', born)                # "(Sivac) Negoslavci": the hamlet stays in the text
                box = [n['x0'], n['top'], n['x1'], n['bottom']]
                if n['pbox']:
                    box = [box[0], min(box[1], n['pbox'][1]), n['pbox'][2], max(box[3], n['pbox'][3])]
                printed = ' '.join(WORDS.get(w, w) for w in n['text'].split()).replace('STO JAN', 'STOJAN').rstrip(' —-,.') + (' — ' + ' '.join(n['place']).rstrip(',.') if n['place'] else '')
                out.append(dict(list=title, units=units, died=died, place=place, pno=pno, last=last, father=father,
                                given=given, nick=nick, year=year, born=born, printed=re.sub(r'\s+', ' ', printed),
                                box=box))
    return out


def main() -> None:
    build_pdf()
    ofz.corpus()
    recs = []
    for i, e in enumerate(read(), 1):
        name = ' '.join(x for x in (e['last'], e['father'], e['given']) if x) + (f' »{e["nick"]}«' if e['nick'] else '')
        x0, y0, x1, y1 = e['box']
        recs.append({'soldier_id': f'{PREFIX}{i:06d}', 'name': name, 'last_name': e['last'], 'first_name': e['given'],
                     'nick': e['nick'], 'fathers_name': e['father'], 'birth_year': e['year'],
                     # "Andrijaševci, Vinkovci", "Radoboj (Krapina)"; "student iz Zagreba" names no birthplace
                     'born_in': '' if ' iz ' in e['born'] else re.sub(r'\s*\((.+)\)$', r', \1', e['born']),
                     'death_year': e['died'][:4], 'death_date': e['died'],
                     'death_place': e['place'], 'units': e['units'], 'list': e['list'],
                     'additional_info': f"{e['list']}: {e['printed']}.", 'source_page': BOOK_PAGE[e['pno']],
                     'pdf_file': PDF.name, 'pdf_page': e['pno'], 'pdf_x': round(x0, 1), 'pdf_y': round(y0, 1),
                     'pdf_x_end': round(x1, 1), 'pdf_y_end': round(y1, 1)})
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    count = {}
    for r in recs:
        count[r['list'][:40]] = count.get(r['list'][:40], 0) + 1
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}: {count}')
    for r in recs:
        print(f"  {r['soldier_id']} {r['name']:32} {r['birth_year']:5} {r['born_in']:22} | {r['additional_info'][-60:]}")


if __name__ == '__main__':
    main()
