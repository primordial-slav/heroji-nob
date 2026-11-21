"""
*Источна Тамнава – Бргуле и околина* (Biblioteka "Hronika sela"; Poreklo library, doc 00000484), a book across units:
two of the lists of its eight villages by Ub (Brgule, Radljevo, Kalenić, Šarbane, Liso Polje, Stublenica, Mali Borak,
Skobalj), in Cyrillic:

    The citizens who died in 1941-1945, by village (scan pp. 541-547): "45. Радуловић Теодосија Милорад, рођен 1920,
        погинуо на Сремском фронту 1945. године." The list counts everyone: the men who fell with the army of 1944-1945,
        the hostages shot, the internees, children killed by a bomb, and, in a district of both movements, men killed
        at home in 1941-1943 whose side it doesn't say. Only those who fell on the fronts of the liberation army in
        1944-1945 (Srem, Slavonia, the push to Zagreb and Maribor; `FRONT`) are taken, as fighters.
    "Носиоци Партизанске споменице 1941. године" (p. 550): ten, by village.

Out: the holders of the Albanian Commemorative Medal (the First World War) and the April war's prisoners.

Output: data-extraction/poreklo/istocna-tamnava-entries.json (IDs 9121xxxxxx: the fallen from 000001 in the list's
order, the spomenica's holders from 001001).
Usage: python data-extraction/parse_istocna_tamnava.py
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
from parse_ostrvica import level_lines  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'istocna-tamnava.json'
OUT = HERE / 'poreklo' / 'istocna-tamnava-entries.json'
PREFIX = '9121'
OFFSET = 4                                   # scan page minus the book's page (scan 541 is p. 537)
TITLE = 'Istočna Tamnava – Brgule i okolina'
FALLEN = 'Poginuli građani 1941–1945.'
SPOMENICA = 'Nosioci „Partizanske spomenice 1941. godine”'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
VILLAGES = {'Бргуле': 'Brgule', 'Радљево': 'Radljevo', 'Каленић': 'Kalenić', 'Шарбане': 'Šarbane',
            'Шарбапе': 'Šarbane', 'Лисо Поље': 'Liso Polje', 'Стубленица': 'Stublenica', 'Мали Борак': 'Mali Borak',
            'Мали Барак': 'Mali Borak', 'Скобаљ': 'Skobalj'}
# the fronts of the liberation army in 1944-1945
FRONT = re.compile(r'Срем|Шид|Товарник|Опатов|Илок|Ловас|Бабск|Оглађенов|Славонск|Загреб|Марибор|Плетерниц|Хрватској 1945|'
                   r'Вуковар|Винковц|Осијек|Нашиц|Дравск|Бјеловар|Банст|Батин|Митровиц|Мохов|Земун|Вировитиц|Слатин|'
                   r'Карловц|Словениј|Трст|Дрин')
ENTRY = re.compile(rf'^(\d{{1,3}})\s*\.\s*([{CU}][{CL}]+)\s+(?:([{CU}][{CL}]+|[{CU}]\.)\s+)?([{CU}][{CL}]+)\s*[,.]\s*(.*)$')


def lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = re.sub(r"^['\"]?ћ", 'Ђ', l.text.strip())
            t = re.sub(r'(\d+)\.(?=[{0}])'.format(CU), r'\1. ', t)
            if not re.fullmatch(r'[\d\s.]{1,5}', t):
                out.append((page, t))
    return out


def main():
    V.corpus()
    book = load(BOOK)
    raw, village, rest = [], '', False
    for page, t in lines(book, range(540, 548)):
        if t.startswith('Рекапитулација') and page > 540:
            break
        mv = re.match(r'^,?\s*([{0}][{1}]+(?:\s[{0}][{1}]+)?)\s*[—–←-]\s*(?:\d[\d ]*)\s*грађан'.format(CU, CL), t)
        if mv:
            village, rest = VILLAGES.get(mv.group(1), latin(mv.group(1))), False
            continue
        if not village:
            continue
        if t.startswith('Остали погинули'):
            rest = True                                    # names alone: no word of how they died
            continue
        m = ENTRY.match(t)
        if m and not rest:
            raw.append({'page': page, 'village': village, 'no': m.group(1), 'g': m.groups()[1:4], 'text': m.group(5)})
        elif raw and not rest and not re.match(r'^\d', t):
            raw[-1]['text'] += ' ' + t
    entries, counts = [], Counter()
    for r in raw:
        cyr = re.sub(r'\s+', ' ', r['text'])
        if not (FRONT.search(cyr) and re.search(r'19(?:44|45)', cyr)) or re.search(r'стрељ|интерн|логор', cyr):
            counts['out'] += 1
            continue
        last, fath, given = r['g']
        if re.search(r'ића$', given) or (fath and fath.endswith('.') and re.search(r'ић$', given)):
            last, given = given[:-1] if given.endswith('а') else given, last   # Šarbane's "Љубивој Милутина Ранковића"
        last, given = V.name_word(last), V.given_word(given)
        if given.endswith('a') and V.T._given[given[:-1].upper()] > V.T._given[given.upper()]:
            given = given[:-1]                                              # "Милорада"
        father = latin(fath) if fath else ''
        info = V.read_cyr(cyr).strip(' .')
        d = V.death(info)
        born = re.search(r'rođen[a]?\s+(1[89]\d\d)', info)
        name = ' '.join(x for x in (last, father, given) if x)
        entries.append({'soldier_id': f'{PREFIX}{len(entries) + 1:06d}', 'name': name, 'last_name': last, 'also': [],
                        'first_name': given, 'nick': '', 'fathers_name': father,
                        'birth_year': born.group(1) if born else '', 'born_in': f"{r['village']}, Ub",
                        'death_year': d.get('year', ''), **({'death_place': d['place']} if d.get('place') else {}),
                        'survived': False, 'units': V.units_of(info),
                        'additional_info': f"{FALLEN}, {r['village']}: {r['no']}. {name}, {info}.", 'list': FALLEN,
                        'book_title': TITLE, 'source_url': viewer_url(book, r['page']),
                        'source_page': r['page'] - OFFSET})
        counts['fighter'] += 1
    # the spomenica's ten, two villages a line ("из Каленића из Шарбана", then "1. Перић Вићентије 1. Јовановић ...")
    n, on, cols = 0, False, []
    for page, t in lines(book, [550]):
        if 'Партизанске споменице' in t:
            on = True
            continue
        if not on:
            continue
        if t.startswith('Укупно'):
            break
        heads = re.findall(r'из\s+([{0}][{1}]+(?:\s[{0}][{1}]+)?)'.format(CU, CL), t)
        names = re.findall(r'\d\s*\.\s*([{0}][{1}]+)\s+(?:\(([{0}][{1}]+)\)\s+)?([{0}][{1}]+)(?:\s+\(([{0}][{1}]+)\))?'
                           .format(CU, CL), t)
        if heads and not names:
            cols = heads
            continue
        if heads and names:                                 # "3. Марковић Алекса из Стубленице"
            cols = [cols[0], heads[-1]] if cols else heads
        for i, (last, other, given, nick) in enumerate(names):
            where = cols[i] if i < len(cols) else (cols[-1] if cols else '')
            n += 1
            last_l, given_l = V.name_word(last), V.given_word(given)
            vil = {'Каленића': 'Kalenić', 'Шарбана': 'Šarbane', 'Радљева': 'Radljevo', 'Малог Борка': 'Mali Borak',
                   'Стубленице': 'Stublenica'}.get(where, latin(where))
            printed = f"{last_l}{' (' + latin(other) + ')' if other else ''} {given_l}{' (' + latin(nick) + ')' if nick else ''}"
            entries.append({'soldier_id': f'{PREFIX}{1000 + n:06d}', 'name': f'{last_l} {given_l}', 'last_name': last_l,
                            'also': [V.name_word(other)] if other else [], 'first_name': given_l,
                            'nick': latin(nick) if nick else '', 'fathers_name': '', 'birth_year': '',
                            'born_in': f'{vil}, Ub' if vil else '', 'death_year': '', 'survived': True, 'units': [],
                            'additional_info': f'{SPOMENICA}, {vil}: {printed}.', 'list': SPOMENICA,
                            'book_title': TITLE, 'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
            counts['spomenica'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'read', len(raw))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} | {e['birth_year']} {e['born_in']} | {e['death_year']} "
              f"{e.get('death_place', '')} | {e['additional_info'][:90]}")


if __name__ == '__main__':
    main()
