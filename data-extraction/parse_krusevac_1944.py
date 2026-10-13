"""
Oslobođenje Kruševca 1944. godine (Zbornik dokumenata, studija i sećanja učesnika i savremenika; znaci.org 00001/292,
the chapter 292_32.pdf) → website/public/pdfs/krusevac-1944-poginuli.pdf: a book across units, its entries added to the
records of the soldiers it describes (see scripts/match_references.py).

"Spisak boraca poginulih u borbama za oslobođenje Kruševca septembra i oktobra 1944. godine" (book pp. 273-283), one
column of numbered entries in Cyrillic under each unit: the 4. proleterska crnogorska (the site's unit 40), the 3. and
6. srpska, the 17. srpska (55) and the command of the Kruševac military area:
    6. Благојевић Миљка Мирослав, рођен 1917. године у селу Паруновац Срез Крушевачки, погинуо септембра 1944.године
    на Трнавачкој чуки.
Surname, father (or an initial) and given name, a few printed given name first ("86. Милован Јокић"). The closing
counts of the fallen whose names were not found ("- У борби са четницима у селу Текије погинуло 4 борца") are not read.

Output: data-extraction/znaci/krusevac-1944-poginuli-entries.json (IDs 9012xxxxxx, in the book's order), with the
fields the matcher reads (last_name, first_name, nick, fathers_name in the genitive, birth_year, born_in, death_year,
death_date, units), the unit as printed, and the entry's place on the page and its box. The entries are in Latin.

Usage: python data-extraction/parse_krusevac_1944.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402

PDF = 'krusevac-1944-poginuli.pdf'
OUT = HERE / 'znaci' / 'krusevac-1944-poginuli-entries.json'
PREFIX = '9012'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# the units' headings, and the site's unit for each that is on the site
UNITS = {'4. Proleterska crnogorska brigada': 40, '3. Srpska brigada': None, '6. Srpska brigada': None,
         '17. srpska brigada': 55, 'Komanda kruševačkog vojnog područja': None}
DEATH = re.compile(r'\b(poginu[ol]a?|umr[lo]a?|streljan[a]?|zarobljen[a]?)\b', re.I)


def lines() -> list[dict]:
    out = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            col = entry_boxes.read_page(page, 1)['columns'][0]
            # an entry starts at the page's left edge, its lines run on indented; a line at the edge without a
            # number is prose (the note before the names a study adds, p. 7)
            left = min((ln['x0'] for ln in col if re.match(r'\d{1,3}\s?\.', ln['text'])), default=0)
            for ln in col:
                out.append(dict(ln, page=pno, text=cyrillic_to_latin(ln['text']).strip(), hangs=ln['x0'] < left + 6))
    return out


def read() -> list[dict]:
    entries, unit, done = [], None, False
    for ln in lines():
        t = ln['text']
        if done or re.fullmatch(r'[•.]?\d{3}', t):
            continue                                                   # the page number
        if re.match(r'-?\s*Samostalni bataljon', t):
            done = True                                                # the counts of the unnamed fallen, to the end
            continue
        heading = next((u for u in UNITS if t.lower() == u.lower()), None)
        if heading:
            unit = heading
            continue
        if not unit:
            continue                                                   # the list's title
        m = re.match(r'^(\d{1,3})\s?\.\s*', t)
        if m and ln['hangs']:
            entries.append({'no': int(m.group(1)), 'lines': [t[m.end():]], 'pdf_page': ln['page'],
                            'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1), 'unit': unit})
        elif entries and not ln['hangs']:
            entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = lines[0]
    for ln in lines[1:]:
        if re.search(rf'[{L}]-$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln
        else:
            text += ' ' + ln
    text = re.sub(r'(\d)\.\s*G\.', r'\1. g.', text)                    # "1923.G."
    text = re.sub(r'(\d{4})\.(?=godin)', r'\1. ', text)                # "1944.godine"
    return re.sub(r'\s+', ' ', text).strip()


def name_order(words: list[str]) -> list[str]:
    """A few names stand given name first ("Milovan Jokić", "Radoslav R. Jelić"): turned to surname first where the
    site knows the first word as a given name far better than as a surname, and the last as a surname."""
    if len(words) < 2:
        return words
    first_as_given = ofz.known(words[0], 'first')[0]
    first_as_surname = ofz.known(words[0], 'last')[0]
    last_as_surname = ofz.known(words[-1], 'last')[0]
    if first_as_given >= 20 and last_as_surname >= 5 and first_as_surname * 10 < first_as_given:
        return [words[-1]] + words[1:-1] + [words[0]]                   # Jokić Milovan, Jelić R. Radoslav
    return words


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    head, info = (re.split(r',\s*', text, 1) + [''])[:2]
    nick = ''
    q = re.search(r'["“”„]([^"“”„]+)["“”„]', head)
    if q:                                                              # Mandić "Ciganče"
        nick, head = q.group(1), (head[:q.start()] + head[q.end():]).strip()
    words = name_order(head.split())
    last = words[0] if words else ''
    if len(words) >= 3:
        father, given = words[1], words[2]
        if len(words) > 3 and not nick:
            nick = ' '.join(words[3:])                                 # Jovanović Radomir Ćurčija
    elif len(words) == 2:
        father, given = '', words[1]
    else:
        father, given = '', ''
    if len(words) == 3 and not re.fullmatch(rf'[{U}]\.', father) and ofz.known(father, 'first')[0] >= 20 \
            and ofz.known(given, 'first')[0] < 3:
        father, given, nick = '', father, given                        # "Jovanović Radomir Ćurčija": a nickname
    if '-' in given and not nick:
        given, nick = given.split('-', 1)                              # "Vojislav-Voja", "Ljubomir-Ljubisav"
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': ' '.join(x for x in (last, father, given) if x)
           + (f' — {nick}' if nick else ''), 'last_name': last, 'first_name': given, 'nick': nick, 'fathers_name': father}
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d\.?\s*(?:g\.|godine)?\s*)?(?:u\s+|na\s+)?(?:selu\s+)?'
                  rf'([{U}][{L}]+(?:[\s-]+[{U}]?[{L}]+){{0,3}})', info)
    rec['born_in'] = re.sub(r'\s*-\s*', ', ', b.group(1)) if b else ''
    d = DEATH.search(info)
    years = re.findall(r'\b(19[34]\d)\b', info[d.start():]) if d else []
    rec['death_year'] = years[0] if years else '1944'
    when = re.search(r'(?:\d{1,2}(?:/\d{1,2})?\.\s?\d{1,2}\.\s?|(?:septembra|oktobra|avgusta|juna|decembra)\s+)19[34]\d',
                     info[d.start():]) if d else None
    parsed = parse_when(when.group(0).replace('/', '-')) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = [UNITS[e['unit']]] if UNITS[e['unit']] else []
    rec['unit'] = e['unit']
    rec['additional_info'] = f"{e['unit']}: {info}"
    rec['no'] = e['no']
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main():
    ofz.corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    by = {}
    for r in recs:
        by[r['unit']] = by.get(r['unit'], 0) + 1
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; {by}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    gaps = [f"{a['no']}->{b['no']}" for a, b in zip(recs, recs[1:]) if b['no'] != a['no'] + 1 and b['no'] != 1]
    print(f'number gaps: {gaps}')
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} | {r['units']}")
            print(f"      {r['additional_info'][:150]}")


if __name__ == '__main__':
    main()
