"""
Parser: 13. vojvođanska udarna brigada (3. brigada KNOJ-a) (brigade code 84).

Source: Đorđe Momčilović, "Kako do brigade" (znaci.org 00003/431.pdf, its pages 761-783, book pp. 771-793)
        →  website/public/pdfs/13-vojvodjanska.pdf:
    "Spisak pripadnika XIII vojvođanske udarne brigade", names only, in capitals, mostly two columns a page (some
    pages are one column):
        ADAMOV ALEKSANDAR
        BABIC RADE PRPIC                        (a nickname after the given name)
        DOSTANIĆ O. ŽIVKO                       (the father's initial)
        POPOV MILAN (MOKRIN)                    (the place, where two share a name)
        SRDIĆ BRANKO, vodnik
The author notes the list is incomplete: the brigade's own records were not yet open to him, he had the full list of
its 3rd battalion, the orders, a survey and the SUBNOR lists of the Banat municipalities.
znaci.org re-typeset the book from its OCR, so the page shows the text layer's errors: most diacritics are lost
("ACIMOVIC", restored from spellings the other units agree on), names are split ("ŽIV AN", joined where the joined
word is a known name), and a few are garbled past reading; those the alphabetical order settles are in FIXES.
A nickname too long for the column is printed on the next line, set in ("MARKUŠEV SVETISLAV / KORCAGIN").
"""
import re
from collections import defaultdict

import pdfplumber

from _parser_scaffold import _fold, _load_name_reference, _page_lines, _record, restore_diacritics, run_parser
from pdf_coords import viewer_offset

U = 'A-ZČĆŽŠĐ'
FIXES = {                                                                    # garbled lines, read by the alphabetical order
    'Đ JKIČIĆ': 'ĐUKIČIĆ',                                                   # between ĐUKANOVIĆ and ĐUKIĆ
    'l NEŽEV OBRAD': 'KNEŽEV OBRAD',                                         # between KMEZIĆ and KNEŽEVIĆ
    'JARIĆ M LAN': 'JARIĆ MILAN',
    'JAR iC PETAR': 'JARIĆ PETAR',
    'ŽIVOJNOV BLAAODAR': 'ŽIVOJNOV BLAGODAR',
    'PF TRO VI ć JOVAN': 'PETROVIĆ JOVAN',
    'POU AKOvVcf ANTON': 'POLJAKOVIĆ ANTON',                                 # among the POLJ- names
    "GRUBIŠIC t'.OFIJA": 'GRUBIŠIĆ SOFIJA',
    'Ä ÄC LEPOSAVAPUŠKA': 'PANIĆ LEPOSAVA PUŠKA',                           # between PANIĆ JOVAN and PANIĆ A. MILIVOJ
    'IIS1CA MIRKO': 'LISICA MIRKO',
    '8PIENICA°DANICA BOJANA': 'OPSENICA DANICA BOJANA',                      # before OPSENICA MAKSIM
    'MILIĆEVM ILOš': 'MILIĆEV MILOŠ',
    'Ž iVA': 'ŽIVA',
    'JACIMOVIC MILE „IT,MIljr': 'JACIMOVIC MILE',                       # a garbled word after the name
    'DRENOV AC MITO': 'DRENOVAC MITO',
}
_ref = {}
_prev: dict = {}


