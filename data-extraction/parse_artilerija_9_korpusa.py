"""
Parser: Artilerija 9. korpusa NOV (brigade code 72).

Source: Borivoj Lah-Boris, "Artilerija 9. korpusa" (Knjižnica NOV in POS, Ljubljana 1985; znaci.org 00003/824.pdf)
        →  website/public/pdfs/artilerija-9-korpusa.pdf (PDF pages 316-329 of the book):
    pp. 1-8     Seznam borcev artilerije 9. korpusa NOV: one column, a soldier a line
                    Ambrožič Janez, 16. 10. 1926, Jesenice
                    Batagelj Albin, Kamnje-Ajdovščina
    pp. 9-11    Seznam padlih: a table of 48, the name, "Datum in kraj rojstva" and "Padel" side by side, each cell
                running on to the lines under it
                    1. Biban Miha        27. 12. 1913, Vodice     april 1945, Vojsko
    pp. 11-14   Poveljniški kader: the commanders of each staff, division and battery, with dates (not read: they
                are in the roster)
"""
import re

import pdfplumber

from _parser_scaffold import _page_lines, _record, run_parser
from _slovene_lists import OWN, fix_ocr, given_names, name_part, restore_carons
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROSTER_TO, PADLI_FROM = 8, 9
DATE = r'(?:\d{1,2}\.\s*)?(?:[\dIVX]{1,4}\.\s*|[a-z]+\s+)?1[89]\d\d'


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """The roster's lines, each an entry; then a line per row of the table of the fallen, its three cells joined
    by '¦' (the columns start where the header's "Datum" and "Padel" do)."""
    lines: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for n in range(start_page - 1, min(end_page or len(pdf.pages), len(pdf.pages))):
            page = pdf.pages[n]
            offset = viewer_offset(page)
            if n + 1 <= ROSTER_TO:
                for ln in _page_lines(page, n + 1, offset):
                    t = ln['text'].strip()
                    if not re.match(r'^SEZNAM|^[\d\W]+$|^\d+\'?\s+\d{3}$', t):        # heading, "316", "21' 323"
                        ln['text'] = '§s§ ' + t
                        lines.append(ln)
                continue
            words = page.extract_words(keep_blank_chars=False)
            dx, dy = offset
            head = {w['text']: w['x0'] - dx for w in words if w['text'] in ('Datum', 'Padel')}
            if 'Datum' not in head:
                continue
            end = min((w['top'] - dy for w in words if w['text'] == 'Poveljniški'), default=1e9)
            rows: list[dict] = []
            printed: list[list[dict]] = []                                      # the words of each printed line
            for w in sorted(words, key=lambda w: w['top']):
                if printed and w['top'] - printed[-1][0]['top'] <= 4:
                    printed[-1].append(w)
                else:
                    printed.append([w])
            for w in (w for line in printed for w in sorted(line, key=lambda w: w['x0'])):
                x, y = w['x0'] - dx, w['top'] - dy
                if y >= end - 2 or y < min(w2['top'] - dy for w2 in words if w2['text'] == 'rojstva') + 4:
                    continue
                col = 0 if x < head['Datum'] - 4 else 1 if x < head['Padel'] - 4 else 2
                if col == 0 and re.fullmatch(r'\d{1,2}\.', w['text']):              # "17." starts a row
                    rows.append({'page': n + 1, 'x': round(x, 1), 'y': round(y, 1), 'cells': [[], [], []], 'last': y})
                    continue
                if rows and re.fullmatch(r'\d{3}', w['text']) and y > rows[-1]['last'] + 12:
                    continue                                                    # the page number
                if rows:
                    rows[-1]['cells'][col].append(w['text'])
                    rows[-1]['last'] = max(rows[-1]['last'], y)
            for r in rows:
                cells = [' '.join(c) for c in r['cells']]
                lines.append({'page': r['page'], 'x': r['x'], 'y': r['y'], 'text': '§p§ ' + ' ¦ '.join(cells)})
    return lines


def year(t: str) -> str:
    return re.sub(r'\b1,(9\d\d)\b', r'1\1', t)                                  # "1,944"


