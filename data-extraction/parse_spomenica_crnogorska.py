"""
*Spomenica crnogorskim antifašistima 1941-1945* (znaci.org 00001/193, the chapters 193_2-193_21, one per municipality,
Andrijevica to Šavnik) → website/public/pdfs/spomenica-crnogorskim-antifasistima.pdf: a book across units, used ONLY as
references for men who already have a unit record (the user's decision of 2026-10-14: the book lists the fallen fighters
and the antifascists shot or dead in camps and prisons together, with no column that tells them apart, so its unmatched
names make no records; build_ostali_borci.REFERENCE_ONLY keeps them out, and taking the book out of that set is the one
switch that would add them).

A table in Cyrillic, a row a man, under each municipality:
    Red. broj | Prezime, ime oca i ime | God. (rođenja) | Mjesto rođenja | God. smrti | Mjesto pogibije
    "1. | Асановић Н. Ђоко | 1911. | Слатина | 1944. | Морача", "14. | Бојовић Драгојев Батрић | 1916. | ..."
The father is an initial or a possessive ("Драгојев", for a woman "Јованова"); cells are often empty. Columns are read
from each page's header, else from where its year cells stand, else from the chapter's last page of the same side (the
odd and even pages sit apart); each cell goes to the row whose number is nearest. Every entry keeps its row's box.

Output: data-extraction/znaci/spomenica-crnogorskim-antifasistima-entries.json, IDs 9035xxxxxx, in the book's order.
Usage: python data-extraction/parse_spomenica_crnogorska.py [--sample N]
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
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_offset  # noqa: E402

BOOK = 'spomenica-crnogorskim-antifasistima'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
CHAPTERS = HERE / '.cache' / 'znaci_library' / 'chapters'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9035'
TITLE = 'Spomenica crnogorskim antifašistima 1941-1945'
# the chapters 193_2 ... 193_21, in the book's order
OPSTINE = ['Andrijevica', 'Bar', 'Berane', 'Bijelo Polje', 'Budva', 'Danilovgrad', 'Žabljak', 'Kolašin', 'Kotor', 'Mojkovac',
           'Nikšić', 'Plav', 'Plužine', 'Pljevlja', 'Podgorica', 'Rožaje', 'Ulcinj', 'Herceg Novi', 'Cetinje', 'Šavnik']
NUMBER = re.compile(r"^[•·'*]?\d(?:-?\d){0,3}[.,]+[,:]?$")             # "•320.", "293,", "8-96."
YEAR = re.compile(r'^1[89]\d\d\.?$')
# the page's slips (Plav 683., read from its neighbours) and the OCR's Л and Љ ("ЈТука", "ЈБубо", "Ал>о")
READ = {'Radenovnć': 'Radenović', 'JTuka': 'Luka', 'JBubo': 'Ljubo', 'Al>o': 'Aljo'}


def build_pdf() -> list[str]:
    """The site's PDF: the twenty chapters in order; the municipality of each of its pages."""
    out, opstina_of = fitz.open(), []
    for i, name in enumerate(OPSTINE, 2):
        src = fitz.open(CHAPTERS / f'00001_193_{i}.pdf')
        out.insert_pdf(src)
        opstina_of += [name] * len(src)
    if not PDF.exists():
        out.save(PDF, garbage=4, deflate=True)
    return opstina_of


def header_cols(words: list[dict]) -> dict | None:
    head = [w for w in words if w['top'] < 175 and not NUMBER.match(w['text'])]
    # the header's "Год." (not a name of the first rows: "Вујадиновић Годоров Митар", p. 367)
    god = sorted(w['x0'] for w in head if re.fullmatch(r'Год\.?', w['text']))
    name = [w['x0'] for w in head if w['text'].startswith('Презиме')]
    if len(god) < 2 or not name or god[-1] - god[0] < 60:
        return None
    by, dy = god[0], god[-1]
    mj = sorted(w['x0'] for w in head if w['text'].startswith('Мјесто'))
    bp = next((x for x in mj if by < x < dy), by + 38)
    dp = next((x for x in mj if x > dy), dy + 38)
    return {'name': name[0], 'by': by, 'bp': bp, 'dy': dy, 'dp': dp}


