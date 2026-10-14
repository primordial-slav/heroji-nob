"""
Vinko Antić, *Vinodolska Selca u borbi* (znaci.org 00003/793, PDF pp. 710-721, the Prilozi's pp. IV-XVII) →
website/public/pdfs/vinodolska-selca.pdf: the fighters of Selce, a book across units.

Two lists go in:
  "Popis poginulih boraca iz Selaca u toku NOB-a": four entries a page, two by two between the photographs of the
  memorial, each a short bio: "ANTIĆ Andrije ANDRIJA, politički delegat u 13. proleterskoj brigadi, rođen 20. X 1914.
  u Selcima, poginuo 1. I 1943. u Žumberku." The text layer runs the two columns into one line and sometimes sets a
  bio's last line apart, so the page's words are grouped into blocks by the gaps between them, and a block that
  begins with no name runs on from the block above it in its column.
  "Prvoborci i nosioci »Partizanske spomenice 1941«": sixteen, numbered, "1. ANTIĆ Mate EMIL, rođen 6. X 1910."
The other lists stay out: "Organizirani učesnici NOB-a" gives names and births only and counts the AFŽ's women and
the NOO's men with the fighters (the mixed-list rule finds no fighter in it), those executed in camps as NOP
collaborators, and the victims of terror.
Output: data-extraction/znaci/vinodolska-selca-entries.json, IDs 9052xxxxxx, each with its box.
Usage: python data-extraction/parse_vinodolska_selca.py
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
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

BOOK = 'vinodolska-selca'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9052'
FIRST, LAST = 710, 721                     # the whole book's PDF pages: the fallen (710-717) to the spomenica (721)
FALLEN, SPOMENICA = range(1, 9), 12        # the site PDF's pages
TITLES = {'fallen': 'Popis poginulih boraca iz Selaca u toku NOB-a',
          'spomenica': 'Prvoborci i nosioci »Partizanske spomenice 1941«'}
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# "ANTIĆ Andrije ANDRIJA,", "ANTIĆ Jur ja IVAN," (the OCR's space), "LONČARIĆ Mihovila ALEKSAN-" (the name runs on)
NAME = re.compile(rf'^(?:(\d{{1,2}})\.\s*)?([{U}][{U}]+(?:-[{U}]+)?)\s+([{U}][{L}]+(?:\s?[{L}]+)?(?:\s+[{U}][{L}]+)?)\s+'
                  rf'([{U}][{U}\s]+?)\s*(?:,|[\xad-]\s*$)')
# a bio's last line the text layer sets apart, above the page's other entries: the entry it ends (by its given name)
MOVED = {'1944. na planini Motajica.': 'BOŽIDAR'}
DEATH = re.compile(r'\b(?:pogi|pognu|obješ|smrznut|ubijen|strijelj|umr|nesta|stradal)\w*.{0,60}?\b(19[34]\d)\b')
UNITS = [(r'13\.\s*proletersk', 6), (r'\b(?:13\.\s*)?primorsko-?\s*goransk\w*\s+(?:udarn\w*\s+)?divizij', 0),
         (r'\b3\.\s*brigad\w*\s+13\.\s*primorsko', 99), (r'\b14\.\s*primorsko', 95), (r'brodsk\w+\s+udarn\w+\s+brigad', 30),
         (r'12\.\s*proletersk\w*\s+(?:slavonsk|brigad)', 146)]


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_793.pdf'), fitz.open()
        out.insert_pdf(src, from_page=FIRST - 1, to_page=LAST - 1)
        out.save(PDF, garbage=4, deflate=True)


def blocks(page) -> list[dict]:
    """The page's words in runs: a line's words parted where the gap between two is wider than a few spaces"""
    runs = []
    for w in sorted(viewer_words(page), key=lambda w: (round(w['top'] / 3), w['x0'])):
        last = runs[-1] if runs else None
        if last and abs(w['top'] - last['top']) < 4 and 0 <= w['x0'] - last['x1'] < 22:
            last['text'] += ' ' + w['text']
            last['x1'] = w['x1']
        else:
            runs.append({'text': w['text'], 'x0': w['x0'], 'x1': w['x1'], 'top': w['top']})
    return runs


def fallen(pdf) -> list[dict]:
    entries, moved = [], []
    for pno in FALLEN:
        runs = sorted(blocks(pdf.pages[pno - 1]), key=lambda r: (r['top'], r['x0']))
        page = []
        for r in runs:
            t = r['text'].strip()
            if re.fullmatch(r'[IVXL]+|POPIS POGINULIH.*|SREDIŠNI DIO.*|NIMA PALIH BORACA', t):
                continue
            if t in MOVED:
                moved.append((MOVED[t], t))
                continue
            if NAME.match(t.replace('\xad', '-')):
                page.append({'lines': [t], 'pdf_page': pno, 'pdf_x': round(r['x0'], 1), 'pdf_y': round(r['top'], 1),
                             'x0': r['x0'], 'bottom': r['top']})
                continue
            # a line of a bio: the entry above it in its column (its left edge within a column's width)
            near = [e for e in page if abs(e['x0'] - r['x0']) < 60 and -6 < r['top'] - e['bottom'] < 40]
            if near:
                e = min(near, key=lambda e: r['top'] - e['bottom'])
                e['lines'].append(t)
                e['bottom'] = r['top']
            else:
                print(f'  p{pno + FIRST - 1} not placed: {t!r}')
        entries += page
    for given, t in moved:
        next(e for e in entries if NAME.match(e['lines'][0]).group(4).strip() == given)['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        ln = ln.replace('\xad', '-')
        if re.search(r'-$', text) and (re.match(rf'[{L}]', ln) or re.search(rf'[{U}]{{2}}-$', text) and re.match(rf'[{U}]', ln)):
            text = text[:-1] + ln                            # "pogi-" "nuo", "ALEKSAN-" "DAR"
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def record(text: str, kind: str, e: dict, n: int) -> dict:
    m = NAME.match(text)
    last, father, given = m.group(2), m.group(3).replace(' ', ''), m.group(4).replace(' ', '')
    by = re.search(r'ro\s?đen\w*,?\s+(?:\d{1,2}\.\s*[IVXLvr]+\s*|\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', text)
    dy = DEATH.search(text)
    where = re.search(rf'\b(?:19[34]\d)\.?\s*(?:godine\s+)?(?:u|kod|na|kraj)\s+(?:planini\s+)?((?:[{U}][{L}]+\s?)+)', text[dy.end() - 4:]) if dy else None
    return {'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{kl.title(last)} {kl.title(given)}', 'last_name': kl.spelled(last, 'last'),
            'also': [], 'first_name': kl.spelled(given, 'first'), 'nick': '', 'fathers_name': father,
            'birth_year': by.group(1) if by else '', 'born_in': 'Selce, Crikvenica',
            'death_year': dy.group(1) if dy and kind == 'fallen' else '',
            'death_place': where.group(1).strip() if where and kind == 'fallen' else '',
            'units': sorted({c for p, c in UNITS if c and re.search(p, text, re.I)}),
            'additional_info': f'{TITLES[kind]}: {text}', 'list': TITLES[kind],
            'pdf_file': PDF.name, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']}


def main() -> None:
    build_pdf()
    ofz.corpus()
    out, n = [], 0
    with pdfplumber.open(PDF) as pdf:
        for e in fallen(pdf):
            n += 1
            out.append(record(join(e['lines']), 'fallen', e, n))
        for ln in entry_boxes.read_page(pdf.pages[SPOMENICA - 1])['columns'][0]:
            m = re.match(r'^(\d{1,2})\.\s', ln['text'])
            if m and NAME.match(ln['text']):
                n += 1
                out.append(record(ln['text'].strip(), 'spomenica', {'pdf_page': SPOMENICA, 'pdf_x': round(ln['x0'], 1),
                                                                    'pdf_y': round(ln['top'], 1)}, n))
    stats = entry_boxes.fill_boxes(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{sum(r['list'] == TITLES['fallen'] for r in out)} fallen, {sum(r['list'] == TITLES['spomenica'] for r in out)} "
          f"spomenica -> {OUT.relative_to(HERE.parent)}; boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    for r in out:
        print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} {r['birth_year']} † {r['death_year']} {r['death_place']!r} {r['units']} | {r['additional_info'][len(r['list']) + 2:][:80]}")


if __name__ == '__main__':
    main()
