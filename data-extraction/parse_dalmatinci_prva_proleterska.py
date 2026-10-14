"""
Parser: Prva proleterska brigada (brigade code 1), its fighters from Dalmatia, with their bios.

Source: *Dalmatinci u Prvoj proleterskoj* (Split; znaci.org 00001/207, the chapter 207_4.pdf, its PDF pp. 2-289, book
pp. 467-754: "Popis boraca iz Dalmacije u Prvoj proleterskoj NOU brigadi", compiled by Tomislav Jelić and Vitomir
Pirak) → website/public/pdfs/dalmatinci-prva-proleterska.pdf. Two or three narrow columns, alphabetical, a bio each:
    ALAĆ Ivana SREĆKO, rođen 1921, Drvenik, Makarska, zemljoradnik. Član SKOJ-a od 1941, član KPJ od 1942. ...
then the "Dodatni spisak" of those whose data the authors couldn't gather, the father as dots where unknown
("ALAGIĆ . . . STRAHINJA. U NOB-u 1942. Bio borac 2. bataljona."; the authors note some may not be from Dalmatia),
and four more at its end ("2. CARIĆ . . . SLAVKO, ..., Svirče, Hvar"). The footnote and the authors' note (with the
names of those who helped them) are not read. The surname and the given name in capitals, the father in the genitive.
These get 0001400001 on (the brigade's other books: 0001000001-, 0001100001-, 0001200001-, 0001300001-), and the same man
in the brigade's roster is merged (scripts/find_source_duplicates.py --brigade 1).
Usage: python data-extraction/parse_dalmatinci_prva_proleterska.py
"""
import re
from collections import Counter

import fitz

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}lI1\-]+'
# where a page's list ends: the "Dodatni spisak"'s footnote, the authors' note after the last entries
ENDS = ('* U ovom spisku', 'NAPOMENA: Ukupan')


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """The OCR's own lines (PyMuPDF), column by column: a page sets two or three narrow columns, each line starting at
    its column's left edge (a paragraph's first line a little in), so the columns are the line starts that recur."""
    lines = []
    with fitz.open(pdf_path) as doc:
        for pno, page in enumerate(doc, 1):
            raw = []
            for b in page.get_text('dict')['blocks']:
                for ln in b.get('lines', []):
                    text = ''.join(s['text'] for s in ln['spans']).strip()
                    if text:
                        x0, y0, x1, y1 = ln['bbox']
                        raw.append({'text': text, 'x0': x0, 'x1': x1, 'top': y0, 'bottom': y1})
            stop = [r['top'] for r in raw if r['text'].startswith(ENDS)]
            if stop:
                raw = [r for r in raw if r['top'] < min(stop) - 2]
            raw = [r for r in raw if not re.fullmatch(r'[\d\W]{1,5}', r['text'])
                   and not re.match(r'^(?:POPIS BORACA IZ|U PRVOJ PROLETERSKOJ|DODATNI SPISAK|BRIGADI$)', r['text'])]
            if not raw:
                continue
            counts = Counter(round(r['x0']) for r in raw)
            starts = []
            for x, n in counts.most_common():
                if n < 4:
                    break
                if all(abs(x - s) > 60 for s in starts):
                    starts.append(x)
            starts.sort()
            col_of = lambda x: max([i for i, s in enumerate(starts) if x >= s - 12] or [0])
            for r in sorted(raw, key=lambda r: (col_of(r['x0']), r['top'], r['x0'])):
                lines.append({'text': r['text'], 'x': round(r['x0'], 1), 'y': round(r['top'] + 2.6, 1), 'page': pno,
                              'x1': r['x1'], 'bottom': r['bottom'], 'col': col_of(r['x0'])})
    out, open_ = [], False
    BOXES.clear()
    for ln in lines:
        t = re.sub(r'^\d{1,2}\.\s+(?=[A-ZČĆŽŠĐ]{2})', '', ln['text'])          # "2. CARIĆ . . . SLAVKO"
        head = t.split(',')[0]
        start = (re.match(rf'^{CAPS}(?:\s*-\s*{CAPS})?(?:\s+\([^)]*\))?\s+(?:[{U}][{L}]+|\.\s?\.|{CAPS}\s*[,.]|$)', t)
                 and not re.match(r'^(?:NOB|NOV|NOVJ|KPJ|KPH|KP|KK|OK|MK|SKOJ|JNA|BJV|VŠ|PPK|SAD|SSSR|SUBNOR|AFŽ|NOO|ZAVNOH|URS|II|III|IV|VI)\b', t)
                 and not open_)
        if start:
            t = '§x§ ' + t
        # a name broken after the surname or the father ("ALAGIĆ" / ". . . STRAHINJA.", "BOŽIĆ Ivana" / "ANTE, rođen")
        open_ = bool(start) and not re.search(rf'\s{CAPS}\s*[,.]?(?:\s|$)', head[len(head.split()[0]):] + ' ') \
            and ',' not in t and len(t) < 30
        ln['text'] = t
        out.append(ln)
    # each entry's box, as the viewer draws it: one rectangle for its lines in each column and page it runs over
    # (the book's columns stand at a different place on every page, which entry_boxes can't follow)
    i = 0
    while i < len(out):
        if not out[i]['text'].startswith('§x§'):
            i += 1
            continue
        j = i + 1
        while j < len(out) and not out[j]['text'].startswith('§x§'):
            j += 1
        rects = {}
        for ln in out[i:j]:
            key = (ln['page'], ln['col'])
            r = rects.setdefault(key, [ln['x'], ln['y'] - 1, ln['x1'], ln['bottom']])
            r[0], r[2], r[3] = min(r[0], ln['x']), max(r[2], ln['x1']), max(r[3], ln['bottom'])
        first = rects[(out[i]['page'], out[i]['col'])]
        BOXES[(out[i]['page'], out[i]['x'], out[i]['y'])] = {
            'pdf_x_end': round(first[2], 1), 'pdf_y_end': round(first[3], 1),
            'pdf_rects': [[round(v, 1) for v in r] for (pg, _), r in rects.items() if pg == out[i]['page']]}
        i = j
    return out


