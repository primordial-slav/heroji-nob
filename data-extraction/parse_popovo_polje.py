"""
Popovo polje u Narodnooslobodilačkoj borbi (Poreklo library, doc 00002554): its Prilog "Borci iz Popova polja pali
u NOR-u" (scan pp. 423-434, book pp. 419-430), as a book across units. One column, Latin, each entry hanging: "Akšam
Ilija, Burin, rođen 1917. godine u Čvaljini, borac. Poginuo u Zaslinju, Konjic, 17. februara 1945. godine." The
surname, the given name and the father as a possessive ("Burin", "Ristin"; a nickname after a dash, "Bošković
Radoslav — Rade, Ristin"), the village, the duty, where and when he fell. The list after it, the victims of fascist
terror of Popovo polje (book p. 431 on), is out and was not fetched.

Output: data-extraction/poreklo/popovo-polje-entries.json (IDs 9094xxxxxx, in the list's order).
Usage: python data-extraction/parse_popovo_polje.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import _village_books as V  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'popovo-polje.json'
OUT = HERE / 'poreklo' / 'popovo-polje-entries.json'
PREFIX = '9094'
OFFSET = 4                                   # scan page minus the book's page
TITLE = 'Popovo polje u Narodnooslobodilačkoj borbi'
LIST = 'Borci iz Popova polja pali u NOR-u'
MUNICIPALITY = 'Trebinje'                    # Popovo polje lies in the Trebinje and Ravno municipalities
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# an entry's first line: surname, given name (a nickname after a dash), the father's possessive, "rođen"
START = re.compile(rf"^([{U}][{L}]+(?:-[{U}][{L}]+)?)[.,]?\s*(?:[{U}]\.\s*)?\.?([{U}{L}][{L}]+"
                   rf"(?:\s*[—–.-]+\s*[{U}][{L}]+)?),\s*([{U}][\w -]{{1,14}}?),\s*[-_.\[\s]*(?:rođen|rOđen)")
LATIN = str.maketrans('аеорсухАВЕКМНОРСТХ', 'aeopcyxABEKMHOPCTX')


def page_lines(book: dict, page: int) -> list:
    words = page_words(book, page)
    return level_lines(words) if words else []


def raw_entries(book: dict) -> list[dict]:
    raw, started = [], False
    for page in range(423, 435):
        lines = page_lines(book, page)
        if not lines:
            continue
        left = min(l.x0 for l in lines if len(l.text) > 20)
        for l in lines:
            t = l.text.translate(LATIN).strip()
            t = re.sub(r"(?<=\w)['’“]+(?=\w)|(?<=\s)['’“]+(?=\w)", '', t).replace('á', 'a')   # "Jov'iri", "'Jovin"
            if 'BORCI IZ POPOVA POLJA' in t:
                started = True
                continue
            if not started or re.fullmatch(r'\d{3}|PALI U NOR-u|[:\W\d]{1,4}', t):
                continue
            if 'ŽRTVE' in t.upper() and 'TERORA' in t.upper():
                return raw
            m = START.match(t)
            if m and l.x0 < left + 400:
                raw.append({'page': page, 'names': m.groups(), 'lines': [t]})
            elif raw:
                raw[-1]['lines'].append(t)
    return raw


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[—–-]$', text) and re.match(rf'[{L}]', ln):
            text = re.sub(r'\s*[—–-]$', '', text) + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).replace(' ,', ',').replace('god-ine', 'godine').strip()


def main():
    ofz.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for no, r in enumerate(raw_entries(book), 1):
        sur, given, father = r['names']
        nick = ''
        given = given.lstrip('.')
        if re.search(r'[—–.-]', given):
            given, nick = [x.strip(' .') for x in re.split(r'\s*[—–.-]+\s*', given, 1)]
        given = given[:1].upper() + given[1:]
        father = father.replace('-', '').replace(' ', '')                # "Ris-tin", "J ovanov"
        last = '-'.join(kl.spelled(w, 'last') for w in re.split(r'[- ]', sur))
        first = kl.spelled(given, 'first')
        text = join(r['lines'])
        y = re.search(r'\brođen[a]?\s+(?:u\s+)?(1[89]\d\d)', text)
        born = re.search(rf'\bgodine\s+u\s+((?:[{U}][{L}]+\s?){{1,3}}?)(?=\s*[,.])', text)
        d = V.death(text)
        # the list's title names them all fighters; its rule marks the movement's people it names otherwise
        role = 'activist' if V.role(text) == 'activist' else None
        entries.append({
            'soldier_id': f'{PREFIX}{no:06d}', 'name': f'{last} {father.strip()} {first}', 'last_name': last, 'also': [],
            'first_name': first, 'nick': nick, 'fathers_name': father.strip(), 'birth_year': y.group(1) if y else '',
            'born_in': f'{born.group(1).strip()}, {MUNICIPALITY}' if born else '',
            'death_year': d.get('year', ''), **({'death_date': d['date']} if d.get('date') else {}),
            **({'death_place': d['place']} if d.get('place') else {}),
            'survived': False, 'units': V.units_of(text), **({'role': role} if role else {}),
            'additional_info': f'{LIST}: {text}', 'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET})
        counts[role or 'fighter'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    if '--sample' in sys.argv:
        random.seed(6)
        for e in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {e['name']} | {e['birth_year']} [{e['born_in']}] † {e['death_year']} {e.get('death_place', '')!r} "
                  f"{e['units']} | {e['additional_info'][:130]}")


if __name__ == '__main__':
    main()
