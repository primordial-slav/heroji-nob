"""
60 година школе Биновце и Калабовце (Poreklo library, doc 00007234), the villages of Binovce and Kalabovce by
Surdulica, as a book across units. Cyrillic, names alone, two columns, numbered:
    "Учесници НОР-а из Биновца" (scan pp. 26-27, book pp. 24-25, 57 names) and "Учесници НОР-а из Калабовца" (p. 27,
        38): the surname, the father's initial and the given name ("Златановић С. Стојан"). The book names them the
        participants of the war and no more, so they go in marked `role: 'participant'` (the user's rule of
        2026-10-20 for such lists);
    "Погинули борци у НОБ-у од 1941-1945. године" (p. 28, book p. 26): five fighters, the given name first, the
        father in the genitive between ("Вера Љубисава Јовић").
Out: the soldier killed in the April war, the victims of terror and the civilians of p. 28, the forced labourers and
the men the Bulgarians interned (pp. 23-26).

Output: data-extraction/poreklo/binovce-entries.json (IDs 9098xxxxxx: Binovce's participants from 000001, Kalabovce's
from 000101, the fallen from 000201, by the book's number).
Usage: python data-extraction/parse_binovce.py
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
import _village_books as V  # noqa: E402
from poreklo_text import load, page_lines, viewer_url  # noqa: E402

BOOK = 'binovce.json'
OUT = HERE / 'poreklo' / 'binovce-entries.json'
PREFIX = '9098'
OFFSET = 2                                  # scan page minus the book's page
TITLE = '60 godina škole Binovce i Kalabovce'
LISTS = {'binovce': ('Učesnici NOR-a iz Binovca', 0), 'kalabovce': ('Učesnici NOR-a iz Kalabovca', 100),
         'fallen': ('Poginuli borci u NOB-u od 1941—1945. godine', 200)}
VILLAGE = {'binovce': 'Binovce, Surdulica', 'kalabovce': 'Kalabovce, Surdulica', 'fallen': ''}
UC = 'А-ЯЂЈЉЊЋЏ'
# the five fallen, given name first, the father in the genitive (as printed, p. 28)
FALLEN = [(1, 'Jović', 'Ljubisava', 'Vera'), (2, 'Batić', 'Dragutina', 'Božidar'), (3, 'Milenković', 'Milutina', 'Gradimir'),
          (4, 'Milenković', 'Đore', 'Milutin'), (5, 'Filipović', 'Dušana', 'Radomir')]
FALLEN_NICK = {5: 'Rade'}
# the OCR's slips in the names, read from the other lists of the book (the interned men of p. 25 name the same people)
FIX = {'Јовић В. Новина': 'Јовић В. Новица', 'Цветковић Милс': 'Цветковић Миле', "С'гавановић Д Драгољуб": 'Стевановић Д. Драгољуб',
       'Сласић В. Стојан': 'Спасић В. Стојан', 'Трајковић Р. ЈБубиша': 'Трајковић Р. Љубиша'}


def numbered(book: dict, page: int) -> list[tuple[int, str, str]]:
    """the page's numbered names, column by column: (number, name, list)"""
    out = []
    kind = None
    for col in page_lines(book, page, 2):
        for l in col:
            t = re.sub(r'(?<=[а-яђјљњћџ]) 3\. ', ' З. ', l.text.strip())        # the initial З read as the digit 3
            t = t.replace('сврћ', 'евић').replace('Ђорђсвић', 'Ђорђевић').replace('ћсвић', 'ћевић')
            if 'ИЗ БИНОВЦА' in t:
                kind = 'binovce'
            elif 'ИЗ КАЛАБОВЦА' in t:
                kind = 'kalabovce'
            for m in re.finditer(rf"(\d{{1,2}})\s*\.\s*((?:['’\"]?[{UC}ћ][^\d]*?))(?=\s+\d{{1,2}}\s*\.|$)", t):
                out.append((int(m.group(1)), m.group(2).strip(' .'), kind, l.top))
    return out


def main():
    book = load(BOOK)
    entries, counts = [], Counter()
    seen = set()
    items = []
    for page in (26, 27):
        lines = page_lines(book, page, 1)[0]
        heads = {('binovce' if 'БИНОВЦА' in l.text else 'kalabovce'): l.top for l in lines if 'УЧЕСНИЦИ НОР' in l.text.upper()}
        for no, name, _, top in numbered(book, page):
            if page == 26 and ('binovce' not in heads or top < heads['binovce']):
                continue                                    # the interned men above the list
            kind = 'kalabovce' if 'kalabovce' in heads and top > heads['kalabovce'] else 'binovce'
            if (kind, no) in seen:
                continue
            seen.add((kind, no))
            items.append((kind, no, name, page))
    for kind, no, name, page in sorted(items, key=lambda x: (x[0] != 'binovce', x[1])):
        name = FIX.get(name, name)
        cyr = re.sub(r"['’\"]?[Бћ][Оо]р[ђћ]", 'Ђорђ', re.sub(r"['’\"]ћор", 'Ђор', name))
        words = cyr.replace('.', '. ').split()
        last = V.name_word(words[0]).replace('Đorćević', 'Đorđević')
        initial = next((w for w in words[1:-1] if re.fullmatch(rf'[{UC}A-Z3]\.?', w)), '')
        first = V.given_word(words[-1]) if len(words) > 1 else ''
        initial = V.read_cyr(initial.replace('3', 'З').rstrip('.')) + '.' if initial else ''
        title, base = LISTS[kind]
        entries.append({
            'soldier_id': f'{PREFIX}{base + no:06d}', 'name': ' '.join(x for x in (last, initial, first) if x),
            'last_name': last, 'also': [], 'first_name': first, 'nick': '', 'fathers_name': initial,
            'birth_year': '', 'born_in': VILLAGE[kind], 'death_year': '', 'survived': False, 'units': [],
            'role': 'participant',
            'additional_info': f"{title}: {no}. {' '.join(x for x in (last, initial, first) if x)}",
            'list': title, 'book_title': TITLE,
            'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
        counts[kind] += 1
    for no, last, fath, first in FALLEN:
        title, base = LISTS['fallen']
        entries.append({
            'soldier_id': f'{PREFIX}{base + no:06d}', 'name': f'{last} {fath} {first}', 'last_name': last, 'also': [],
            'first_name': first, 'nick': FALLEN_NICK.get(no, ''), 'fathers_name': fath, 'birth_year': '',
            'born_in': 'Binovce, Surdulica', 'death_year': '', 'survived': False, 'units': [],
            'additional_info': f"{title}: {no}. {first}{'-' + FALLEN_NICK[no] if no in FALLEN_NICK else ''} {fath} {last}",
            'list': title, 'book_title': TITLE, 'source_url': viewer_url(book, 28), 'source_page': 28 - OFFSET})
        counts['fallen'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    for kind, n in (('binovce', 57), ('kalabovce', 38)):
        nos = {int(e['soldier_id'][-3:]) - LISTS[kind][1] for e in entries if e['list'] == LISTS[kind][0]}
        print(kind, 'missing', [i for i in range(1, n + 1) if i not in nos])
    print([e['name'] for e in entries][:200])


if __name__ == '__main__':
    main()