def read_dot(given: str) -> str:
    """'Jo.e' = Jože: a caron letter the scan read as a dot, where the corpus knows the name well."""
    if not re.search(rf'[{L}]\.[{L}]', given):
        return given
    best = max((given.replace('.', c) for c in 'žčš'), key=lambda g: given_names()[g])
    return best if given_names()[best] >= 10 else given


def parse_place(s: str) -> str:
    """'Kamnje-Ajdovščina' = Kamnje, Ajdovščina (the village, then the municipality); 'Len j ava' = Lenjava."""
    s = re.sub(rf'(?<=[{L}])-(?=[{U}])', ', ', s.strip(' ,.'))
    s = re.sub(rf'(?<=[{L}]) ((?![vszk])[{L}]) (?=[{L}])', r'\1', s)         # "Len j ava" (not "v", "s", "z", "k")
    toks: list[str] = []
    for w in s.split():
        if toks and re.fullmatch(rf'[{L}]{{1,2}}', w) and w not in ('v', 'na', 'ob', 'pri', 'pod', 'nad'):
            toks[-1] += w
        else:
            toks.append(w)
    return ' '.join(toks)


def parse_roster(text: str) -> dict:
    """'Ambrožič Janez, 16. 10. 1926, Jesenice'"""
    text = year(fix_ocr(re.sub(r'^§s§\s*', '', text)))
    head, _, rest = text.partition(',')
    last, given, notes = name_part(head.strip())
    given = read_dot(given)
    rest = rest.strip(' ,')
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    m = re.match(rf'^({DATE})\b[.,]?\s*(.*)$', rest)
    place = m.group(2) if m else rest
    if m:
        rec['birth_year'] = re.search(r'1[89]\d\d', m.group(1)).group(0)
    place = parse_place(place)
    if place and re.match(rf'^[{U}]', place) and not re.search(r'\d', place):
        rec['birth_place'] = place
    return rec


def parse_fallen(text: str) -> dict:
    """'1. Biban Miha ¦ 27. 12. 1913, Vodice ¦ april 1945, Vojsko'"""
    name, born, died = (year(fix_ocr(c)).strip() for c in re.sub(r'^§p§\s*', '', text).split('¦'))
    name = re.sub(r'-\s+(?=[{U}])'.replace('{U}', U), '-', name)                 # "Bitežnik Alojz- Lojze"
    last, given, notes = name_part(name)
    given = read_dot(given)
    info = '; '.join(notes + [p for p in (born, ('padel ' + died) if died else '') if p])
    rec = _record(last, given, '', info)
    rec['death_type'] = 'poginuo'
    rec['birth_year'] = ''
    m = re.match(rf'^({DATE})(?:\s*\(\d{{4}}\))?[.,]?\s*(.*)$', born)
    if m and int(re.search(r'1[89]\d\d', m.group(1)).group(0)) < 1935:      # "28. 6. 1,944": a misprint, no birth year
        rec['birth_year'] = re.search(r'1[89]\d\d', m.group(1)).group(0)
    place = parse_place(m.group(2) if m else born)
    if place and re.match(rf'^[{U}]', place) and not re.search(r'\d', place):
        rec['birth_place'] = place
    d = re.match(rf'^({DATE})\b[.,]?\s*(.*)$', died)
    if d:
        rec['death_date'] = re.sub(r'\s+', ' ', d.group(1))
        dp = parse_place(d.group(2))
        if dp and re.match(rf'^[{U}]', dp):
            rec['death_place'] = dp
    return rec


def parse(text: str) -> dict:
    return parse_fallen(text) if text.startswith('§p§') else parse_roster(text)


if __name__ == '__main__':
    OWN['file'] = 'artilerija-9-korpusa-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/artilerija-9-korpusa.pdf',
        brigade_code=72,
        output_path='website/public/artilerija-9-korpusa-soldiers.json',
        start_page=1,
        end_page=11,
        layout='single',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        post_fn=lambda soldiers: restore_carons(soldiers, lambda s: s['pdf_page'] >= PADLI_FROM),
    )