def data_cols(words: list[dict]) -> dict | None:
    """Without a header: the year cells stand in two columns, the names start right of the numbers."""
    xs = sorted(w['x0'] for w in words if YEAR.match(w['text']) and w['top'] > 140)
    if len(xs) < 6:
        return None
    gaps = [(b - a, i) for i, (a, b) in enumerate(zip(xs, xs[1:]))]
    gap, i = max(gaps)
    if gap < 60:
        return None
    by, dy = xs[0], xs[i + 1]
    nums = [w for w in words if NUMBER.match(w['text']) and w['x0'] < by - 100]
    if not nums:
        return None
    nx = Counter(round(w['x1']) for w in nums).most_common(1)[0][0]
    return {'name': nx + 6, 'by': by, 'bp': by + 38, 'dy': dy, 'dp': dy + 38}


def read() -> list[dict]:
    opstina_of = build_pdf()
    rows, last = [], {}
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            dx, dy = viewer_offset(page)
            words = [dict(w, x0=w['x0'] - dx, x1=w['x1'] - dx, top=w['top'] - dy, bottom=w['bottom'] - dy)
                     for w in page.extract_words(keep_blank_chars=False)]
            if not words:
                continue
            side = (opstina_of[pno - 1], pno % 2)
            cols = header_cols(words) or data_cols(words) or last.get(side)
            if not cols:
                print(f'  p{pno}: no columns', file=sys.stderr)
                continue
            last[side] = cols
            body = [w for w in words if w['top'] > (max((h['bottom'] for h in words if h['text'].startswith(('Презиме', 'смрти', 'број'))
                                                           and h['top'] < 175), default=0))]
            anchors = [w for w in body if NUMBER.match(w['text']) and w['x1'] < cols['name'] + 4]
            if not anchors:
                continue
            page_rows = [{'no': int(re.sub(r'\D', '', a['text'])), 'pdf_page': pno, 'top': a['top'],
                          'opstina': opstina_of[pno - 1], 'cells': {k: [] for k in ('name', 'by', 'bp', 'dy', 'dp')},
                          'box': [a['x0'], a['top'], a['x1'], a['bottom']]} for a in anchors]
            for w in body:
                if w in anchors or w['x1'] < cols['name'] - 2:
                    continue
                col = ('dp' if w['x0'] >= cols['dp'] - 6 else 'dy' if w['x0'] >= cols['dy'] - 6 else
                       'bp' if w['x0'] >= cols['bp'] - 6 else 'by' if w['x0'] >= cols['by'] - 6 else 'name')
                r = min(page_rows, key=lambda r: abs(r['top'] - w['top']))
                if abs(r['top'] - w['top']) > 9:
                    continue                                          # a line between rows: the page's furniture
                r['cells'][col].append(w)
                b = r['box']
                r['box'] = [min(b[0], w['x0']), min(b[1], w['top']), max(b[2], w['x1']), max(b[3], w['bottom'])]
            rows += page_rows
    return rows


def cell(ws: list[dict]) -> str:
    return cyrillic_to_latin(' '.join(w['text'] for w in sorted(ws, key=lambda w: (round(w['top'] / 4), w['x0'])))).strip(' .,;|')


