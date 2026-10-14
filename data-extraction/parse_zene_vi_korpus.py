"""
*Žene Hrvatske u narodnooslobodilačkoj borbi* (znaci.org 00003/585), dokument 427: the VI. korpus staff's "Popis
poginulih drugarica-boraca i rukovodioca u jedinicama na području Štaba VI. korpusa NOVJ" of 23 December 1944 (PDF pp.
298-309, book pp. 301-312) → website/public/pdfs/zene-vi-korpus-poginule.pdf: the women fighters and officers of the
Slavonian units who fell, a book across units.

A table: number, duty and unit ("bolničarka", "Borac XII. Udarne Brigade"), name, year of birth, birthplace (village,
općina, srez), when and in what fight she fell, note. A row's cells stand around its number, above and below it, so
a row takes the band halfway to the next number's; the columns are found by each page's headers. A duty or a death
given as "isto" or a ditto mark ("„", "»", which the OCR reads as 33, 55, 53) is the row's above.
Output: data-extraction/znaci/zene-vi-korpus-poginule-entries.json, IDs 9054xxxxxx, each with its box.
Usage: python data-extraction/parse_zene_vi_korpus.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

BOOK = 'zene-vi-korpus-poginule'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9054'
FIRST, LAST = 298, 309
TITLE = 'Popis poginulih drugarica-boraca i rukovodioca u jedinicama VI. korpusa NOVJ (23. XII 1944)'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NAMES = {67: ('Bakić Marija', 'Borac Bilogor. Odreda'), 85: ('Šlapar Marija', 'Borac Omladinske Brigade Hrvatske u NOB')}
UNNAMED = {23}                                                    # "? Jelena": her surname not known
DITTO = re.compile(r'^(?:[„"»«]+|3\s?3|5\s?5|5\s?3|isto|Isto)$')
# the units the duty names, by the brigade's roman number ("Borac XII. Udarne Brigade", "Omladinske Brigade")
UNITS = [(r'\bXII\.?\s*(?:Ud|Pr|Brig)', 146), (r'\bXVI\.?\s*(?:Ud|Om|Brig)|Omladinsk', 37), (r'\bXVII\.?\s*(?:Ud|Brig)', 16),
         (r'\bXVIII\.?\s*(?:Ud|Brig)', 17), (r'\bXXI\.?\s*(?:Ud|Brig)', 34), (r'\bXXV\.?\s*(?:Ud|Brig)|[Bb]rodsk', 30),
         (r'Osječk', 104)]


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_585.pdf'), fitz.open()
        out.insert_pdf(src, from_page=FIRST - 1, to_page=LAST - 1)
        out.save(PDF, garbage=4, deflate=True)


def number(t: str) -> int | None:
    t = t.replace(' ', '').translate(str.maketrans('Ilio', '1110')).replace('O', '0')     # "l i" 11, "6o" 60
    return int(t) if re.fullmatch(r'\d{1,3}', t) else None


def headers(words: list[dict]) -> dict:
    """Each header's left edge, found by its letters along a line: the OCR sets some headers a letter a word
    ("R e d .", "G o d .", "M j e s t o ,")"""
    found = {}
    lines: dict[int, list[dict]] = {}
    for w in words:
        if w['top'] < 400:
            lines.setdefault(round(w['top'] / 4), []).append(w)
    for ws in lines.values():
        ws.sort(key=lambda w: w['x0'])
        s, xs = '', []
        for w in ws:
            s += w['text']
            xs += [w['x0']] * len(w['text'])
        for key in ('Red.', 'PREZIME', 'God.', 'Mjesto', 'Kada', 'Opaska'):
            i = s.find(key)
            if i >= 0 and key not in found:
                found[key] = {'x0': xs[i], 'top': ws[0]['top']}
    return found


def read(pdf) -> list[dict]:
    rows = []
    for pno, page in enumerate(pdf.pages, 1):
        words = viewer_words(page)
        head = headers(words)
        if len(head) < 6:
            print(f'  p{pno + FIRST - 1}: headers not found ({sorted(head)})')
            continue
        top = max(w['top'] for w in head.values()) + 12
        num_x = head['Red.']['x0'] + 22
        cols = [('duty', num_x), ('name', head['PREZIME']['x0'] - 15), ('year', head['God.']['x0'] - 6),
                ('place', head['Mjesto']['x0'] - 4), ('death', head['Kada']['x0'] - 6), ('note', head['Opaska']['x0'] - 8)]
        body = sorted((w for w in words if w['top'] > top), key=lambda w: (round(w['top']), w['x0']))
        # the rows' numbers, read in the number column (the OCR's "I" and "l i" for 1 and 11)
        marks = []
        for w in body:
            if w['x0'] < num_x:
                if marks and abs(marks[-1]['top'] - w['top']) < 3:
                    marks[-1]['text'] += ' ' + w['text']
                    continue
                marks.append(dict(w))
        # a number the OCR garbled past reading ("no" for 110, '"5' for 115) is the one between its neighbours
        nums = [number(m['text']) for m in marks]
        for i, n in enumerate(nums):
            if n is None and 0 < i < len(nums) - 1 and nums[i - 1] is not None and nums[i + 1] == nums[i - 1] + 2:
                nums[i] = nums[i - 1] + 1
                marks[i]['text'] = str(nums[i])
        marks = [m for m, n in zip(marks, nums) if n is not None]
        for i, m in enumerate(marks):
            lo = (marks[i - 1]['top'] + m['top']) / 2 if i else top
            # the page's last row as far below its number as the rows reach (the table's end is followed by prose)
            hi = (m['top'] + marks[i + 1]['top']) / 2 if i + 1 < len(marks) else m['top'] + 22
            cells = {c: [] for c, _ in cols}
            for w in body:
                if lo <= w['top'] < hi and w['x0'] >= num_x:
                    col = [c for c, x in cols if w['x0'] >= x]
                    cells[col[-1]].append(w)
            rows.append({'no': number(m['text']), 'cells': cells, 'pdf_page': pno, 'pdf_x': round(m['x0'], 1),
                         'pdf_y': round(min([m['top']] + [w['top'] for ws in cells.values() for w in ws]), 1)})
    return rows


def text(ws: list[dict]) -> str:
    out = ''
    for w in sorted(ws, key=lambda w: (round(w['top'] / 3), w['x0'])):
        t = w['text']
        if out.endswith('-') and t[:1].islower():
            out = out[:-1] + t
        else:
            out += (' ' if out else '') + t
    return re.sub(r'\s+', ' ', out).strip()


def main() -> None:
    build_pdf()
    with pdfplumber.open(PDF) as pdf:
        rows = read(pdf)
    out, last_duty, last_death = [], '', ''
    for n, r in enumerate(rows, 1):
        c = {k: text(v) for k, v in r['cells'].items()}
        # a ditto mark beside a duty ("55 Borac Brodske Brigade", "ml. vodnik 33") is the OCR's: the duty stands alone
        rest = ' '.join(t for t in c['duty'].split() if not re.fullmatch(r'[„"»«>]*\d{2}|[„"»«>]+\d?', t))
        duty = last_duty if not rest or DITTO.match(rest) else rest
        death = last_death if DITTO.match(c['death'] or '') else c['death']
        last_duty, last_death = duty, death
        name = re.sub(r'\d+$', '', c['name']).strip()             # "Ostojić Bosiljka1": a footnote's number
        if r['no'] in NAMES:                                      # a word of the duty set into the name's column
            name, duty = NAMES[r['no']]
        ws = name.split()
        father = ws.pop(1) if len(ws) > 2 and re.fullmatch(rf'[{U}]\.', ws[1]) else ''    # "Marić I. Borka"
        last, first = (ws[0], ' '.join(ws[1:])) if len(ws) > 1 else ('', name)
        y = re.search(r'1[89]\d\d', c['year'])
        dy = re.search(r'19[34]\d', death)
        dplace = re.search(rf'\b(?:u|kod|na)\s+(?:borbi\s+)?(?:u|kod|na)?\s*((?:[{U}][{L}]+\.?\s?)+)', death)
        info = ', '.join(x for x in (f'{duty} {name}'.strip(), y.group(0) if y else '', c['place'], death, c['note']) if x)
        out.append({'soldier_id': f'{PREFIX}{n:06d}', 'name': name, 'last_name': last, 'also': [], 'first_name': first,
                    'nick': '', 'fathers_name': father, 'birth_year': y.group(0) if y else '', 'born_in': c['place'],
                    'death_year': dy.group(0) if dy else '', 'death_place': dplace.group(1).strip() if dplace else '',
                    'units': sorted({code for p, code in UNITS if re.search(p, duty)}), 'no': r['no'],
                    'additional_info': f'{TITLE}: {info}', 'list': TITLE,
                    'pdf_file': PDF.name, 'pdf_page': r['pdf_page'], 'pdf_x': r['pdf_x'], 'pdf_y': r['pdf_y']})
        if r['no'] in UNNAMED:
            out[-1]['unnamed'] = True
    stats = entry_boxes.fill_boxes(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    nums = [r['no'] for r in rows]
    gaps = [f'{a}->{b}' for a, b in zip(nums, nums[1:]) if b != a + 1]
    print(f'{len(out)} women -> {OUT.relative_to(HERE.parent)}; numbers {nums[:1]}..{nums[-1:]}, gaps {gaps}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}; birth year {sum(bool(r['birth_year']) for r in out)}, "
          f"death year {sum(bool(r['death_year']) for r in out)}, a unit {sum(bool(r['units']) for r in out)}")
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(out, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['no']} {r['last_name']}|{r['first_name']} {r['birth_year']} [{r['born_in']}] † {r['death_year']} {r['death_place']!r} {r['units']} | {r['additional_info'][len(TITLE) + 2:][:100]}")


if __name__ == '__main__':
    main()
