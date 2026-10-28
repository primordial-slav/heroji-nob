"""
Mlađen Jovanov Vučetić, *Grahovo u vrijeme rata 1941-1945: grahovske podjele* (Beograd 2020; doc 00009010 of the
Poreklo library), Grahovo by Nikšić, as a book across units, two of its appendices:
    Prilog 4, "Ubijeni i strijeljani partizanski pozadinski radnici iz Grahova od odlaska partizana za Bosnu (kraj
        maja 1942. do povratka 1943. godine)" (book pp. 237-238): 21 men, the father as a possessive or genitive, the
        birth year, a short bio: "Bulajić Simov Mirko (1906), član KPJ od 1936. godine. ... Ubijen od četnika.". The
        book counts them the movement's rear workers: a fighter by the mixed lists' rule (`_village_books.role`),
        else an activist;
    Prilog 8, "Spisak Grahovljana nosilaca Partizanske spomenice 1941. godine (borci od 1941-1945)" (book pp. 252-255):
        83 names, a line each, "Banićević Petra Vasilj — Srgo" (the numbers the OCR lost to specks).
Out: the book's table of the Chetniks' dead (Prilog 5), those the partisans killed (Prilog 6) and those killed
after the liberation (Prilog 7). Its partisans' fallen are the list of *Revolucionarno Grahovo* (parse_
revolucionarno_grahovo.py), which the book takes them from.

Output: data-extraction/poreklo/grahovo-podjele-entries.json (IDs 9109xxxxxx: the rear workers from 000001, the
spomenica holders from 001001).
Usage: python data-extraction/parse_grahovo_podjele.py
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

BOOK = 'grahovo-podjele.json'
OUT = HERE / 'poreklo' / 'grahovo-podjele-entries.json'
PREFIX = '9109'
OFFSET = 1                                  # scan page minus the book's page
BOOK_TITLE = 'Grahovo u vrijeme rata 1941-1945: grahovske podjele'
REAR = ('Ubijeni i strijeljani partizanski pozadinski radnici iz Grahova (1942-1943)', range(238, 240))
SPOMENICA = ('Grahovljani nosioci Partizanske spomenice 1941. godine', range(253, 257))
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
NAME = re.compile(rf'([{U}][{L}]+(?:-[{U}][{L}]+)?)\s+([{U}][{L}]+|[{U}]\.|\?)\s+([{U}][{L}]+)(?:\s*[–—-]\s*([{U}][{L}]+))?')


REAR_NAME = re.compile(rf'([{U}][{L}]+)\s+(?:([{U}][{L}]+|[{U}]\.)\s+)?([{U}][{L}]+)(?:\s*[–—-]\s*([{U}][{L}]+))?')
# the OCR's slips: "Ieremij e", "Đorđij e"; "Blang a", the father of the Kovačević brothers, is Blagoje (the narodni
# heroj Sava Kovačević of Nudo, Kovačević Blagoja Sava on the 5. proleterska's roll)
READ = {'Ieremij e': 'Jeremije', 'Đorđij e': 'Đorđije', 'Blang a': 'Blagoja', 'Dimirtije': 'Dimitrije'}


def clean(t: str) -> str:
    t = t.replace('КРЈ', 'KPJ').replace(']', 'J').replace('Dorđ', 'Đorđ').replace('Dura', 'Đura').replace('Duro', 'Đuro').replace('Doka', 'Đoka').replace('Doko', 'Đoko')
    for a, b in READ.items():
        t = t.replace(a, b)
    return re.sub(rf'\bI(?=[oae][{L}])', 'J', t)                       # "Iovo", "Iošan", "Ianka": J


def rear(book: dict) -> list[dict]:
    entries, cur = [], None
    for page in REAR[1]:
        for l in level_lines(page_words(book, page)):
            t = clean(l.text.strip())
            if re.fullmatch(r'\d{3}', t) or t.startswith(('PRILOG', 'UBIIENI', 'RADNICI', '(kraj maja')):
                continue
            if t.startswith('Napomena'):
                return entries
            m = re.match(rf'^(?:\d{{1,2}}\.\s+)?{REAR_NAME.pattern}\s*(?:\((\d{{4}})\))?,\s*(.*)$', t)
            if m and (not cur or cur['text'].rstrip().endswith('.')):
                cur = {'groups': m.groups()[:4], 'year': m.group(5) or '', 'text': m.group(6), 'page': page}
                entries.append(cur)
            elif cur:
                cur['text'] += ' ' + t
    return entries


def spomenica(book: dict) -> list[dict]:
    out = []
    for page in SPOMENICA[1]:
        for l in level_lines(page_words(book, page)):
            t = clean(l.text.strip())
            m = NAME.search(t)
            if not m or re.fullmatch(r'\d{3}', t) or t.startswith(('PRILOG', 'SPISAK', 'PARTIZANSKE', '(BORCI')):
                continue
            out.append({'groups': m.groups(), 'page': page})
    return out


def main():
    V.corpus()
    book = load(BOOK)
    out, counts = [], Counter()
    for no, e in enumerate(rear(book), 1):
        last, fath, first, nick = e['groups']
        fath = fath or ''
        bio = V.unhyphen(e['text']).strip()
        role = V.role(bio)
        role = 'activist' if role == 'out' else role        # the book counts them the movement's rear workers
        d = V.death(bio)
        rec = {'soldier_id': f'{PREFIX}{no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
               'last_name': last, 'also': [], 'first_name': first, 'nick': nick or '', 'fathers_name': fath,
               'birth_year': e['year'], 'born_in': 'Grahovo, Nikšić', 'death_year': d.get('year', ''),
               **({'death_place': d['place']} if d.get('place') else {}), 'survived': False, 'units': V.units_of(bio),
               'list': REAR[0], 'book_title': BOOK_TITLE, 'source_url': viewer_url(book, e['page']),
               'source_page': e['page'] - OFFSET,
               'additional_info': f"{REAR[0]}: " + ' '.join(x for x in (last, fath, first) if x)
                                  + (f' — {nick}' if nick else '') + (f" ({e['year']})" if e['year'] else '') + f', {bio}'}
        if role:
            rec['role'] = role
        counts[f"rear: {role or 'fighter'}"] += 1
        out.append(rec)
    for no, e in enumerate(spomenica(book), 1):
        last, fath, first, nick = e['groups']
        fath = '' if fath == '?' else fath
        out.append({'soldier_id': f'{PREFIX}{1000 + no:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                    'last_name': last, 'also': [], 'first_name': first, 'nick': nick or '', 'fathers_name': fath,
                    'birth_year': '', 'born_in': 'Grahovo, Nikšić', 'death_year': '', 'survived': False, 'units': [],
                    'list': SPOMENICA[0], 'book_title': BOOK_TITLE, 'source_url': viewer_url(book, e['page']),
                    'source_page': e['page'] - OFFSET,
                    'additional_info': f"{SPOMENICA[0]}: {last} {fath} {first}{' — ' + nick if nick else ''}".replace('  ', ' ')})
        counts['spomenica'] += 1
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(out))
    for r in out:
        print(f"  {r['soldier_id']} {r['name']} {r['nick']} | {r['birth_year']} {r['death_year']} {r.get('role', '')}")


if __name__ == '__main__':
    main()
