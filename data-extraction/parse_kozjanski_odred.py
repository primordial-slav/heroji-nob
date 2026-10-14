"""
Parser: Kozjanski odred (brigade code 164).

Source: Tomaž Teropšič, "Kozjanski odred" II (Knjižnica NOV in POS 29/3; znaci.org 00003/2086.pdf), the roster of the
        odred's fighters →  website/public/pdfs/kozjanski-odred.pdf (PDF pp. 78-418 of the book; its scans made
        1-bit at 200 dpi, 41 MB to 8 MB, the text layer untouched). A table, a fighter in each row:
            Priimek, ime, partizansko ime | Leto in kraj rojstva | Datum vstopa v NOV in POS | Poklic | Ostalo
            ABRAM                         | 10. 8. 1917,         | VII. 1944                 | kmečki | Do septembra 1944 je bil v 3. četi
            Franc                         | Brezje               |                           | sin    | 2. bataljona, nato v 1. bataljonu.
The columns are taken from each page's header ("Priimek", "Leto", "vstopa", "Poklic", "Ostalo"); a row starts where
the name column has a surname in capitals. The author says the roster is not complete: in 1944 alone the odred sent
some 4,000 recruits on to Dolenjska and the Kamnik-Zasavje odred.
"""
import re
from collections import Counter

import pdfplumber

from _parser_scaffold import _record, run_parser, title_case
from pdf_coords import viewer_words

U = 'A-ZČĆŽŠĐ'
COLS = ('name', 'birth', 'joined', 'trade', 'note')
MONTHS = r'januarja|februarja|marca|aprila|maja|junija|julija|avgusta|septembra|oktobra|novembra|decembra'


# where the columns start, from the birth column (the header of p. 1: Priimek 75, Leto 164, vstopa 252, Poklic 316,
# Ostalo 366)
OFFSETS = (-89, 0, 88, 152, 202)


def columns(words: list[dict]) -> list[float] | None:
    """Where each column starts on this page. The pages sit up to 10 pt apart, and half have no header, so the
    birth column is measured from the data: the x where most rows' first date stands."""
    rows: dict = {}
    for w in words:
        rows.setdefault(round(w['top'] / 4), []).append(w)
    xs = Counter()
    for ws in rows.values():
        ws = sorted(ws, key=lambda w: w['x0'])
        first = next((w for w in ws if re.match(r'^(?:\d{1,2}\.|1[89]\d\d)', w['text']) and 120 < w['x0'] < 220), None)
        if first:
            xs[round(first['x0'])] += 1
    if not xs:
        return None
    mode = xs.most_common(1)[0][0]
    birth = min(x for x in xs if abs(x - mode) <= 3)
    return [birth + off - 6 for off in OFFSETS]


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, cols = [], None
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            words = viewer_words(pdf.pages[pno - 1])
            cols = columns(words) or cols                                     # a page without the header: the last one's
            header_end = max((w['bottom'] for w in words if w['text'] in ('POS', 'rojstva', 'partizansko')), default=0)
            rows: dict = {}
            for w in words:
                if w['top'] <= header_end + 1 or re.fullmatch(r'\d{1,3}', w['text']) and w['top'] < 70:
                    continue
                if w['x0'] < cols[0] - 4:
                    continue                                                  # the page number and title set sideways in the margin
                key = next((k for k in rows if abs(k - w['top']) < 3.5), w['top'])
                rows.setdefault(key, []).append(w)
            for top in sorted(rows):
                cells = ['', '', '', '', '']
                ws = sorted(rows[top], key=lambda w: w['x0'])
                for w in ws:
                    i = max(k for k in range(5) if w['x0'] >= cols[k] or k == 0)
                    cells[i] = (cells[i] + ' ' + w['text']).strip()
                if not any(cells):
                    continue
                starts = bool(re.match(rf'^[{U}][{U}\-]+(?:\s|$)', cells[0])) and sum(c.isupper() for c in cells[0][:3]) >= 2
                # a surname the scan read small ("mAčkovšek", "Stadler"): only a row's first line has a date in the
                # birth column or the date of joining
                # (not the second line of "18.2.1913, (tudi: / 1914), Dobrava")
                starts = starts or bool(cells[0]) and (bool(re.match(r'^(?:\d{1,2}\.|1[89]\d\d)(?![\d.\s]*\))', cells[1]))
                                                       or bool(re.match(r'^[IVX]{1,4}\.(?![\d.\s]*\))', cells[2])))
                text = '§x§ ' if starts else '§c§ '
                out.append({'page': pno, 'x': round(ws[0]['x0'], 1), 'y': round(top, 1),
                            'text': text + '|'.join(cells)})
    return out


