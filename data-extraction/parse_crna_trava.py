"""
*Црна Трава и Црнотравци* (Radomir Kostadinović, the Crna Trava SUBNOR, 1966?; Poreklo library, doc 00006272), a book
across units: its lists at the end (scan pp. 496-511, book pp. 524-539), in Cyrillic:

    "Народни хероји поникли из Црнотравског (Другог јужноморавског) одреда" (p. 524): twelve, a line each;
    "Они који су у наше данас и сутра уградили своје животе" (pp. 525-538): the dead of the war by village, numbered,
        "Анђелковић Ј. Дејан 1944. Брод", the fighters first ("Погинули од:" whom, where, the unit: "Симоновић В.
        Давид 1945. Немаца Срем XII бригада"), then each village's "Жртве фашистичког терора", which are out;
    the holders of the Spomenica 1941 (p. 539), names in two columns.

The OCR reads Д and Л as А ("Аејан" Dejan, "ВАадичин" Vladičin): each word of a name is read as the variant the
site's names know best (`best`).

Output: data-extraction/poreklo/crna-trava-entries.json (IDs 9125xxxxxx: the heroes 000001-000012, the fallen from
001001 in the list's order, the spomenica's holders from 002001).
Usage: python data-extraction/parse_crna_trava.py
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_lines, viewer_url  # noqa: E402

BOOK = 'crna-trava.json'
OUT = HERE / 'poreklo' / 'crna-trava-entries.json'
PREFIX = '9125'
OFFSET = -28                                 # scan page minus the book's page (scan 496 is p. 524)
TITLE = 'Crna Trava i Crnotravci'
HEROES = 'Narodni heroji ponikli iz Crnotravskog (Drugog južnomoravskog) odreda'
FALLEN = 'Oni koji su u naše danas i sutra ugradili svoje živote'
SPOMENICA = 'Nosioci „Spomenice 1941”'
MUNICIPALITY = 'Crna Trava'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
CONF = {'А': 'АДЛ', 'Б': 'БЂ', 'ћ': 'ћђ', 'Ћ': 'ЋЂ', 'Н': 'НЛ', 'д': 'дл'}
VILLAGE_READ = {'Maačište I Bajince': 'Mlačište i Bajince', 'Kaana I Krivi Aea': 'Kalna i Krivi Del',
                'Pavaičine': 'Pavličine', 'Krstibevo': 'Krstićevo', 'G R A A S K A': 'Gradska'}


def variants(word: str):
    choices = [CONF.get(c, c) if c.isupper() or c in 'ћд' else c for c in word]
    n = 1
    for c in choices:
        n *= len(c)
    return [word] if n > 512 else [''.join(p) for p in itertools.product(*choices)]


def best(word: str, part: str) -> str:
    word = word.strip('.,;:\'"“)(')
    if not word:
        return ''
    if re.search(r'\s*[-–]\s*', word):                     # "Стојичић-Филиповић", "Синадиновић – Гигић"
        return '-'.join(best(x, part) for x in re.split(r'\s*[-–]\s*', word) if x)
    word = re.sub(r'нћ$', 'ић', word.replace('Аоуб', 'Љуб').replace('ии', 'ин'))   # "Аоубомир", "Аоубнћ"
    table = V.T._names if part == 'last' else V.T._given
    top = max(variants(word), key=lambda c: (table[latin(c.upper())], -sum(a != b for a, b in zip(c, word))))
    return latin(top[0] + top[1:].lower()) if table[latin(top.upper())] else latin(word[0] + word[1:].lower())


def fix_text(t: str) -> str:
    """the duty and place as printed, the OCR's А for Д and Л inside words put back"""
    t = re.sub(rf'(?<=[{CL}])А(?=[{CL}])', 'л', t)                                   # "ВАадичин"
    t = re.sub(r'\bА(?=[аеиоуј])', 'Д', t)                                             # "Аејан", "Аимитријевић"
    return t.replace('сеАо', 'село').replace('сеАу', 'селу')


def lines(book: dict, page: int, columns: int = 1):
    for col in page_lines(book, page, columns):
        for l in col:
            t = l.text.strip()
            if t and not re.fullmatch(r'\d{3}', t):
                yield t


ENTRY = re.compile(rf'^\W*(\d{{1,3}})?\s*\.?\s*([{CU}][{CU}{CL}]+(?:\s*[-–]\s*[{CU}][{CU}{CL}]+)?)\s+(?:([{CU}А])\.\s*)?'
                   rf'([{CU}][{CU}{CL})]+)\s+(?:\d{{1,2}}\s*\.\s*(?:\d{{1,2}}|[XIVLХП]+)\s*\.?\s*)?(19\d\d)\.?\s*(.*)$')
