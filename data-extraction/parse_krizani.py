"""
*Križani v boju za svobodo / S. Croce nella lotta per la libertà* (skupina avtorjev; znaci.org 00003/720, PDF pp. 78-108,
book pp. 88-118) → website/public/pdfs/krizani-v-boju-za-svobodo.pdf: the people of Križ (Santa Croce, by Trieste) in
the war, a book across units.

Two parts go in:
  "Padli za svobodo", a bio each, one column: "Antončič Evald - rojen 3. oktobra 1924 v Križu, oče Alojz, mati ...".
  The book's dead are not all fighters (men shot by the Germans at home, an activist who died after Mauthausen, a
  volunteer who fell in Spain in 1937), so a bio goes in only if it puts him in the army (partizani, a brigade, a
  battalion, a unit of the IX. korpus, the narodnoosvobodilna vojska, a komanda mesta, borec) and names a war year;
  the last such year is his death.
  "Seznami borcev": the table "Križani v narodnoosvobodilni vojski Jugoslavije" (163) and "Borci NOV, ki niso Križani,
  pa stanujejo v Križu" (number, name, house name, father, born, joined the NOV, rank, unit), the rows set where the
  cells' text falls, a cell sometimes on two lines.
The lists after them (the Spanish volunteers, Križani in Italian partisan units and in the Italian army, the
deportees) stay out.
Output: data-extraction/znaci/krizani-v-boju-za-svobodo-entries.json, IDs 9051xxxxxx, each with its box.
Usage: python data-extraction/parse_krizani.py [--sample N]
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
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

BOOK = 'krizani-v-boju-za-svobodo'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9051'
FIRST, LAST = 78, 108                      # the whole book's PDF pages: the first bio to the last table page
BIOS = range(1, 24)                        # the site PDF's pages of "Padli za svobodo" (PDF pp. 78-100)
TABLES = range(26, 32)                     # and of the tables (PDF pp. 103-108)
U, L = 'A-ZČŠŽĆĐ', 'a-zčšžćđ'
HEAD = re.compile(rf'^([{U}][{L}]+(?:\s+[{U}][{L}]+){{1,2}})\s*[-–—]\s*rojen')
ARMY = re.compile(r'partizan|brigad|bataljon|odred|\bčet[aeiou]?\b|\bNOVJ?\b|\bVDV\b|korpus|\bbor(?:ec|ka|ci)\b|komandir|'
                  r'komandant|komisar|kurir|divizij|prekomorsk|KNOJ|mornaric|narodnoosvobodiln\w*\s+vojsk|komand\w*\s+mest|'
                  r'prvobor',                                    # "med Šercerjevimi prvoborci" (1941)
                  re.I)
WAR_YEAR = re.compile(r'\b(194[1-6])\b')       # the list is of the fallen: the last war year a bio names is his death
#                                               (one who died of a partisan's illness in January 1946 is among them)
TITLES = {'nov': 'Križani v narodnoosvobodilni vojski Jugoslavije',
          'tenants': 'Borci NOV, ki niso Križani, pa stanujejo v Križu'}
# the site's units, by the table's words ("Gradnikova brig.", "XIX.Kosovelova brig.", "1 .prekomorska brig.")
UNITS = [(r'gradnikov', 64), (r'kosovelov', 142), (r'\b(?:1|I|2|II)\s*\.\s*prekomorsk', 144), (r'\b(?:4|IV)\s*\.\s*prekomorsk', 166),
         (r'\b(?:5|V)\s*\.\s*prekomorsk', 143), (r'osiješk|osječk', 104), (r'šercerjev', 141), (r'bračičev', 69),
         (r'tomšičev', 70), (r'cankarjev', 61), (r'gubčev', 62), (r'zidanškov', 65), (r'ljubljansk', 4),
         (r'art\w*\W+(?:IX|9)\.?\s*korp', 72)]


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_720.pdf'), fitz.open()
        out.insert_pdf(src, from_page=FIRST - 1, to_page=LAST - 1)
        out.save(PDF, garbage=4, deflate=True)


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[\xad-]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('\xad-') + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text.replace('\xad', '')).strip()


def bios(pdf) -> list[dict]:
    out = []
    for pno in BIOS:
        for ln in entry_boxes.read_page(pdf.pages[pno - 1])['columns'][0]:
            t = ln['text'].strip()
            if re.fullmatch(r'\d{1,3}', t) or t.startswith('Podoba matere') or ln['x0'] < 200:
                continue                                     # page numbers, a photo's caption under the text
            m = HEAD.match(t)
            if m:
                out.append({'name': m.group(1), 'lines': [t], 'pdf_page': pno, 'pdf_x': round(ln['x0'], 1),
                            'pdf_y': round(ln['top'], 1)})
            elif out:
                out[-1]['lines'].append(t)
    return out


def tables(pdf) -> list[dict]:
    """The tables' rows: a row starts at its number ("12."), and every word down to the next number is its"""
    rows, kind = [], 'nov'
    for pno in TABLES:
        words = sorted(viewer_words(pdf.pages[pno - 1]), key=lambda w: (round(w['top']), w['x0']))
        heads, head_top = {}, 0                 # each header's first word (a unit can be "Edinica IX. korpusa")
        for w in words:
            if w['text'] in ('Priimek', 'Domače', 'Očetovo', 'Rojstvo', 'Vstopil', 'Čin', 'Edinica') and w['text'] not in heads:
                heads[w['text']], head_top = w['x0'], max(head_top, w['top'])
        if len(heads) < 7:
            continue
        cols = [('name', heads['Priimek'] - 8), ('house', heads['Domače'] - 8), ('father', heads['Očetovo'] - 6),
                ('born', heads['Rojstvo'] - 14), ('joined', heads['Vstopil'] - 10), ('rank', heads['Čin'] - 8),
                ('unit', heads['Edinica'] - 8)]
        # a date never stands in the name columns: it is the birth or the joining, by which header it is nearer
        mid = (heads['Rojstvo'] + heads['Vstopil']) / 2 + 8
        number_x = heads['Priimek'] - 8
        body = [w for w in words if w['top'] > head_top + 6]
        # the second table's title, a line across the page ("BORCI NOV, KI NISO KRIŽANI, PA STANUJEJO V KRIŽU")
        title = next((w['top'] for w in body if w['text'] == 'BORCI' and w['x0'] < number_x + 10), None)
        body = [w for w in body if title is None or abs(w['top'] - title) >= 3]
        # first the rows' numbers, in order (not the page's own number, "114"), then each word to its row
        page_rows = []
        for w in body:
            k = 'tenants' if title is not None and w['top'] > title else kind
            before = page_rows or [r for r in rows if r['kind'] == k]
            last_no = before[-1]['no'] if before and before[-1]['kind'] == k else 0
            if (w['x0'] < number_x and re.fullmatch(r'\d{1,3}\.?', w['text'])
                    and 0 < int(w['text'].rstrip('.')) - last_no <= 2):
                page_rows.append({'kind': k, 'no': int(w['text'].rstrip('.')), 'cells': {c: [] for c, _ in cols},
                                  'pdf_page': pno, 'pdf_x': round(w['x0'], 1), 'pdf_y': round(w['top'], 1),
                                  'top': w['top'], 'word': w})
        if title is not None:
            kind = 'tenants'
        rows += page_rows
        for w in body:
            if any(w is r['word'] for r in page_rows):
                continue
            # a row's cells stand from a few points above its number (the dates, a line set higher) to the next row;
            # a word above the page's first row is the last row's of the page before
            later = [r for r in page_rows if r['top'] - 6 <= w['top']]
            if not later:
                continue
            row = later[-1]
            col = [c for c, x in cols if w['x0'] >= x]
            if re.fullmatch(r'[\d.]*\d{4}|\d{1,2}\.\d{1,2}\.?', w['text']) and col and col[-1] in ('house', 'father', 'born', 'joined'):
                col = ['born' if w['x0'] < mid else 'joined']
            elif col and col[-1] in ('born', 'joined') and re.search(rf'[{L}]{{3,}}', w['text']):
                col = ['rank']                               # "borec", "desetar" set a little left of the column
            if col:
                row['cells'][col[-1]].append(w['text'])
    return rows