def parse_entry(text: str) -> dict:
    """The entry's lines, each '§x§ name|birth|joined|trade|note': the cells of a column joined down the rows."""
    parts = [ln for ln in re.split(r'§[xc]§\s*', text) if ln.strip()]
    cells = ['', '', '', '', '']
    for ln in parts:
        for i, c in enumerate((ln.split('|') + [''] * 5)[:5]):
            c = c.strip()
            if c:
                cells[i] = (cells[i][:-1] if cells[i].endswith('-') else cells[i] + ' ') + c if cells[i] else c
    name, birth, joined, trade, note = (re.sub(r'\s+', ' ', c).strip() for c in cells)
    name = re.sub(r"\s+['/!,Ä]+(?=\s|$)", '', name)
    name = re.sub(r'(?<=[a-zčšžćđ])\s+([a-zčšž])(?=-|\s|$)', r'\1', name)    # "Aloj z", "Marij a-Vida"
    name = re.sub(r'(?<=[a-z])\.(?=[a-z])', '', name)                          # "Evge.n"
    name = re.sub(r'\((?:t\.?|tudi):?\s*', '(tudi: ', name)                     # "(t: Hribar)", "(t.: Karel)"
    name = re.sub(rf'\(([{U}]{{3,}})\)', r'(tudi: \1)', name)                   # "(TRAVNIKAR)"
    caps = re.match(rf'^((?:[{U}][{U}\-]+)(?:\s+(?:[{U}][{U}\-]+|\(tudi:?\s*[^)]*\)))*)\s*(.*)$', name)
    if not caps:                                                              # "mAčkovšek Alojz": read small
        caps = re.match(r'^(\S+)\s*(.*)$', name)
    if not caps:
        return {}
    last = title_case(re.sub(r'\s*\(tudi:?\s*([^)]*)\)', '', caps.group(1)))
    other = re.search(r'\(tudi:?\s*([^)]*)\)', caps.group(1))
    rest = caps.group(2)
    notes = [f'ili {title_case(other.group(1))}'] if other else []
    maiden = re.match(rf'^((?:roj|r)\.\s*[{U}][\w\-]+)\s+(.*)$', rest)          # "AVSEC roj. BIZJAK Vida", "r. Cerjak"
    if maiden:
        notes.append('roj. ' + title_case(maiden.group(1).split()[1]))
        rest = maiden.group(2)
    also = re.search(r'\s*\((?:tudi|t\.):?\s*([^)]*)\)', rest)                 # "Milan (tudi: Ivan)", "Drago (t.: Karel)"
    if also:
        notes.append(f'ili {also.group(1).strip()}')
        rest = (rest[:also.start()] + rest[also.end():]).strip()
    given, _, alias = rest.partition('-')                                      # "Bojan-Švejk": the partisan name
    if alias:
        notes.append(f'zvani {alias.strip()}')
    born = re.match(r'^((?:\d{1,2}\.\s*\d{1,2}\.\s*)?1[89]\d\d)\s*(?:\(tudi:?[^)]*\))?\s*,?\s*(.*)$', birth)
    if born:
        notes.append(f'rojen {born.group(1)}' + (f', {born.group(2)}' if born.group(2) else ''))
    elif birth:
        notes.append(f'rojen {birth}')
    if joined:
        notes.append(f'v NOV in POS od {joined}')
    if trade:
        notes.append(trade)
    if note:
        notes.append(note.rstrip('.'))
    rec = _record(last, given.strip(), '', '; '.join(notes))
    if born:
        rec['birth_year'] = born.group(1)[-4:]
        if born.group(2) and not re.search(r'\d', born.group(2)):
            rec['birth_place'] = born.group(2)
    if trade:
        rec['occupation'] = trade
    fell = re.search(rf'\bPadl[ae]\s+je\s+((?:\d{{1,2}}\.\s*)?(?:{MONTHS})?\s*19\d\d)?', note)
    if fell:
        rec['death_type'] = 'poginuo'
        if fell.group(1) and re.search(r'19\d\d', fell.group(1)):
            rec['death_date'] = re.sub(r'\s+', ' ', fell.group(1)).strip()
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/kozjanski-odred.pdf',
        brigade_code=164,
        output_path='website/public/kozjanski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
    )