def columns(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """Each page's lines column by column. A column starts where many lines start after a wide gap; the cut lies just
    left of it, so a long name's last word stays in its column."""
    lines: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        stop = min(end_page, len(pdf.pages)) if end_page else len(pdf.pages)
        for n in range(start_page - 1, stop):
            page = pdf.pages[n]
            offset = viewer_offset(page)
            dx = offset[0]
            rows = defaultdict(list)
            for w in page.extract_words(x_tolerance=1.5):
                rows[round(w['top'] / 3)].append(w)
            cands = []
            for ws in rows.values():
                ws.sort(key=lambda w: w['x0'])
                for prev, w in zip([None] + ws[:-1], ws):
                    if prev is None or w['x0'] - prev['x1'] > 18:
                        cands.append(w['x0'] - dx)
            cands.sort()
            clusters: list[list[float]] = []
            for x in cands:
                if clusters and x - clusters[-1][-1] <= 8:
                    clusters[-1].append(x)
                else:
                    clusters.append([x])
            starts = [c[0] for c in clusters if len(c) >= 6]
            cuts = [-1e9] + [s - 4 for s in starts[1:]] + [1e9]
            for a, b in zip(cuts, cuts[1:]):
                part = page.filter(lambda o, a=a, b=b: o.get('object_type') != 'char' or a <= o['x0'] - dx < b)
                lines.extend(_page_lines(part, n + 1, offset))
                LINES.extend({'page': n + 1, 'x': round(ln['x0'] - dx, 1), 'y': round(ln['top'] - offset[1], 1),
                              'x1': round(ln['x1'] - dx, 1), 'bottom': round(ln['bottom'] - offset[1], 1)}
                             for ln in part.extract_text_lines(strip=True, return_chars=False) if ln['text'].strip())
    return lines


LINES: list[dict] = []


def boxes(soldiers: list[dict]) -> list[dict]:
    """Each name's box: its own words, and a nickname set in on the next line. entry_boxes finds no gutter on some of
    these pages (their columns sit at different places), so the file is in entry_boxes.INLINE_ENTRIES, which keeps
    these boxes."""
    by_page: dict = {}
    for ln in LINES:
        by_page.setdefault(ln['page'], []).append(ln)
    for s in soldiers:
        lines = sorted(by_page.get(s['pdf_page'], []), key=lambda ln: (ln['y'], ln['x']))
        i = next((k for k, ln in enumerate(lines) if abs(ln['x'] - s['pdf_x']) < 1 and abs(ln['y'] - s['pdf_y']) < 1), None)
        if i is None:
            continue
        mine = [lines[i]]
        nxt = [ln for ln in lines[i + 1:] if ln['x'] - lines[i]['x'] > 30 and 0 < ln['y'] - lines[i]['y'] < 12
               and ln['x'] < lines[i]['x'] + 140]
        mine += nxt[:1]                                                      # "MARKUŠEV SVETISLAV / KORCAGIN"
        s['pdf_x_end'] = max(ln['x1'] for ln in mine)
        s['pdf_y_end'] = max(ln['bottom'] for ln in mine)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    return boxes(restore_diacritics(soldiers))


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    prev = _prev.copy()
    if ln['page'] == 1 and (ln['y'] < 300 or ln['y'] > 570):
        return False                                                         # the heading, the author's note
    if re.search(r'Momčilović|KAKO DO|^BRIGADE$', t) or not re.search(r'[A-Za-zČĆŽŠĐčćžšđ]{3}', t):
        return False                                                         # running heads, page numbers, letters, specks
    for bad, good in FIXES.items():
        t = t.replace(bad, good)
    t = re.sub(rf'^(?:[{U}]|LJ|NJ|DŽ)\s+(?=[{U}]{{2,}}\S*\s+\S)', '', t)      # "A AREŽINA ILIJA": the letter heading
    t = re.sub(r"^['\"„“]+|[\s,.%]+$", '', t)
    _prev.update(page=ln['page'], x=ln['x'], y=ln['y'])
    if t.startswith('(') or (prev.get('page') == ln['page'] and ln['x'] - prev['x'] > 30 and 0 < ln['y'] - prev['y'] < 12):
        ln['text'] = t                                                       # the end of the line above, set in
        return True
    ln['text'] = '§p§ ' + t
    return True


def known(word: str) -> bool:
    if not _ref:
        _ref.update(_load_name_reference())
    w = _fold(word).lower()
    return any(w in _ref[f] for f in ('first_name', 'last_name'))


def fix(word: str) -> str:
    word = word.replace('2', 'Ž').replace('1', 'I').replace('0', 'O')
    word = re.sub(r'[^A-ZČĆŽŠĐa-zčćžšđ-]', '', word)
    if len(word) == 1:
        return word.upper()                                                  # "MIJIN ž. SAVA"
    return word.upper() if sum(c.isupper() for c in word) >= len(word) / 2 else word   # "DRAKULIć", "BOšKO"


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text).strip()
    text = re.sub(r'\s+\(([^)]*)$', r' (\1)', text)                           # "(B. ARANĐELOVO" without the bracket
    notes = []
    m = re.search(r'\s*\(([^)]+)\)', text)
    if m:
        notes.append(m.group(1).strip().title() if m.group(1).isupper() else m.group(1).strip())   # "(MOKRIN)"
        text = text[:m.start()] + text[m.end():]
    m = re.search(r',\s*(.+)$', text)
    if m:
        notes.append(m.group(1).strip())                                     # "RADIN IVAN, stariji"
        text = text[:m.start()]
    if re.search(r'\bdr\.?\s', text, re.I):
        notes.append('dr')
        text = re.sub(r'\b[Dd][Rr]\.?\s+', '', text)
    toks = [fix(t) for t in text.split()]
    toks = [t for t in toks if t]
    i = 0
    while i < len(toks) - 1:                                                 # "ŽIV AN", "STE VAN", "PA JA", "L JOT A"
        if (len(toks[i]) <= 3 or len(toks[i + 1]) <= 3) and not re.fullmatch(rf'[{U}]', toks[i]) and known(toks[i] + toks[i + 1]):
            toks[i:i + 2] = [toks[i] + toks[i + 1]]
        else:
            i += 1
    if len(toks) > 2 and re.fullmatch(r'L', toks[-3]) and toks[-2:] == ['JOT', 'A']:
        toks[-3:] = ['LJOTA']
    father = ''
    if len(toks) >= 3 and re.fullmatch(rf'[{U}]', toks[1].rstrip('.')):
        father = toks.pop(1).rstrip('.') + '.'                               # "DOSTANIĆ O. ŽIVKO", "IVANCEVIC A ILIJA"
    last = toks[0] if toks else ''
    given = toks[1] if len(toks) > 1 else ''
    if len(toks) > 2:
        nick = [w for w in toks[2:] if len(w) > 1]                           # "TOKIN JOVAN ć": a speck
        if nick:
            notes.insert(0, 'zvani ' + ' '.join(nick).title())
    return _record(last, given, father, '; '.join(notes))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/13-vojvodjanska.pdf',
        brigade_code=84,
        output_path='website/public/13-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns,
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
