"""
Горња Јабланица кроз историју (Poreklo library, doc 00002500), the Gornja Jablanica area of the Medveđa
municipality, as a book across units. Its chapter "Слобода најузвишенији идеал Горњојабланичана" (scan pp. 663-673,
the book's pages too), Cyrillic, one column with the photographs' captions between:
    "Народни хероји и други погинули првоборци НОР-а": four narodni heroji, a bio each ("Ајдиновић Зејнел – Тоша (р.
        1910), из Тупала, првоборац, ... Погинуо је 7. марта 1942. ..."), then the first fighters of 1941 who fell,
        names alone under each village (Бучумет, Велики Брајина, Гајтан, ...), from the SUBNOR board's records and the
        units' books;
    "Носиоци Партизанске споменице 1941. године", names alone under each village; they lived through the war.
Out: the holders of the Albanian spomenica and the Karađorđe star (the wars of 1912-1918), and the chapter on the
area's people in high posts during the war and after it (p. 674 on), not a list of fighters.

Output: data-extraction/poreklo/gornja-jablanica-entries.json (IDs 9101xxxxxx: the heroes from 000001, the fallen
from 000101, the spomenica holders from 000301, in the book's order).
Usage: python data-extraction/parse_gornja_jablanica.py
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
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'gornja-jablanica.json'
OUT = HERE / 'poreklo' / 'gornja-jablanica-entries.json'
PREFIX = '9101'
TITLE = 'Gornja Jablanica kroz istoriju'
HEROES = 'Narodni heroji i drugi poginuli prvoborci NOR-a'
FALLEN = 'Narodni heroji i drugi poginuli prvoborci NOR-a, poginuli borci NOR-a od 1941. godine iz Gornje Jablanice'
SPOMENICA = 'Nosioci Partizanske spomenice 1941. godine'
MUNICIPALITY = 'Medveđa'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# village headings the OCR garbled, as the captions under the photographs spell them
VILLAGES = {'Гајшан': 'Гајтан', 'Г ајшан': 'Гајтан', 'Božynoeau': 'Боговинац', 'НеЕосавље': 'Негосавље',
            'стубла': 'Стубла', '(lomu—mn': ''}


# the captions' second lines under the photographs, set among the names ("Бучумет Бучумет", "Стубле Сшубле")
CAPTION_LEFTOVERS = {'Бучумет Бучумет', 'Стубле Сшубле', 'Црног Врха', '. . > . . _ .w; ;, i, з ili??): . ·'}
# names the OCR garbled or ran into a caption, read from the page: line as read -> line
READ = {"Бадњар 'Боко": 'Бадњар Ђоко', "Вукадиновић М. 'Борђије Брајднг": 'Вукадиновић М. Ђорђије',
        'Ј ововићМарко': 'Јововић Марко', 'Ковачевић О. Сава спева" жудић "3 Гајтан“': 'Ковачевић О. Сава',
        'Ј овчић Тихомир – Тадија': 'Јовчић Тихомир – Тадија', 'Булатовић Вукој е': 'Булатовић Вукоје',
        "Жутић 'Борђе": 'Жутић Ђорђе', 'Г огић Петар – Мићун': 'Гогић Петар – Мићун', "'ћаловић Миле": 'Ћаловић Миле',
        'Томановић Милутин – Никад Владимир Перошевић–': 'Томановић Милутин – Никад'}


def lines(book: dict) -> list[tuple[int, object]]:
    out = []
    for page in range(663, 675):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.fullmatch(r'\d{3}|[\W\d_]{1,12}', t):
                continue
            out.append((page, l))
    return out


def main():
    book = load(BOOK)
    entries, counts = [], Counter()
    section, village, heroes = None, '', []
    for page, l in lines(book):
        t = l.text.strip()
        if t.startswith('Народни хероји и други'):
            section = 'heroes'
            continue
        if t.startswith('Поред народ') and 'хероја' in t:
            section = 'pre-fallen'
            continue
        if section == 'pre-fallen' and t.startswith('1941. године из'):
            section = 'fallen'
            continue
        if t.startswith('Носиоци Партизанске'):
            section, village = 'spomenica', ''
            continue
        if t.startswith('* Овде се даје списак'):
            section = 'skip' if section == 'fallen' else 'end'
            continue
        if section == 'end':
            break
        if section == 'heroes':
            if l.x0 > 3700 and re.match(rf'[{UC}][{LC}]+\s+(?:[{UC}0]\.\s+)?[{UC}][{LC}]+\s*[–—-]', t):
                heroes.append({'page': page, 'lines': [t]})
            elif heroes and l.x0 < 3300 and not re.search(r'\sиз\s|херој', t):
                heroes[-1]['lines'].append(t)
            continue
        if section not in ('fallen', 'spomenica'):
            continue
        # a photograph's caption: names with "из" and the village, set under the photo
        if re.search(r'\sиз(?:\s|Д|$)|^из|Народни (?:херој|ерој)', t):
            continue
        if l.x0 < 3400:
            v = VILLAGES.get(t, t)
            if re.fullmatch(rf'[{UC}][{LC}]+(?:[ –-][{UC}{LC}][{LC}]+)?', v.replace('Г ај', 'Гај')):
                village = v.replace('Г ај', 'Гај')
            continue
        if t in CAPTION_LEFTOVERS:
            continue
        t = READ.get(t, t)
        m = re.match(rf"^['’\"]?([{UC}Б][{LC}]+(?:[–-][{UC}][{LC}]+)?)\s+(?:([{UC}])[.,]\s+)?(?:др\s+)?([{UC}][{LC}]+(?:\s+[{UC}][{LC}]+)?)"
                     rf"(?:\s*[–—-]\s*(.+))?$", t)
        if not m:
            print('  ?', page, t)
            continue
        sur = re.sub(r"^['’\"]?Б", 'Ђ', t[:1] + m.group(1)) if t[:1] in "'’\"" else m.group(1)
        last = '-'.join(V.name_word(x) for x in re.split(r'[–-]', sur))
        first = V.given_word(m.group(3).split()[0])
        initial = V.read_cyr(m.group(2)) + '.' if m.group(2) else ''
        nick = V.read_cyr(m.group(4)).strip() if m.group(4) else ''
        vil = V.read_cyr(village) if village else ''
        kind = section
        base = 100 if kind == 'fallen' else 300
        counts[kind] += 1
        no = counts[kind]
        title = FALLEN if kind == 'fallen' else SPOMENICA
        printed = ' '.join(x for x in (last, initial, first) if x) + (f' – {nick}' if nick else '')
        entries.append({
            'soldier_id': f'{PREFIX}{base + no:06d}', 'name': ' '.join(x for x in (last, initial, first) if x),
            'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': initial,
            'birth_year': '', 'born_in': f'{vil}, {MUNICIPALITY}' if vil else '', 'death_year': '',
            'survived': kind == 'spomenica', 'units': [],
            'additional_info': f'{title}, {vil}: {printed}' if vil else f'{title}: {printed}',
            'list': title, 'book_title': TITLE, 'source_url': viewer_url(book, page), 'source_page': page})
    for no, h in enumerate(heroes, 1):
        text = re.sub(r'\s+', ' ', V.unhyphen(' '.join(h['lines'])))
        info = V.read_cyr(text)
        m = re.match(rf'^([{UC}][{LC}]+)\s+(?:([{UC}0])\.\s+)?([{UC}][{LC}]+)\s*[–—-]\s*([^(]+?)\s*\(р\.\s*(1[89]\d\d)\)', text)
        last, initial, first, nick, year = V.name_word(m.group(1)), m.group(2), V.given_word(m.group(3)), \
            V.read_cyr(m.group(4)), m.group(5)
        initial = (V.read_cyr(initial.replace('0', 'О')) + '.') if initial else ''
        born = re.search(r'\biz\s+([A-ZČĆŽŠĐ]\w+)', info)
        d = V.death(info)
        entries.append({
            'soldier_id': f'{PREFIX}{no:06d}', 'name': ' '.join(x for x in (last, initial, first) if x),
            'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': initial,
            'birth_year': year, 'born_in': f'{born.group(1)}, {MUNICIPALITY}' if born else '',
            'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
            **({'death_place': d['place']} if d.get('place') else {}),
            'survived': False, 'units': V.units_of(info),
            'additional_info': f'{HEROES}: {info} Narodni heroj.', 'list': HEROES, 'book_title': TITLE,
            'source_url': viewer_url(book, h['page']), 'source_page': h['page']})
        counts['heroes'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    for e in entries:
        print(' ', e['soldier_id'][-3:], e['name'], '—', e['nick'], '|', e['born_in'], '|', e['additional_info'][:60])


if __name__ == '__main__':
    main()
