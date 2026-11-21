"""
*Krbavica u prošlosti i sadašnjosti* (Poreklo library, doc 00009299), a book across units: in Roko Franić Barba's
article *Prva dalmatinska*, "Borci Prve dalmatinske čete (Treće čete Bataljona »M. Orešković«) po grupama odlaska sa
šibenskog područja" (scan pp. 366-371), the 118 partisans of northern Dalmatia who went to Lika in November and
December 1941, by group and home place:

    "a) iz Vodica 3. XI. 1941." / "Pamuković Kamilo, Ante, komandir" / "Ivas Ante »Finci«, Tome"

the surname, the given name and a nickname, the father's name in the genitive, a duty at times. The list was drawn up
by Roko Franić »Barba« with the Šibenik SUBNOR.

Output: data-extraction/poreklo/krbavica-entries.json (IDs 9127xxxxxx by the list's number; the first group's seven,
whose numbers the OCR lost, 1-7 in their order).
Usage: python data-extraction/parse_krbavica.py
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

BOOK = 'krbavica.json'
OUT = HERE / 'poreklo' / 'krbavica-entries.json'
PREFIX = '9127'
OFFSET = 9                                   # scan page minus the book's page (scan 366 is p. 357)
TITLE = 'Krbavica u prošlosti i sadašnjosti'
LIST = 'Borci Prve dalmatinske čete (Treće čete Bataljona »M. Orešković«)'
PLACES = {'Vodica': 'Vodice', 'Tribunja': 'Tribunj', 'Macura': 'Macure', 'Šibenika': 'Šibenik', 'Prvić Luke': 'Prvić Luka',
          'Prvić Šepurine': 'Prvić Šepurine', 'Srime': 'Srima', 'Zatona': 'Zaton', 'Zmana – Dugi otok': 'Zman, Dugi otok',
          'Raslina': 'Raslina', 'Grebaštice': 'Grebaštica', 'Jadrtovca': 'Jadrtovac', 'Žirja': 'Žirje', 'Zlarina': 'Zlarin',
          'Krapnja': 'Krapanj', 'Brodarice': 'Brodarica', 'Primoštena': 'Primošten', 'Pirovca': 'Pirovac',
          'Tisnoga': 'Tisno', 'Betine': 'Betina', 'Murtera': 'Murter', 'Jezera': 'Jezera', 'Skradina': 'Skradin',
          'Malog Iža': 'Mali Iž', 'Luke – Dugi otok': 'Luka, Dugi otok', 'Savara – Dugi otok': 'Savar, Dugi otok',
          'Bukovice': 'Bukovica'}
UP, LOW = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ENTRY = re.compile(rf'^\W*(?:(\d{{1,3}})\s*\.\s*)?([{UP}][{LOW}]+(?:\s*[-–—]\s*[{UP}][{LOW}]+)?)\s+([{UP}][{LOW}]+(?:\s*[-–—]\s*[{UP}][{LOW}]+)?)'
                   rf'\s*(?:[»«<>]+\s*([^»«<>]+?)\s*[»«<>]+)?\s*(?:,\s*(.*?)|\s+([{UP}][{LOW}]+))?\s*,?\s*(?:\bi)?$')


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts, place, last_no = [], Counter(), '', 0
    for page in range(366, 372):
        for l in page_lines(book, page, 1)[0]:
            t = re.sub(r'(?<=\w)·(?=\w)|\s·\s', ' ', l.text.strip()).replace('F·onso', 'Fonso').replace('Pamuk-ović', 'Pamuković')
            t = re.sub(r'^\d{4}\W+(?=Pamukovi)', '1. ', t)                     # "5992“??? Pamuković"
            t = t.replace('Kraplja-nov', 'Krapljanov').replace('»Burgež,', '»Burgež«,')
            mp = re.match(r'^\W*[a-zA-Z&]\)\s*iz\s+(.+?)(?:\s*[–-]?\s*\d{1,2}\.\s*[XIV]+\..*)?$', t)
            if mp:
                key = mp.group(1).strip(' –-')
                place = PLACES.get(key, key)
                continue
            if t.startswith(('6. Spisak', 'Spisak je')):
                break
            m = ENTRY.match(t)
            if not m:
                continue
            no = int(m.group(1)) if m.group(1) else last_no + 1
            if no <= last_no or no - last_no > 3:
                no = last_no + 1
            last_no = no
            last = '-'.join(V.name_word(x) if V.T._names[x.upper()] else x for x in re.split(r'\s*[-–—]\s*', m.group(2)))
            given = m.group(3).split('-')[0].split('–')[0].strip()
            nick = (m.group(4) or '').strip()
            rest = (m.group(5) or '').strip(' .,')
            fm = re.match(rf'^([{UP}][{LOW}]+)\s*(?:,\s*(.*))?$', rest)
            father = m.group(6) or (fm.group(1) if fm else '')
            duty = ((fm.group(2) or '') if fm else rest).strip(' .,')
            if re.match(r'^(Kad|vod|Otočani|U prvoj|Pošto|Početkom)\b', m.group(2)):
                continue
            printed = f"{no}. {m.group(2)} {m.group(3)}{' »' + nick + '«' if nick else ''}{', ' + father if father else ''}{', ' + duty if duty else ''}"
            entries.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': ' '.join(x for x in (last, father, given) if x), 'last_name': last,
                            'also': [], 'first_name': given, 'nick': nick, 'fathers_name': father, 'birth_year': '',
                            'born_in': place,
                            'death_year': '', 'survived': False, 'units': [],
                            'additional_info': f'{LIST}, {place}: {printed}.', 'list': LIST, 'book_title': TITLE,
                            'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
            counts['fighter'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    nos = [int(e['soldier_id'][-3:]) for e in entries]
    print(len(entries), 'entries ->', OUT.name, dict(counts), 'missing', sorted(set(range(1, max(nos) + 1)) - set(nos)))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['born_in']} | {e['additional_info'][:90]}")


if __name__ == '__main__':
    main()
