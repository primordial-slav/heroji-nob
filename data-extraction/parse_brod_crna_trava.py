"""
Брод - село код Црне Траве (Poreklo library, doc 00000448): the fighters of the village Brod by Crna Trava who fell in
the war, as a book across units. Cyrillic. "Прилог III, Погинули 1941.-1945. из села Брод" (scan pp. 812-813, book pp.
808-809) is a table of the village's dead, a row each: number, "Surname (Father) Given", the mahala, the day and the
place of death, and for a fighter his unit ("VII срп.", "XII срп.", "Црн. од", "ком. подр.", "Омл.бат"). The table
names the village's civilians too (the women killed at home, a man dead in a German camp in 1941) and doesn't say
which a man without a unit was: only the rows that give a unit go in. The five "Борци из села Брод погинули у овом
одреду" of the 11. južnomoravski odred (p. 163) are rows of the table and join them. Out: Prilog II (p. 811, the wars
of 1912-1918) and Prilog IV (the families of 1995).

Output: data-extraction/poreklo/brod-crna-trava-entries.json, IDs 9088000001-076 by the table's number.
Usage: python data-extraction/parse_brod_crna_trava.py
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
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'brod-crna-trava.json'
OUT = HERE / 'poreklo' / 'brod-crna-trava-entries.json'
PREFIX = '9088'
OFFSET = 4                                  # scan page minus the book's page
TITLE = 'Brod - selo kod Crne Trave'
LIST = 'Poginuli 1941-1945. iz sela Brod (Prilog III)'
ODRED = 'Borci iz sela Brod poginuli u 11. južnomoravskom odredu'
VILLAGE = 'Brod, Crna Trava'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# the unit column as printed (Latin, the OCR's slips: "УН срп" VII, "ХП"/"XIIcp" XII, "Црод" Црн. од) -> the site's
# unit (or 0: a unit not on the site) and how the entry's text gives it
UNITS = [(r'\b(?:VII|UN|UP)\s*srp', 85, 'VII srpska brigada'), (r'\b(?:XII|HP|XP)\s*(?:srp|sr|cp)|XIIcp|XII\s*cp', 90, 'XII srpska brigada'),
         (r'\bVIII\s*srp', 87, 'VIII srpska brigada'), (r'\b(?:X|H)\s+srp', 88, 'X srpska brigada'),
         (r'11\s*juž', 0, '11. južnomoravski odred'), (r'Crn\.\s*o|Crod', 0, 'Crnotravski odred'),
         (r'kom\.\s*podr', 0, 'komanda područja'), (r'kom\.\s*gr', 0, 'komanda grada'),
         (r'[Oo]ml?\.\s*bat', 0, 'omladinski bataljon'), (r'1\s*ju[žŽ]\.\s*br', 0, '1. južnomoravska brigada')]
# p. 163: the odred's fallen, given name first, as rows of the table (number) with their text
ODRED_ROWS = {73: 'Vlajko P. Milenković, Madžare, 19. 3. 1944. Čemernik', 26: 'Čedomir D. Nikolić, Rašine, 24. 3. 1944. Čemernik',
              10: 'Bratislav S. Milanović, Rašine, 19. 4. 1944. Rupska reka', 21: 'Radovan D. Savić, Rašine, 4. 9. 1944. Plana',
              55: 'Mika S. Veljković, Dećeve, 15. 5. 1944. Plana'}
ROW = re.compile(rf"^(\d{{1,2}})\s+[·.]?\s*([{UC}][{LC}]+)\s*(?:\(\s*([^)]+?)\s*\)|([{UC}])\.)\s*"
                 rf"([{UC}]?[{LC}]+(?:\s*[–-]\s*[{UC}][{LC}]+)?)\s+(.*)$")
WHEN = re.compile(r'(?:(\d{1,2})\.\s?)?(\d{1,2})\.\s?(19\d\d|194)\.?|(?:мај|март|април)\s*(194\d)\.?|(194\d)\.')


def rows(book: dict) -> list[dict]:
    out = []
    for page in (812, 813):
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            t = t.replace('ApaHbenosuh(T1HpKa)', 'Аранђеловић (Тирка)')            # no. 37, in Latin look-alikes
            t = re.sub(r'(?<![\w])Ј\s+(?=[а-я])', 'Ј', t)                         # "Ј аничијевић"
            t = re.sub(r'\(\s*([А-Я])\s+([а-я]+)\s*\)', r'(\1\2)', t)            # "(Г орче)"
            m = ROW.match(t)
            if m:
                out.append({'no': int(m.group(1)), 'page': page, 'sur': m.group(2), 'father': m.group(3) or '',
                            'initial': m.group(4) or '', 'given': m.group(5), 'rest': m.group(6)})
    return out


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for r in rows(book):
        rest = latin(r['rest'])
        mahala, _, after = rest.partition(' ')
        if mahala in ('M.', 'М.'):                          # "М. Равни." = Malo Ravnište
            mahala, after = 'Malo Ravnište', after.split(' ', 1)[1] if ' ' in after else ''
        units = [(code, name) for pat, code, name in UNITS if re.search(pat, after)]
        if not units:
            counts['no unit: left out'] += 1
            continue
        last = V.name_word(r['sur'])
        given = '-'.join(V.given_word(x) for x in re.split(r'\s*[–-]\s*', r['given']))
        first, nick = (given.split('-', 1) + [''])[:2]
        fath = V.father(r['father']) if r['father'] else ''
        when = re.search(r'(?:(\d{1,2})\.)?(\d{1,2})\.(19\d\d)|(\d{1,2})\.(19\d\d)|(?:maj|mart)\s*(19\d\d)|(19\d\d)', after)
        year = next((g for g in (when.groups() if when else ()) if g and len(g) == 4), '')
        date = f'{when.group(3)}-{int(when.group(2)):02d}-{int(when.group(1)):02d}' if when and when.group(1) else ''
        place = after[when.end():].strip(' .,') if when else ''
        place = re.split(r'[.,]\s*|\s+(?=VII|XII|VIII|UN|HP|X\s|H\s|Crn|kom|Om|om|1\s*ju|11\s*ju)', place)[0].strip()
        place = {'HOBO Selo': 'Novo Selo', 'KOCOBO': 'Kosovo'}.get(place, place)    # Latin look-alikes
        printed = f'{last}{f" ({fath})" if fath else (" " + latin(r["initial"]) + "." if r["initial"] else "")} {given}'
        text = f'{LIST}: {r["no"]}. {printed}, {mahala}, {after}; {", ".join(n for _, n in units)}'
        if r['no'] in ODRED_ROWS:
            text += f'. {ODRED}: {ODRED_ROWS[r["no"]]}'
        entries.append({'soldier_id': f'{PREFIX}{r["no"]:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                        'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
                        'birth_year': '', 'born_in': VILLAGE, 'death_year': year,
                        **({'death_date': date} if date else {}), **({'death_place': place} if place else {}),
                        'survived': False, 'units': sorted({c for c, _ in units if c}),
                        'additional_info': text, 'list': LIST, 'book_title': TITLE,
                        'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET})
        counts['fighters'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