SPOM = re.compile(rf'(\d{{1,2}})\s*\.?\s*([{CU}][{CU}{CL}]+(?:\s*[-–]\s*[{CU}][{CU}{CL}]+)?)\s+(?:([{CU}А])\.\s*)?'
                  rf'([{CU}][{CU}{CL}]+)')


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    # the heroes (scan 496)
    n = 0
    for t in lines(book, 496):
        m = re.match(rf'^\W*(\d{{1,2}})?\s*\.?\s*([{CU}][{CL}]+)\s+([{CU}][{CL}]+)(?:\s+([{CU}][{CL}]+))?\s*[,.]?\s*(.*)$', t)
        if not m or 'НАРОАНИ' in t or 'поникди' in t:
            if entries and entries[-1]['list'] == HEROES and t and not re.match(r'^\W*\d', t):
                entries[-1]['_text'] += ' ' + t
            continue
        n += 1
        given, last, nick = best(m.group(2), 'first'), best(m.group(3), 'last'), latin(m.group(4)) if m.group(4) else ''
        entries.append({'soldier_id': f'{PREFIX}{n:06d}', 'last_name': last, 'first_name': given, 'nick': nick,
                        'fathers_name': '', '_text': fix_text(m.group(5)), 'list': HEROES, 'page': 496,
                        'survived': not re.search(r'[Пп]огин', m.group(5)), 'born_in': ''})
    # the fallen (scan 497-511)
    village, victims, n = MUNICIPALITY, False, 0
    for page in range(497, 512):
        for t in lines(book, page):
            bare = re.sub(rf'[^{CU} ]', '', t).strip()
            if 'ЖРТВЕ' in t or 'ЖФТ' in t:
                victims = True
                continue
            if bare and bare == t.strip() and len(bare) > 3 and not re.search(r'\d', t) and 'ОНИ' not in bare:
                village, victims = latin(bare.title()), False
                village = VILLAGE_READ.get(village, village)
                continue
            if 'Имена 32 бораца' in t or 'Споменике' in t:
                break
            m = ENTRY.match(t)
            if not m or victims:
                if m:
                    counts['victims out'] += 1
                continue
            no, last, init, given, year, rest = m.groups()
            n += 1
            father = latin(init.replace('А', 'Д')) if init else ''
            last_l, given_l = best(last, 'last'), best(given, 'first')
            rest = fix_text(rest)
            entries.append({'soldier_id': f'{PREFIX}{1000 + n:06d}', 'last_name': last_l, 'first_name': given_l,
                            'nick': '', 'fathers_name': father, 'death_year': year, 'list': FALLEN, 'page': page,
                            '_text': f"{no + '. ' if no else ''}{last_l} {father + '. ' if father else ''}{given_l}, {year}. "
                                     f"{V.read_cyr(rest)}".strip(), 'survived': False,
                            'born_in': f'{village}, {MUNICIPALITY}' if village != MUNICIPALITY else MUNICIPALITY,
                            '_village': village})
            counts['fallen'] += 1
    # the spomenica (scan 511, two columns run into one line)
    on, n = False, 0
    for t in lines(book, 511):
        if 'Имена 32' in t:
            break
        on = on or bool(re.match(r'^\W*\d', t))
        for m in SPOM.finditer(t):
            last, init, given = m.group(2), m.group(3), m.group(4)
            n += 1
            last_l, given_l = best(last, 'last'), best(given, 'first')
            father = latin(init.replace('А', 'Д')) if init else ''
            entries.append({'soldier_id': f'{PREFIX}{2000 + int(m.group(1)):06d}', 'last_name': last_l,
                            'first_name': given_l, 'nick': '', 'fathers_name': father, 'list': SPOMENICA, 'page': 511,
                            '_text': f"{m.group(1)}. {last_l} {father + '. ' if father else ''}{given_l}",
                            'survived': True, 'born_in': ''})
            counts['spomenica'] += 1
    seen, out = set(), []
    for e in entries:
        if e['soldier_id'] in seen:
            continue
        seen.add(e['soldier_id'])
        info = e['_text'] if e['list'] != HEROES else V.read_cyr(e['_text'])
        d = V.death(info) if e['list'] == HEROES else {}
        born = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*\S+\s+)?(1[89]\d\d)', info)
        name = ' '.join(x for x in (e['last_name'], e['fathers_name'], e['first_name']) if x)
        out.append({'soldier_id': e['soldier_id'], 'name': name, 'last_name': e['last_name'], 'also': [],
                    'first_name': e['first_name'], 'nick': e['nick'], 'fathers_name': e['fathers_name'],
                    'birth_year': born.group(1) if born else '', 'born_in': e['born_in'],
                    'death_year': e.get('death_year') or d.get('year', ''),
                    'survived': e['survived'], 'units': V.units_of(info),
                    'additional_info': f"{e['list']}{', ' + e['_village'] if e.get('_village') else ''}: {info}.",
                    'list': e['list'], 'book_title': TITLE, 'source_url': viewer_url(book, e['page']),
                    'source_page': e['page'] - OFFSET})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(out), 'entries ->', OUT.name, dict(counts))
    for e in out:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['born_in']} | {e['death_year']} | {e['additional_info'][:90]}")


if __name__ == '__main__':
    main()