BOXES: dict = {}


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = k8.post(soldiers)
    for s in soldiers:
        box = BOXES.get((s.get('pdf_page'), s.get('pdf_x'), s.get('pdf_y')))
        if box:
            s.update(box if len(box['pdf_rects']) > 1 else {k: v for k, v in box.items() if k != 'pdf_rects'})
    return soldiers


def parse(text: str) -> dict:
    t = re.sub(r'^§x§\s*', '', text)
    t = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', t)                   # "ro- đen"
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])- (?=[A-ZČĆŽŠĐ])', '', t)                   # "PE- TAR"
    t = re.sub(r'\s*\.\s?\.\s?\.?\s*', ' ', t, 1) if re.match(rf'^{CAPS}\s*\.\s?\.', t) else t   # the unknown father's dots
    # the name ends with the given name in capitals, before a comma or a full stop ("STRAHINJA. U NOB-u 1942.")
    t = re.sub(rf'^(\S+(?:\s+[{U}][{L}]+)?\s+{CAPS}(?:\s+{CAPS})?)\s*\.\s+', r'\1, ', t, 1)
    t = re.sub(rf'^(\S+(?:\s+[{U}][{L}]+)?\s+{CAPS})\s+(?=[{U}][{L}]|U\s)', r'\1, ', t, 1)          # "BADŽIN Krste MARKO U NOB-u"
    rec = k8.parse_entry(t)
    rec.pop('unit_detail', None)                          # the 8. division's brigades: not this list's
    y = re.search(r'\brođen[a]?\s+(?:[^.]*?\b)?(1[89]\d\d)\b', rec['additional_info'])
    rec['birth_year'] = y.group(1) if y else rec.get('birth_year', '')
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/dalmatinci-prva-proleterska.pdf',
        brigade_code=1,
        output_path='website/public/prva-proleterska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        extract_fn=extract,
        post_fn=post,
        id_start=400001,
        keep_other_sources=True,
    )