def parse_bio(e: dict, n: int) -> dict | None:
    text = join(e['lines'])
    deaths = [int(y) for y in WAR_YEAR.findall(text)]
    if not ARMY.search(text) or not deaths:
        return None
    last, *given = e['name'].split()
    by = re.search(r'rojen\w*\.?\s+(?:\d+\s*\.\s*\w+\s+)?(1[89]\d\d)', text)
    father = re.search(rf'\boče\s+([{U}][{L}]+)', text)
    return {'soldier_id': f'{PREFIX}{n:06d}', 'name': e['name'], 'last_name': last, 'also': [], 'first_name': given[0],
            'nick': '', 'fathers_name': father.group(1) if father else '', 'birth_year': by.group(1) if by else '',
            'born_in': 'Križ, Trst', 'death_year': str(deaths[-1]),
            'units': sorted({c for p, c in UNITS if re.search(p, text, re.I)}),
            'additional_info': f'Padli za svobodo: {text}', 'list': 'Padli za svobodo',
            'pdf_file': PDF.name, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']}


def parse_row(r: dict, n: int) -> dict:
    # a capital the OCR set apart ("T enee", "M irko") joined again
    c = {k: re.sub(rf'\b([{U}]) (?=[{L}]{{2,}})', r'\1', ' '.join(v)).strip(' _—-') for k, v in r['cells'].items()}
    name = re.sub(r'\s*-\s*', '-', c['name']).replace('Tenee', 'Tence')   # "Purič -Tence Miroslav"; the OCR's Tenee
    also = []
    m = re.search(rf'\s+(?:roj|por)\.\s*([{U}][{L}]+)', name)   # "Bogateč roj. Sulčič Silva", "Paskovič por.Sulčič Ivka"
    if m:
        also, name = [m.group(1)], name[:m.start()] + name[m.end():]
    words = name.split()
    if len(words) > 2 and words[0] in ('Di', 'De', 'Del', 'Da', 'Dal', 'Della'):
        words = [f'{words[0]} {words[1]}'] + words[2:]          # "Di Lenardo Rudolf"
    last, first = (words[0], words[-1]) if len(words) > 1 else (name, '')
    first, nick = (first.split('-', 1) + [''])[:2] if '-' in first and last != first else (first, '')   # "Guerino-Vojko"
    born = re.search(r'(1[89]\d\d)\s*$', c['born'].replace(' ', '')) or re.search(r'(1[89]\d\d)', c['born'])
    by = born.group(1) if born else ''
    if not by and re.fullmatch(r'\d{1,2}\.\d{1,2}(1[89]\d\d)', c['born'].replace(' ', '')):
        by = c['born'].replace(' ', '')[-4:]                  # "18.41911": the full stop lost
    parts = [f"{name}" + (f" ({c['house']})" if c['house'] else ''), f"oče {c['father']}" if c['father'] else '',
             f"roj. {c['born']}" if c['born'] else '', f"v NOV {c['joined']}" if c['joined'] else '', c['rank'], c['unit']]
    text = ', '.join(p for p in parts if p)
    return {'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {first}'.strip(), 'last_name': last, 'also': also,
            'first_name': first, 'nick': nick, 'fathers_name': c['father'] if re.fullmatch(rf'[{U}][{L}]+', c['father']) else '',
            'birth_year': by, 'born_in': 'Križ, Trst' if r['kind'] == 'nov' else '',
            'units': sorted({code for p, code in UNITS if re.search(p, c['unit'], re.I)}),
            'additional_info': f"{TITLES[r['kind']]}: {text}", 'list': TITLES[r['kind']], 'no': r['no'],
            'pdf_file': PDF.name, 'pdf_page': r['pdf_page'], 'pdf_x': r['pdf_x'], 'pdf_y': r['pdf_y']}


def main() -> None:
    build_pdf()
    with pdfplumber.open(PDF) as pdf:
        raw_bios, raw_rows = bios(pdf), tables(pdf)
    out, n, dropped = [], 0, []
    for e in raw_bios:
        n += 1
        rec = parse_bio(e, n)
        if rec:
            out.append(rec)
        else:
            dropped.append(e['name'])
    for r in raw_rows:
        n += 1
        out.append(parse_row(r, n))
    stats = entry_boxes.fill_boxes(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(raw_bios)} bios, {len(raw_bios) - len(dropped)} fighters kept (left out: {", ".join(dropped)})')
    for kind in TITLES:
        nums = [r['no'] for r in raw_rows if r['kind'] == kind]
        gaps = [f'{a}->{b}' for a, b in zip(nums, nums[1:]) if b != a + 1]
        print(f'{kind}: {len(nums)} rows, numbers {nums[:1]}..{nums[-1:]}, gaps {gaps}')
    print(f'{len(out)} entries -> {OUT.relative_to(HERE.parent)}; boxes: {entry_boxes.describe(stats, stats["boxed"])}')
    if '--sample' in sys.argv:
        random.seed(3)
        for r in random.sample(out, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} {r['also']} {r['birth_year']} {r['units']} | {r['additional_info'][:110]}")


if __name__ == '__main__':
    main()
