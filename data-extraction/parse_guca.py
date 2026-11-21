"""
*Гуча кроз векове* (Poreklo library, doc 00006613), a book across units: "Погинули (по годинама)" (scan pp. 110-116),
the townsmen of Guča who died in 1941-1945, year by year, from Goran Davidović and Miloš Timotijević's *Zatamnjena
prošlost*, every name with the side he died on:

    "Милан Икодиновић (1912), погинуо у борби са Немцима на Краљеву, партизан;"

Only those the list calls partisans or fighters of the NOVJ or KNOJ are taken; the civilians, the JVuO, ZBOR, the
State Guard, the royal army's men and the others are out.

Output: data-extraction/poreklo/guca-entries.json (IDs 9123xxxxxx in the list's order).
Usage: python data-extraction/parse_guca.py
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

BOOK = 'guca.json'
OUT = HERE / 'poreklo' / 'guca-entries.json'
PREFIX = '9123'
OFFSET = 1                                   # scan page minus the book's page (scan 110 is p. 109)
TITLE = 'Guča kroz vekove'
LIST = 'Poginuli (po godinama)'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
ENTRY = re.compile(rf'^((?:[{CU}][{CL}]+\s+){{1,2}}(?:[{CU}]\.\s*)?[{CU}][{CL}]+(?:\s*[–-]\s*[{CU}][{CL}]+)?)\s*(?:\((1[89]\d\d)\))?\s*,\s*(.*)$')
SIDE = re.compile(r'партизан|НОВЈ|КНОЈ|НОП')
NOT = re.compile(r'цивил|ЈВуО|ЗБОР|СДС|ВКЈ|БЈВ|четни|љотић|домобран|усташ\w*\s*;', re.I)


def main():
    V.corpus()
    book = load(BOOK)
    raw, year, on = [], '', False
    for page in range(110, 117):
        for l in level_lines(page_words(book, page)):
            t = re.sub(r"^['\"г]?Њ(?=[уо]р)", 'Ђ', l.text.strip())           # "'Њорђевић", "гЊорђе", "'Њуретић"
            t = re.sub(r"(?<=\s)['\"]Њ(?=[уо]р)", 'Ђ', t)
            if t.startswith('Погинули (по годинама)'):
                on = True
                continue
            if not on or re.match(r'^\d{2,3}\.\s', t) or t.startswith('*') or re.fullmatch(r'\d{1,3}', t):
                continue
            if re.fullmatch(r'19(4\d)\.', t):
                year = t[:4]
                continue
            if re.match(r'^(Немци су|Радници|окупатори)', t):
                on = False
                continue
            m = ENTRY.match(t)
            if m and l.x0 > 3000:                           # an entry's first line stands in from the margin
                raw.append({'page': page, 'year': year, 'name': m.group(1), 'born': m.group(2), 'text': m.group(3)})
            elif raw:
                raw[-1]['text'] += ' ' + t
    # entries the OCR ran into the one before ("... партизан; Миодраг С. Протић (1912), ...")
    split = []
    for r in raw:
        parts = re.split(rf';\s+(?=(?:[{CU}][{CL}]+\s+){{1,2}}(?:[{CU}C]\.\s*)?[{CU}][{CL}]+(?:\s*[–-]\s*[{CU}][{CL}]+)?\s*(?:\(1[89]\d\d\))?\s*,)', re.split(r';\s+(?=[{0}])'.format(CL), r['text'])[0])
        split.append(dict(r, text=parts[0]))
        for x in parts[1:]:
            m = ENTRY.match(x.replace('C.', 'С.'))
            if m:
                split.append(dict(r, name=m.group(1), born=m.group(2), text=m.group(3)))
    raw = split
    entries, counts, seen = [], Counter(), set()
    for r in raw:
        cyr = V.unhyphen(r['text']) if hasattr(V, 'unhyphen') else r['text']
        if not SIDE.search(cyr) or NOT.search(cyr) and not re.search(r'партизан\s*[;,.]?\s*$', cyr.strip()):
            counts['out'] += 1
            continue
        if not r['year'] or r['year'] > '1945':                  # after the war (1946, 1948): out
            counts['after the war'] += 1
            continue
        key = (r['name'], r['born'])
        if key in seen:                                         # printed twice (Gavrilović Borisav, 1898)
            counts['twice'] += 1
            continue
        seen.add(key)
        nick = ''
        if re.search(r'\s[–-]\s', r['name']):                   # "Славољуб Мирковић – Артем"
            r['name'], nick = (x.strip() for x in re.split(r'\s[–-]\s', r['name'], maxsplit=1))
            nick = V.given_word(nick)
        words = r['name'].split()
        last = V.name_word(words[-1])
        given = V.given_word(words[0])
        nick = nick or (V.given_word(words[1]) if len(words) == 3 and not words[1].endswith('.') else '')
        info = V.read_cyr(cyr).strip(' ;.')
        d = V.death(info)
        name = f'{last} {given}'
        entries.append({'soldier_id': f'{PREFIX}{len(entries) + 1:06d}', 'name': name, 'last_name': last, 'also': [],
                        'first_name': given, 'nick': nick, 'fathers_name': '', 'birth_year': r['born'] or '',
                        'born_in': 'Guča, Lučani', 'death_year': d.get('year', '') or r['year'],
                        **({'death_place': d['place']} if d.get('place') else {}), 'survived': False,
                        'units': V.units_of(info),
                        'additional_info': f"{LIST}, {r['year']}: {latin(r['name'])}"
                                           f"{' (' + r['born'] + ')' if r['born'] else ''}, {info}.",
                        'list': LIST, 'book_title': TITLE, 'source_url': viewer_url(book, r['page']),
                        'source_page': r['page'] - OFFSET,
                        **({'role': 'participant'} if 'симпатизер' in cyr else {})})
        counts['participant' if 'симпатизер' in cyr else 'partisan'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'read', len(raw))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} | {e['death_year']} | "
              f"{e['additional_info'][:110]}")


if __name__ == '__main__':
    main()
