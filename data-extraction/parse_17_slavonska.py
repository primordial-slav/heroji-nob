"""
Parser: 17. Slavonska Udarna Brigada (brigade code 16).

Source: Zdravko B. Cvetković — "SEDAMNAESTA SLAVONSKA BRIGADA"
        znaci.org/00001/131_9.pdf   →  17-slavonska-poginuli.pdf   (SPISAK POGINULIH, 24 pages)
        znaci.org/00001/131_10.pdf  →  17-slavonska-prezivjeli.pdf (SPISAK PREŽIVJELIH, pages 1-54;
                                        55-58 are the table of contents and colophon)
Two columns (the gutter moves between pages: col_split_x='auto'), Latin.

Entries are grouped under the municipality whose veterans' organisation reported them:
    BJELOVAR
    BADOVINAC S. BRANKO, rođen 1925 V. Pisanica — poginuo 1943, Ludbreg
    BOSANAC M. BOŠKO, rođen 1914, Babinac — poginuo 1943, Koprivnica
The survivors' list is terser ("ANDELIC PERO, 1915, Grahovijani, Pakrac"), sometimes just a name.
A heading is an ALL-CAPS line without a comma followed by extra space; it is kept out of the entry
text and added to each soldier's bio as "(općina Bjelovar)".
"""
import re
from _parser_scaffold import extract_lines_two_column, repair_lj_ocr, restore_diacritics, run_parser

U = 'A-ZČĆŽŠĐ'
PDFS = [('website/public/pdfs/17-slavonska-poginuli.pdf', 1, 24), ('website/public/pdfs/17-slavonska-prezivjeli.pdf', 1, 54)]
TITLE = re.compile(r'^(?:S ?P ?I ?S ?A ?K|S AK|S P I|SPI|SAK|SPISAK|POGINULIH BORACA|PREŽIVJELIH BORACA|17\. UDARNE BRIGADE\*?)$')
NO_NOTE = {'OSTALA MJESTA', 'RAZNA MJESTA'}          # catch-all sections: no municipality to add
CAPS_LINE = re.compile(rf'^[{U}][{U}.\- ]{{2,30}}$')
COL_SPLIT = 200            # only used to tell the columns apart when looking for headings


def _key(ln):
    return (ln['file'], ln['page'], round(ln['y'], 1), round(ln['x'], 1))


def find_headings():
    """Municipality headings: caps, no comma, and a gap of more than a line below them."""
    headings = {}
    for path, sp, ep in PDFS:
        lines = extract_lines_two_column(path, sp, ep, 'auto')
        name = path.rsplit('/', 1)[1]
        for i, ln in enumerate(lines):
            ln['file'] = name
            t = ln['text'].strip()
            if not CAPS_LINE.match(t) or TITLE.match(t):
                continue
            nxt = next((m for m in lines[i + 1:i + 3] if m['page'] == ln['page'] and (m['x'] < COL_SPLIT) == (ln['x'] < COL_SPLIT)), None)
            # at the foot of a column only a one-word line can be a heading ("ŽUFAR IVAN" is a survivor with no data)
            if (nxt is not None and nxt['y'] - ln['y'] > 14) or (nxt is None and ' ' not in t):
                headings[_key(ln)] = t
    return headings


HEADINGS = find_headings()
_footnote = set()             # (file, page, column) where a "*" footnote started


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    col = (ln['file'], ln['page'], ln['x'] < COL_SPLIT)
    if ln['page'] == 1 and t.startswith('*'):
        _footnote.add(col)
    if col in _footnote or TITLE.match(t) or _key(ln) in HEADINGS:
        return False
    ln['text'] = repair_line_start(t)
    return True


def repair_line_start(t: str) -> str:
    """OCR damage that hides an entry start: "GAJIĆ M.PAVLE" (no space after the initial), "PAyLOVIC",
    "2EGARAC" (Ž), "M IL JANO VIČ BOZO" (spaced caps), "PETRIN(K)" (initial glued on)."""
    t = re.sub(rf'(?<=\b[{U}])\.(?=[{U}]{{2}})', '. ', t)
    t = re.sub(rf'^([{U}]{{3,}})\(([{U}])\)', r'\1 (\2)', t)
    head, sep, tail = t.partition(' ')
    letters = [c for c in head if c.isalpha()]
    if len(head) >= 4 and letters and sum(c.isupper() for c in letters) / len(letters) >= 0.7:
        head = re.sub(r'^2', 'Ž', head).replace('y', 'V').upper()
        t = head + sep + tail
    name = t.split(',', 1)[0]
    toks = name.split()
    caps = []
    for tok in toks:
        if re.fullmatch(rf'[{U}]+', tok):
            caps.append(tok)
        else:
            break
    if len(caps) >= 3 and any(len(x) <= 2 for x in caps[:-1]) and not re.fullmatch(rf'[{U}]', caps[-2]):
        t = ''.join(caps[:-1]) + ' ' + t[len(' '.join(caps[:-1])) + 1:]
    return t


def _title(s: str) -> str:
    return ' '.join(w if len(w) <= 2 and w.endswith('.') else w.capitalize() for w in s.split()).replace('Sl.', 'Sl.')


def add_municipality(soldiers):
    order = lambda f, p, x, y: (f, p, x >= COL_SPLIT, y)
    heads = sorted((order(k[0], k[1], k[3], k[2]), v) for k, v in HEADINGS.items())
    for s in soldiers:
        pos = order(s.get('pdf_file'), s.get('pdf_page'), s.get('pdf_x') or 0, s.get('pdf_y') or 0)
        before = [v for k, v in heads if k[0] == pos[0] and k <= pos]
        if before and before[-1] not in NO_NOTE:
            town = 'ČSSR' if before[-1] == 'CSSR' else f'općina {_title(before[-1])}'
            s['additional_info'] = (s['additional_info'].rstrip(' .') + f' ({town})').strip()
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path=PDFS[0][0],
        brigade_code=16,
        output_path='website/public/17-slavonska-soldiers.json',
        start_page=PDFS[0][1],
        end_page=PDFS[0][2],
        layout='two_column',
        col_split_x='auto',
        script='latin',
        additional_pdfs=[{'pdf_path': PDFS[1][0], 'start_page': PDFS[1][1], 'end_page': PDFS[1][2]}],
        line_filter=keep_line,
        post_fn=lambda soldiers: add_municipality(repair_lj_ocr(restore_diacritics(soldiers))),
    )
