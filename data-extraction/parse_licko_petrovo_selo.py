"""
Miloš Pužić, Da se ne ponovi: Ratna kronika ranije općine Ličko Petrovo Selo (1985; Poreklo library, collection
"Monografije sela"): "Pali borci", the fallen fighters of the former općina by village, as a book across units.

A table a village (scan pp. 209-216): number, surname, the father and the name (the name often on a second line),
the years of birth, of joining the NOV and of death, the place of death, the unit, the duty and a note ("1. Pužić
Mile Dmitar 1903 1941 1943 Prijeboj 2. č. 1. lič. odreda k-dir voda"). Its villages: a) Ličko Petrovo Selo, b) Novo
Selo, c) Željava, d) Arapov Do, e) Rešetar, f) Zaklopača i Lisina, g) Donji Vaganac; the OCR lost or garbled the
headings of b), d) and g)
and reads Željava as "Leljava" (read from the scans), so a village starts where the numbering does. The table after
it, "Umrli u toku rata" (the dead of typhus, hunger and mines), is of civilians and stays out.

Each row's words are given to its columns by where they stand; a row's second line (the name, a unit or duty that
wraps) joins it. The entry's text is made of the columns: "Pužić Mile Dmitar, rođ. 1903, u NOV od 1941, pogib.
1943, Prijeboj; 2. č. 1. lič. odreda, k-dir voda" (the table's own abbreviations, the same for women).

Output: data-extraction/poreklo/licko-petrovo-selo-entries.json (IDs 9049xxxxxx: the village's letter times 100 plus
the row's number).
Usage: python data-extraction/parse_licko_petrovo_selo.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'licko-petrovo-selo.json'
OUT = HERE / 'poreklo' / 'licko-petrovo-selo-entries.json'
PREFIX = '9049'
PAGES = range(209, 217)
OFFSET = 2                                  # scan page minus the book's page
TITLE = 'Da se ne ponovi: Ratna kronika ranije općine Ličko Petrovo Selo'
LIST = 'Pali borci'
VILLAGES = ['Ličko Petrovo Selo', 'Novo Selo', 'Željava', 'Arapov Do', 'Rešetar', 'Zaklopača i Lisina',
            'Donji Vaganac']
# the columns' left edges in the scan's pixels: name, born, joined, died, place, unit, duty, note
COLUMNS = [('name', 560), ('born', 1300), ('joined', 1550), ('died', 1800), ('place', 2140), ('unit', 2530),
           ('duty', 2920), ('note', 3270)]
NUMBER = re.compile(r'^(\d{1,2})\s*\.')
# names and words the OCR garbled, as printed -> as on the page
FIX = {'PuZiČ': 'Pužić', 'Puzić_': 'Pužić', 'Реје': 'Pere', 'Рапе': 'Pane', 'Gtgić': 'Grgić', 'Dure': 'Đure',
       'Duka': 'Đuka', 'Priiebpi': 'Prijeboj', 'Očiicvo': 'Očijevo', 'chcngora': 'Crna Gora', 'lie.': 'lič.',
       'не.': 'lič.', 'ит.': '2.', 'um.': '2.', 'РО': 'PO', 'Sluni': 'Slunj', 'Kosini': 'Kosinj', 'Boiica': 'Božica',
       # the bold names' Đ read as V or D ("Vigo", "Dum" for Đuro, checked on the scans), П as Р
       'Vigo': 'Đuro', 'Dum': 'Đuro', 'Бигс': 'Đure', 'Reje': 'Peje', 'Мапе': 'Mane', 'Priieboi': 'Prijeboj',
       'Polianak': 'Poljanak', 'Loviniac': 'Lovinac', 'Prijcboj': 'Prijeboj', 'Jezeree': 'Jezerce'}
# a line of the header the table repeats on each page
HEADER = re.compile(r'^(?:red|br)\.|^NOV$|PALI BORCI|^\S\)\s|Prezim|očevo|očcvo|ime\s*i\s*ime|jedinica|primj?ie?d')


def column(x: float) -> str:
    name = 'number'
    for col, left in COLUMNS:
        if x >= left - 20:
            name = col
    return name


def rows(book: dict) -> list[dict]:
    out, cur, village, last = [], None, -1, 0
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            text = l.text.strip()
            if HEADER.search(text) or re.fullmatch(r'\d{3}', text):
                continue
            m = NUMBER.match(text)
            # a number the OCR misread ("в." for 8., "“3."): a short word with a full stop in the number's column
            first = l.words[0]
            misread = not m and first.x0 < 560 and len(first.text) <= 4 and first.text.endswith('.') and cur
            if misread:
                m = re.match(r'(\d+)', str(last + 1))
            # a row whose number the OCR lost: a name and its birth year where the row before has one already, or
            # the row's surname again after its name is whole ("Šorak Sime Mane" / "Šorak Steve Dane")
            name_words = [w.text for w in l.words if column(w.x0) == 'name']
            lost = (not m and cur and l.words[0].x0 >= 540 and (
                cur['cells'].get('born') and any(column(w.x0) == 'born' and re.fullmatch(r'1[89]\d\d', w.text)
                                                 for w in l.words)
                or len(cur['cells'].get('name', [])) >= 3 and name_words[:1] == cur['cells']['name'][:1]))
            if lost:
                last += 1
                cur = {'village': village, 'no': last, 'page': page, 'cells': {}}
                out.append(cur)
                words = l.words
            elif m and l.words[0].x0 < 560:
                n = int(m.group(1))
                if n == 1 or n < last:
                    village += 1                         # the next village's table
                last = n
                cur = {'village': village, 'no': n, 'page': page, 'cells': {}}
                out.append(cur)
                words = l.words[1:]
            elif cur:
                words = l.words
            else:
                continue
            for w in words:
                t = FIX.get(w.text, w.text)
                t = FIX.get(latin(t), latin(t)) if re.search('[Ѐ-ӿ]', t) else t   # Cyrillic look-alikes
                cur['cells'].setdefault(column(w.x0), []).append(t.replace(']', 'J'))
    return out


def main():
    book = load(BOOK)
    entries, counts = [], Counter()
    for r in rows(book):
        c = {k: ' '.join(v) for k, v in r['cells'].items()}
        # the names as printed (the book is in Latin), the scan's specks and a stray comma left out
        name = [w.strip(',.') for w in c.get('name', '').replace('_', '').split() if re.search(r'\w{2}', w)]
        if len(name) < 2:
            counts['unreadable'] += 1
            print('unreadable:', r)
            continue
        last, first = name[0], name[-1]
        father = name[1] if len(name) >= 3 else ''
        years = {k: (re.search(r'1[89]\d\d', c.get(k, '')) or [''])[0] for k in ('born', 'joined', 'died')}
        village = VILLAGES[r['village']]
        parts = [f"{' '.join(name)}"]
        if years['born']:
            parts.append(f"rođ. {years['born']}")
        if years['joined']:
            parts.append(f"u NOV od {years['joined']}")
        died = f"pogib. {years['died']}" if years['died'] else ''
        if c.get('place'):
            died = f"{died}, {c['place']}" if died else c['place']
        if died:
            parts.append(died)
        info = ', '.join(parts)
        rest = [c[k] for k in ('unit', 'duty', 'note') if c.get(k)]
        if rest:
            info += '; ' + ', '.join(rest)
        entries.append({
            'soldier_id': f"{PREFIX}{(r['village'] + 1) * 100 + r['no']:06d}",
            'name': ' '.join(name), 'last_name': last, 'first_name': first, 'nick': '', 'fathers_name': father,
            'birth_year': years['born'], 'born_in': f'{village}, Ličko Petrovo Selo',
            'death_year': years['died'],
            **({'death_place': c['place']} if c.get('place') else {}),
            'survived': False,
            'additional_info': info + '.',
            'list': f'{LIST}: {village}', 'book_title': TITLE,
            'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET,
        })
        counts[village] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))


if __name__ == '__main__':
    main()
