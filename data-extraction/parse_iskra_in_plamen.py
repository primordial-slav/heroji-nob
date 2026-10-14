"""
Marjan Moškrič (ed.), *Iskra in plamen* 3 (znaci.org bk=1096, the whole book 00003/1096.pdf, PDF pp. 170-212: "Svoja
življenja so dali za svobodo", the dead of the villages of the old municipality of Polje, north-east Ljubljana) →
website/public/pdfs/iskra-in-plamen-padli.pdf: a book across units, fighters only.

Village by village under a heading in capitals ("BIZOVIK"; several villages together over two lines), four lists:
"padli v NOV" (fell in the army), "umrli v internaciji in zaporih", "talci", "ostale žrtve". Only the first goes in (the
user's rule for lists of fighters and civilians together: the book parts them). Two columns, numbered, each entry
hanging: "1. Anžič Ivan, 1920-1942, neznano kje, zidar" (surname, given name, the years of birth and death, where he fell,
his trade). The OCR reads a number's 1 as l or I ("l.", "JO.", "l l.") and a small diacritic first letter ("škrlj").

Output: data-extraction/znaci/iskra-in-plamen-padli-entries.json, IDs 9039xxxxxx, each with its box (entry_boxes).
Usage: python data-extraction/parse_iskra_in_plamen.py [--sample N]
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
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402

BOOK = 'iskra-in-plamen-padli'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9039'
TITLE = 'Svoja življenja so dali za svobodo (Iskra in plamen 3), padli v NOV'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
START = re.compile(rf'^([\dlIJO](?:\s?[\dlIJO]){{0,2}})\s?[.,]\s+(?=[{U}]|[šžčćđ][{L}])')
SECTION = re.compile(r'^(padli v NO[VTY/]+|umrli v internaciji|talci$|ostale žrtve)', re.I)


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_1096.pdf'), fitz.open()
        out.insert_pdf(src, from_page=169, to_page=211)
        out.save(PDF, garbage=4, deflate=True)


def number(s: str) -> int:
    return int(s.replace(' ', '').replace('l', '1').replace('I', '1').replace('J', '1').replace('O', '0'))


def is_heading(t: str) -> bool:
    return (bool(re.fullmatch(rf'[{U}][{U}{L}\s,.\-]+', t)) and not START.match(t)
            and sum(c.isupper() for c in t) > 0.6 * sum(c.isalpha() for c in t))


def unspace(t: str) -> str:
    """"Br g l e z S t a n e" -> "Brglez Stane": letters the OCR spaced out joined, the words parted at the capitals"""
    def join(m):
        s = m.group(0).replace(' ', '')
        return re.sub(rf'(?<=[{L}])(?=[{U}])', ' ', s)
    return re.sub(rf'(?<!\S)(?:[{U}{L}]{{1,2}} ){{2,}}[{U}{L}]{{1,2}}(?!\S)', join, t)


def ordered(data: dict) -> list[dict]:
    """The page's lines in reading order: a village heading set across both columns parts the page into bands, and
    each band is read left column first, then right"""
    left, right = data['columns'][0], data['columns'][1] if len(data['columns']) > 1 else []
    split = data.get('split') if isinstance(data.get('split'), (int, float)) else None
    # a heading set across both columns: in halves, one in each, or one line over the gutter ("HRUŠICA-FUŽINE")
    across = [l for l in left + right if is_heading(l['text'].strip()) and split is not None
              and l['x0'] < split - 5 and l.get('x1', 0) > split + 5]
    # or one set in a single column whose list starts in the other column just below it ("HRASTJE, OBRIJE" on the
    # right, its "padli v NOV" on the left)
    for here, there in ((left, right), (right, left)):
        for h in here:
            if is_heading(h['text'].strip()) and not any(h is a for a in across) and any(
                    SECTION.match(o['text'].strip()) and 0 < o['top'] - h['top'] < 60 for o in there):
                across.append(h)
    cuts = sorted({round(l['top']) for l in left if is_heading(l['text'].strip())
                   if any(abs(r['top'] - l['top']) < 4 and is_heading(r['text'].strip()) for r in right)}
                  | {round(l['top']) for l in across})
    bands = [float('-inf')] + [c - 2 for c in cuts] + [float('inf')]
    left = [l for l in left if not any(l is a for a in across)]
    right = [r for r in right if not any(r is a for a in across)]
    # a heading's right half goes straight after its left half, not after the left column's entries
    partner = {id(r): l for r in right for l in left if is_heading(r['text'].strip()) and is_heading(l['text'].strip())
               and abs(r['top'] - l['top']) < 4}
    halves = {id(l): r for r in right for l in [partner.get(id(r))] if l is not None}
    out = []
    for lo, hi in zip(bands, bands[1:]):
        out += [a for a in across if lo <= a['top'] < hi]             # the band's heading first
        for l in left:
            if lo <= l['top'] < hi:
                out.append(l)
                if id(l) in halves:
                    out.append(halves[id(l)])
        out += [r for r in right if lo <= r['top'] < hi and id(r) not in partner]
    return out


def read() -> list[dict]:
    entries, village, section, heading = [], '', '', []
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            data = entry_boxes.read_page(page, columns=2)
            for col in [ordered(data)]:
                for ln in col:
                    t = unspace(ln['text'].strip())
                    if re.fullmatch(r'[\d\W]{1,4}', t) or re.match(r'^(?:SVOJA ŽIVLJENJA|SO DALI ZA SVOBODO)', t):
                        continue
                    if is_heading(t):
                        heading.append(t)                    # a village (or several, over two lines and both columns)
                        village, section = ' '.join(heading).strip(' ,'), ''
                        continue
                    heading = []
                    m = SECTION.match(t)
                    if m:
                        section = 'padli' if m.group(1).lower().startswith('padli') else 'other'
                        continue
                    if section != 'padli':
                        continue
                    s = START.match(t)
                    if s:
                        entries.append({'no': number(s.group(1)), 'lines': [t[s.end():]], 'pdf_page': pno,
                                        'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1), 'village': village})
                    elif entries and entries[-1]['pdf_page'] in (pno, pno - 1):
                        entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if text.endswith('-') and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def place_title(village: str) -> str:
    return ', '.join(' '.join(w.capitalize() for w in part.split()) for part in village.split(','))


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    head, _, rest = text.partition(',')
    words = head.split()
    last = words[0][:1].upper() + words[0][1:] if words else ''
    given = ' '.join(words[1:])
    years = re.match(r'\s*(1[89]\d\d)?\s*-\s*(19[34]\d)?\s*,?\s*', rest)
    by, dy = (years.group(1) or '', years.group(2) or '') if years else ('', '')
    after = rest[years.end():] if years else rest
    parts = [p.strip() for p in after.split(',') if p.strip()]
    place = parts[0] if parts and not re.search(r'nezna\w*\s*kj', parts[0].replace(' ', '')) else ''
    village = place_title(e['village'])
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {given}'.strip(), 'last_name': last, 'also': [],
           'first_name': given.split()[0] if given else '', 'nick': '', 'fathers_name': '',
           'birth_year': by, 'born_in': f'{village.split(",")[0]}, Ljubljana' if village else '',
           'death_year': dy, 'death_place': place, 'no': e['no'],
           'additional_info': f'{village}, padli v NOV: {last} {given}, {rest.strip()}'.strip(),
           'list': TITLE, 'pdf_file': PDF.name, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']}
    return rec


def main() -> None:
    build_pdf()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} fallen in the army -> {OUT.relative_to(HERE.parent)}; villages: {len({r["additional_info"].split(", padli")[0] for r in recs})}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    gaps, prev = [], None
    for r, e in zip(recs, raw):
        if prev and prev[0] == e['village'] and r['no'] != prev[1] + 1:
            gaps.append(f"{e['village'][:20]} {prev[1]}->{r['no']} (p{r['pdf_page']})")
        prev = (e['village'], r['no'])
    print(f'number gaps: {len(gaps)}', gaps[:20])
    print(f"birth year: {sum(bool(r['birth_year']) for r in recs)}, death year: {sum(bool(r['death_year']) for r in recs)}, "
          f"place: {sum(bool(r['death_place']) for r in recs)}")
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']}-{r['death_year']} {r['death_place']!r} | {r['additional_info'][:100]}")


if __name__ == '__main__':
    main()
