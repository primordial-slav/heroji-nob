"""
Parser: 4. proleterska (crnogorska) brigada (brigade code 40), third book — the men on the day it was formed.

Source: *Četvrta proleterska - zbornik sjećanja*, knj. 2 (znaci.org 00001/287), "Spisak boraca i starješina na dan
        formiranja brigade" (17 June 1942), PDF pp. 507-586 → website/public/pdfs/4-proleterska-formiranje.pdf
A table over each spread, in Cyrillic: the left page the number, name ("ДАПЧЕВИЋ Јована ПЕКО", the father in the
genitive), duty and birthplace; the right page the same rows' year of birth, trade, membership of the KPJ or SKOJ and
a note (most often what became of him: "Погинуо 1942. на Купресу", "Умро послије рата"). The staff's and each
battalion's and company's heading ("ШТАБ БРИГАДЕ", "2. ЧЕТА") stands between the rows: the record's unit_detail.
A row's cells may run to a second line ("ЂУРИЧКОВИЋ Милоша / БОШКО"), so a row takes the band down to the next number;
the right page's rows stand at the same heights.
Each record's box is the row on the left page (the PDF is in entry_boxes.INLINE_ENTRIES).
Usage: python data-extraction/parse_4_proleterska_formiranje.py [--dry out.json]
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
from _parser_scaffold import assign_ids_to_soldiers, cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = HERE.parent / 'website' / 'public' / 'pdfs' / '4-proleterska-formiranje.pdf'
SOURCE = HERE / '.cache' / 'znaci_library' / 'chapters' / '00001_287.pdf'            # znaci.org/00001/287.pdf
OUTPUT = HERE.parent / 'website' / 'public' / '4-proleterska-soldiers.json'
FIRST, LAST = 507, 586
ID_START = 20001
TITLE = 'Spisak boraca i starešina na dan formiranja brigade (17. jun 1942)'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
HEADING = re.compile(r'\b(?:ŠTAB|ČETA|BATALJON|POLITODJEL|TEHNIKA|KURIRI|VOD|BOLNIC|PRATEĆ|EKIPA|SANITET|INTENDANT|'
                     r'KOD ŠTABA|BRIGADE)\b')


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(SOURCE), fitz.open()
        out.insert_pdf(src, from_page=FIRST - 1, to_page=LAST - 1)
        out.save(PDF, garbage=4, deflate=True)


def lat(w: dict) -> dict:
    t = cyrillic_to_latin(w['text'])
    if len(t) >= 6 and len(t) % 2 == 0 and t[0::2] == t[1::2]:
        t = t[0::2]                                     # a word the text layer doubled ("bboorraacc", fake bold)
    return dict(w, text=t)


def lines_of(words: list[dict]) -> list[list[dict]]:
    rows: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if rows and abs(rows[-1][0]['top'] - w['top']) < 4:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w['x0']) for r in rows]


def headers(words: list[dict], keys: tuple) -> dict:
    """Each header's left edge and line, found by its letters along a line (the OCR sets some headers a letter a
    word: "Д у ж н о с т", "М јесто")"""
    found = {}
    for ln in lines_of([w for w in words if w['top'] < 260]):
        s, xs = '', []
        for w in ln:
            s += w['text']
            xs += [w['x0']] * len(w['text'])
        for key in keys:
            i = s.find(key)
            if i >= 0 and key not in found:
                found[key] = {'x0': xs[i], 'top': ln[0]['top']}
    return found


def column_starts(words: list[dict], k: int) -> list[float]:
    """The k columns' left edges: the x where most of the page's words begin, peaks at least 25pt apart (a header
    sits centred over its column, so the rows' own words tell where a column begins)"""
    from collections import Counter
    hist = Counter(round(w['x0'] / 3) * 3 for w in words)
    peaks: list[int] = []
    for x, _ in hist.most_common():
        if all(abs(x - p) > 25 for p in peaks):
            peaks.append(x)
        if len(peaks) == k:
            break
    return sorted(peaks)


def is_left(page) -> bool:
    return bool(headers([lat(w) for w in viewer_words(page)], ('Prezime', 'očevo')))


def spread(left, right, pno: int, section: str) -> tuple[list[dict], str]:
    lw = [lat(w) for w in viewer_words(left)]
    rw = [lat(w) for w in viewer_words(right)] if right is not None else []
    # "Prezime, očevo ime i ime" (the OCR's "Prezimg", "Irezime": "očevo" stands in every one)
    head = headers(lw, ('Prezime', 'očevo', 'Dužnost', 'Mjesto'))
    if 'očevo' not in head and 'Prezime' not in head:
        return [], section
    if 'Prezime' not in head:
        head['Prezime'] = {'x0': head['očevo']['x0'] - 38, 'top': head['očevo']['top']}
    top = max(w['top'] for w in head.values()) + 10
    body = [w for w in lw if w['top'] > top]
    # the columns where the rows' words begin: the name where a row's first word after its number stands (the
    # surname); duty and birthplace the two commonest left edges well right of it (past the father and given name)
    firsts = sorted(ln[1]['x0'] for ln in lines_of(body)
                    if len(ln) > 1 and re.fullmatch(r'\d{1,3}\.?', ln[0]['text']) and ln[1]['text'].isupper())
    if not firsts:
        return [], section
    name_start = firsts[len(firsts) // 2]
    starts = column_starts([w for w in body if w['x0'] > name_start + 120], 2)
    if len(starts) < 2:
        return [], section
    name_x, duty_x, place_x = name_start - 5, starts[0] - 5, starts[1] - 5
    rhead = headers(rw, ('Godina', 'Zanimanje', 'Član', 'Primjedba', 'Prim'))
    rtop = max([h['top'] for h in rhead.values()] + [0]) + 14
    rbody = [w for w in rw if w['top'] > rtop and not re.fullmatch(r'\d{3}', w['text'])]
    rstarts = column_starts(rbody, 4) if rbody else []
    trade_x, party_x, note_x = (rstarts[1:] if len(rstarts) == 4 else [145, 222, 300])
    # the rows: a number in the first column ("51."); the headings between them
    marks, headings = [], []
    for ln in lines_of(body):
        t = ' '.join(w['text'] for w in ln)
        if ln[0]['x0'] < name_x and re.fullmatch(r'\d{1,3}\.?', ln[0]['text']) and int(ln[0]['text'].rstrip('.')) < 400:
            marks.append(ln[0])                         # (not the page's number, "492", at its foot)
            if len(ln) > 1 and re.fullmatch(r'\d{1,3}\.', ln[1]['text']) and ln[1]['x0'] < name_x:
                marks.append(dict(ln[1], top=ln[1]['top'] + 9))   # "72." "73." on one line: the next row below
        elif HEADING.search(t) and t.upper() == t and not re.search(r'\d{4}', t):
            headings.append((ln[0]['top'], ln))
    # two numbers stacked on one row where the text layer put two rows' names together ("72." "73.")
    out = []
    for i, m in enumerate(marks):
        lo = m['top'] - 5
        hi = marks[i + 1]['top'] - 5 if i + 1 < len(marks) else 10 ** 6
        sec = [h for h in headings if h[0] < m['top']]
        if sec:
            words = [w for _, ln in sec for w in ln] if False else sec[-1][1]
            section = ' '.join(w['text'] for w in words)
        hw = {id(w) for _, ln in headings for w in ln}
        cells = {'name': [], 'duty': [], 'place': []}
        for w in body:
            if lo <= w['top'] < hi and id(w) not in hw and w is not m and not (w['x0'] < name_x and re.fullmatch(r'\d{1,4}\.?', w['text'])):
                col = 'place' if w['x0'] >= place_x else 'duty' if w['x0'] >= duty_x else 'name' if w['x0'] >= name_x else None
                if col:
                    cells[col].append(w)
        rcells = {'year': [], 'trade': [], 'party': [], 'note': []}
        for w in rbody:
            if lo - 4 <= w['top'] < hi - 4:
                col = 'note' if w['x0'] >= note_x - 5 else 'party' if w['x0'] >= party_x - 5 else 'trade' if w['x0'] >= trade_x - 5 else 'year'
                rcells[col].append(w)
        out.append({'no': int(m['text'].rstrip('.')), 'section': section, 'cells': cells, 'rcells': rcells,
                    'pdf_page': pno, 'pdf_x': round(m['x0'], 1), 'pdf_y': round(m['top'], 1),
                    'pdf_x_end': round(max([w['x1'] for ws in cells.values() for w in ws] + [m['x1']]), 1),
                    'pdf_y_end': round(max([w['bottom'] for ws in cells.values() for w in ws] + [m['bottom']]), 1)})
    if headings and (not marks or headings[-1][0] > marks[-1]['top']):
        section = ' '.join(w['text'] for w in headings[-1][1])
    return out, section


def text(ws: list[dict]) -> str:
    s = ''
    for w in sorted(ws, key=lambda w: (round(w['top'] / 3), w['x0'])):
        t = w['text']
        if s.endswith('-') and t[:1].islower():
            s = s[:-1] + t
        else:
            s += (' ' if s else '') + t
    return re.sub(r'\s+', ' ', s).strip()


def parse(r: dict) -> dict | None:
    c = {k: text(v) for k, v in r['cells'].items()}
    rc = {k: text(v) for k, v in r['rcells'].items()}
    ws = c['name'].replace("'", '').split()
    caps = [w for w in ws if w.isupper() and len(w) > 1]
    if not caps:
        return None
    last = caps[0].capitalize()
    first = ' '.join(w.capitalize() for w in caps[1:]) if len(caps) > 1 else ''
    father = next((w for w in ws if not w.isupper()), '')
    by = re.search(r'1[89]\d\d', rc['year'])
    section = ' '.join(w.capitalize() if w.isupper() else w for w in r['section'].split())
    info = ', '.join(x for x in (c['duty'], c['place'], by.group(0) if by else '', rc['trade'], rc['party'], rc['note']) if x)
    return {'last_name': '-'.join(p.capitalize() for p in last.split('-')), 'middle_name': father, 'first_name': first,
            'fathers_name': '', 'full_name': f'{last} {first}'.strip(),
            'additional_info': f'{TITLE}, {section}: {info}' if section else f'{TITLE}: {info}',
            'birth_year': by.group(0) if by else '', 'unit_detail': section,
            'pdf_file': PDF.name, 'pdf_page': r['pdf_page'], 'pdf_x': r['pdf_x'], 'pdf_y': r['pdf_y'],
            'pdf_x_end': r['pdf_x_end'], 'pdf_y_end': r['pdf_y_end'], '_no': r['no']}


def main() -> None:
    build_pdf()
    rows, section = [], ''
    with pdfplumber.open(PDF) as pdf:
        pages = pdf.pages
        for i, page in enumerate(pages):
            if not is_left(page):
                continue
            right = pages[i + 1] if i + 1 < len(pages) and not is_left(pages[i + 1]) else None
            got, section = spread(page, right, i + 1, section)
            rows += got
    recs = [s for s in (parse(r) for r in rows) if s]
    nums = [r['_no'] for r in recs]
    gaps = [f'{a}->{b}' for a, b in zip(nums, nums[1:]) if b != a + 1]
    print(f'{len(rows)} rows, {len(recs)} records; numbers {nums[:1]}..{nums[-1:]}; gaps {gaps[:30]}')
    print(f"birth year {sum(bool(r['birth_year']) for r in recs)}, father {sum(bool(r['middle_name']) for r in recs)}, "
          f"sections {len({r['unit_detail'] for r in recs})}")
    for r in recs:
        r.pop('_no')
    recs.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))
    recs = assign_ids_to_soldiers(recs, 40, ID_START)
    if '--dry' in sys.argv:
        Path(sys.argv[sys.argv.index('--dry') + 1]).write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
        return
    kept = [s for s in json.loads(OUTPUT.read_text(encoding='utf-8')) if s.get('pdf_file') != PDF.name]
    for s in kept:
        if s.get('other_sources'):
            s['other_sources'] = [o for o in s['other_sources'] if o.get('pdf_file') != PDF.name]
            if not s['other_sources']:
                del s['other_sources']
    clash = {s['soldier_id'] for s in kept} & {s['soldier_id'] for s in recs}
    assert not clash, sorted(clash)[:5]
    OUTPUT.write_text(json.dumps(kept + recs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(recs)} records from {ID_START} -> {OUTPUT.name} (kept {len(kept)})')


if __name__ == '__main__':
    main()