def split_name(text: str) -> tuple[str, str, str, str]:
    """"Asanović N. Đoko" -> Asanović, N., Đoko; "Bojović Dragojev Batrić" -> father Dragojev; "Vujović S. Đuro-Španac"
    -> given Đuro, nick Španac; "Aleksić Mirko" -> no father. A name the page prints without its spaces is parted where
    a capital starts the next word after a surname's, father's or possessive's ending ("ДабановићЂураЗарија",
    "ОсманаТемо", "ТадићЈ.Ћурко", "М.Јована"); not at a capital the OCR set inside a word ("РадоМан", "БогиНевиН"), nor
    at its J for Љ or Њ ("ЖиваЈвевић", "НеђеЈнков"), but "ЋуровЈанко"."""
    text = re.sub(r'(?<=[a-zčćžšđ]{2}[ćvnae])(?=[A-IK-ZČĆŽŠĐ][a-zčćžšđ]|[A-ZČĆŽŠĐ]\.)|(?<=ić|ov|ev|in)(?=J[a-zčćžšđ])|'
                  r'(?<=[A-ZČĆŽŠĐ]\.)(?=[A-ZČĆŽŠĐ][a-zčćžšđ])', ' ', text)
    words = [READ.get(w, w) for w in re.split(r'\s+', text.replace('|', ' ')) if w and not re.fullmatch(r'[\W\d]+', w)]
    if not words:
        return '', '', '', ''
    last, rest = words[0], words[1:]
    father = ''
    if len(rest) >= 2:                                    # Surname Father Given: "Saveljić Nika Petar", "Asanović N. Đoko"
        father, rest = rest[0], rest[1:]
    given = rest[0] if rest else ''
    nick = ' '.join(rest[1:])
    # an initial is a letter and its full stop, the OCR's Latin X the Cyrillic Х ("Nurak Х. Džeka"); a capital the OCR
    # set inside a name is a small letter ("МилоbиН")
    if re.fullmatch(r'[A-ZČĆŽŠĐX][a-zčćžšđ]?\.?', father):
        father = father.rstrip('.').replace('X', 'H') + '.'
    fix = lambda w: w[0] + w[1:].lower() if w and '-' not in w and re.search(r'[a-zčćžšđ][A-ZČĆŽŠĐ]', w) else w
    last, given = fix(last), fix(given)
    if '-' in given and all(len(p) > 2 for p in given.split('-')):
        given, nick = given.split('-', 1)[0], (given.split('-', 1)[1] + (' ' + nick if nick else '')).strip()
    return last, father, given, nick


def year(text: str) -> str:
    m = re.search(r'\b(1[89]\d\d)\b', text)
    return m.group(1) if m else ''


def main() -> None:
    rows = read()
    recs = []
    for n, r in enumerate(rows, 1):
        c = {k: cell(v) for k, v in r['cells'].items()}
        last, father, given, nick = split_name(c['name'])
        by, dy = year(c['by']), year(c['dy'])
        parts = [f"godina rođenja {by}" if by else '', f"mjesto rođenja {c['bp']}" if c['bp'] else '',
                 f"godina smrti {dy}" if dy else '', f"mjesto pogibije {c['dp']}" if c['dp'] else '']
        info = f"{TITLE}, {r['opstina']}: " + '; '.join(p for p in parts if p)
        rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': c['name'], 'last_name': last, 'also': [], 'first_name': given,
               'nick': nick, 'fathers_name': father if re.fullmatch(r'\w\.', father) else father.rstrip('.'),
               'birth_year': by, 'born_in': ', '.join(x for x in (c['bp'], r['opstina']) if x),
               'death_year': dy, 'death_place': c['dp'], 'opstina': r['opstina'], 'no': r['no'],
               'additional_info': info, 'list': TITLE,
               'pdf_file': PDF.name, 'pdf_page': r['pdf_page'], 'pdf_x': round(r['box'][0], 1), 'pdf_y': round(r['box'][1], 1),
               'pdf_x_end': round(r['box'][2], 1), 'pdf_y_end': round(r['box'][3], 1)}
        recs.append(rec)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}')
    # the numbers run 1, 2, 3 ... within each municipality: a gap is a row the reader missed
    gaps, prev = [], None
    for r in recs:
        if prev and prev['opstina'] == r['opstina'] and r['no'] != prev['no'] + 1:
            gaps.append(f"{r['opstina']} {prev['no']}->{r['no']} (p{r['pdf_page']})")
        prev = r
    print(f'number gaps: {len(gaps)}', gaps[:30])
    print(f"by municipality: {dict(Counter(r['opstina'] for r in recs))}")
    print(f"no surname: {sum(not r['last_name'] for r in recs)}, no given: {sum(not r['first_name'] for r in recs)}, "
          f"father: {sum(bool(r['fathers_name']) for r in recs)}, birth year: {sum(bool(r['birth_year']) for r in recs)}, "
          f"death year: {sum(bool(r['death_year']) for r in recs)}")
    if '--sample' in sys.argv:
        random.seed(7)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} -> {r['last_name']}|{r['fathers_name']}|{r['first_name']}|{r['nick']} [{r['born_in']}] "
                  f"{r['birth_year']} d{r['death_year']} {r['death_place']} p{r['pdf_page']}")


if __name__ == '__main__':
    main()
