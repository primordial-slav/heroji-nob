"""
Васојевићко село Божиће и Божићани (Vladimir Radovanov Dubak; Poreklo library, doc 00003336): the fighters of
Božiće by Andrijevica, as a book across units. The book names its people by brotherhood, the surname and then the
given names of its men ("Вулић Батрић, Вукашин, Гаврило, Данило и Драгић"), a father's initial before a name its
brotherhood repeats ("В. Милан", "Ђ. Милан") or the father's possessive ("Деса Вељова"). Lists, typed from the OCR:
  - "из Божића су борци само" (scan pp. 317-318): the fighters as the author counts them, by the Convention on
    combatants (a unit, a command, arms carried openly, a sign worn): no role;
  - "Носиоци Партизанске споменице 1941. године" (p. 318): six, one of them in the list above;
  - "Погинули су као борци у јединицама или као сарадници НОПЈ" (pp. 319-320): nineteen, all but one in the
    fighters' list (whose entry takes this list's line); Vulić B. Nenad of Krajište, whom the list doesn't tell apart,
    is a `role: 'participant'`.
Out: the Chetnik movement's dead (p. 320), the two girls abducted in 1944 and the children killed by mines after the
war.

Output: data-extraction/poreklo/bozice-entries.json, IDs 9091xxxxxx: the fighters 9091000001 on, the spomenica's
holders who are no fighter of the list 9091000101 on, Vulić Nenad 9091000201.
Usage: python data-extraction/parse_bozice.py
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
from poreklo_text import load, viewer_url  # noqa: E402

BOOK = 'bozice.json'
OUT = HERE / 'poreklo' / 'bozice-entries.json'
PREFIX = '9091'
OFFSET = 1                                  # scan page minus the book's page
TITLE = 'Vasojevićko selo Božiće i Božićani'
VILLAGE = 'Božiće, Andrijevica'
FIGHTERS = 'Borci iz Božića (prema Konvenciji o borcu)'
SPOMENICA = 'Nosioci Partizanske spomenice 1941. godine'
FALLEN = 'Poginuli kao borci u jedinicama ili kao saradnici NOPJ'
# the fighters (pp. 317-318) by brotherhood; "V. Milan" a father's initial, "Desa Veljova" his possessive
BROTHERHOODS = [
    ('Vuković', 317, ['Miodrag']),
    ('Vulić', 317, ['Batrić', 'Vukašin', 'Gavrilo', 'Danilo', 'Dragić']),
    ('Vučević', 317, ['Branko', 'Radosav']),
    ('Dedović', 317, ['Aleksandar', 'Bogić', 'Vuka', 'Vulka', 'Vladimir', 'Desa Veljova', 'Desa Mijailova', 'Dragoljub',
                      'Ljubica', 'Milovan', 'Miloš', 'Minja']),
    ('Dubak', 317, ['Aleksandar-Bilo', 'Vladimir', 'Dragutin', 'Đorđije', 'Josif', 'Mileva', 'Miloš', 'Nikola', 'Radoje',
                    'Radoš']),
    ('Đukić', 317, ['Danica']),
    ('Zekić', 317, ['Miloš', 'Milonja']),
    ('Jukić', 317, ['Božidar', 'Vojin', 'Vukosav', 'Dragoje', 'Dušan', 'Mileta']),
    ('Maslovarić', 318, ['Aleksa', 'Vaso', 'Vuk', 'Danilo', 'Dragiša', 'Đorđije', 'Ivan', 'Jovan', 'V. Milan', 'Đ. Milan',
                         'Milivoje', 'Milić', 'V. Milorad', 'M. Milorad', 'Milosav', 'Milosava-Sela', 'Đ. Mihailo', 'Novak',
                         'M. Radonja', 'P. Radonja', 'Radovan']),
    ('Milović', 318, ['Golub', 'Milo']),
    ('Savić', 318, ['Milka', 'Đ. Milorad', 'Petar']),
]
HOLDERS = [('Dedović', 'Dragoljub'), ('Binović', 'Slobodan'), ('Lalević', 'Aleksandar'), ('Maslovarić', 'Ruža'),
           ('Savić', 'Darinka'), ('Radunović', 'Božidar')]
# the fallen (pp. 319-320) as printed, (surname, given name as in the fighters' list)
FALLEN_NAMES = [('Vuković', 'Miodrag'), ('Vučević', 'Branko'), ('Dubak', 'Dragutin'), ('Đukić', 'Danica'),
                ('Zekić', 'Miloš'), ('Jukić', 'Božidar'), ('Jukić', 'Dragoje'), ('Maslovarić', 'Vaso'),
                ('Maslovarić', 'Aleksa'), ('Maslovarić', 'Danilo'), ('Maslovarić', 'Đ. Milan'), ('Maslovarić', 'Milić'),
                ('Maslovarić', 'M. Radonja'), ('Milović', 'Golub'), ('Milović', 'Milo'), ('Savić', 'Milka'),
                ('Savić', 'Petar')]
# printed "Масловарић ... Н.Милорад, Радисав": N. Milorad is one of the fighters' two Milorads (V. and M.), which one
# the list doesn't say, so his line joins neither; Radisav, not in the fighters' list, is an entry of his own
EXTRA_FALLEN = [('Maslovarić', 'Radisav', '', 319, VILLAGE, None)]
NENAD = ('Vulić', 'Nenad', 'B.', 320, 'Krajište, Andrijevica')


def split(given: str) -> tuple[str, str, str, str]:
    """(given name, father's initial, his possessive, nickname)"""
    initial, possessive, nick = '', '', ''
    m = re.match(r'^([A-ZČĆŽŠĐ])\.\s*(\S+)$', given)
    if m:
        initial, given = m.group(1) + '.', m.group(2)
    m = re.match(r'^(\S+)\s+(\S+ova)$', given)
    if m:
        given, possessive = m.groups()
    if '-' in given:
        given, nick = given.split('-', 1)
    return given, initial, possessive, nick


def main():
    book = load(BOOK)
    entries, counts, by_name = [], Counter(), {}
    n = 0
    for last, page, names in BROTHERHOODS:
        for g in names:
            given, initial, possessive, nick = split(g)
            n += 1
            printed = f'{last} {g}'
            e = {'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {possessive + " " if possessive else ""}{given}',
                 'last_name': last, 'also': [], 'first_name': given, 'nick': nick, 'fathers_name': possessive,
                 'birth_year': '', 'born_in': VILLAGE, 'death_year': '', 'survived': False, 'units': [],
                 'additional_info': f'{FIGHTERS}: {printed}', 'list': FIGHTERS, 'book_title': TITLE,
                 'source_url': viewer_url(book, page), 'source_page': page - OFFSET}
            entries.append(e)
            by_name[(last, g)] = e
            counts['fighters'] += 1
    for last, g in FALLEN_NAMES:
        e = by_name[(last, g)]
        e['additional_info'] += f'. {FALLEN}: {last} {g}'
        e['death_year'] = ''
        e['source_url'], e['source_page'] = viewer_url(book, 319), 319 - OFFSET
        counts['fallen joined'] += 1
    k = 0
    for last, given in HOLDERS:
        e = by_name.get((last, given))
        if e:
            e['additional_info'] += f'. {SPOMENICA}: {last} {given}'
            counts['holders joined'] += 1
            continue
        k += 1
        entries.append({'soldier_id': f'{PREFIX}{100 + k:06d}', 'name': f'{last} {given}', 'last_name': last, 'also': [],
                        'first_name': given, 'nick': '', 'fathers_name': '', 'birth_year': '', 'born_in': VILLAGE,
                        'death_year': '', 'survived': True, 'units': [],
                        'additional_info': f'{SPOMENICA}: {last} {given}', 'list': SPOMENICA, 'book_title': TITLE,
                        'source_url': viewer_url(book, 318), 'source_page': 318 - OFFSET})
        counts['holders alone'] += 1
    for last, given, fath, page, village, role in EXTRA_FALLEN:
        k += 1
        entries.append({'soldier_id': f'{PREFIX}{100 + k:06d}', 'name': f'{last} {given}', 'last_name': last, 'also': [],
                        'first_name': given, 'nick': '', 'fathers_name': fath, 'birth_year': '', 'born_in': village,
                        'death_year': '', 'survived': False, 'units': [], 'role': 'participant',
                        'additional_info': f'{FALLEN}: {last} {given}', 'list': FALLEN, 'book_title': TITLE,
                        'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
        counts['fallen alone'] += 1
    last, given, initial, page, village = NENAD
    entries.append({'soldier_id': f'{PREFIX}000201', 'name': f'{last} {given}', 'last_name': last, 'also': [],
                    'first_name': given, 'nick': '', 'fathers_name': '', 'birth_year': '', 'born_in': village,
                    'death_year': '', 'survived': False, 'units': [], 'role': 'participant',
                    'additional_info': f'{FALLEN}: {last} {initial} {given} iz Krajišta', 'list': FALLEN,
                    'book_title': TITLE, 'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
    counts['fallen alone'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
