"""
Хроника села Кремна са основним подацима о општини Прњавор (Poreklo library, doc 00000547), the village of Kremna by
Prnjavor, as a book across units. Its lists of the war's partisans, Cyrillic, names alone, typed here from the
scan's OCR (they are short, numbered in two columns, and the OCR garbled the numbers):
    "Списак погинулих бораца у партизанима из села Кремне од 1941.-1945." (scan pp. 136-137, 26 names) and
    "Погинули борци у селу Кремна и насељима Лужани и Јасик у Другом светском рату" (pp. 148-149, 33 names, from the
        memorial plaque on the school at Podvučjak, the father's initial between): one man in both lists is one entry
        with both lines (`FALLEN`);
    "Носиоци Партизанске споменице 1941. године" (p. 173, 22 of the Prnjavor area);
    "Команданти партизанских јединица са прњаворског подручја" (p. 174, 8).
Out: the Chetniks' dead and living, the victims of terror, the 1941 insurgents who later went either way (p. 144),
the soldiers of 1914-1918 and of 1991-1995.

Output: data-extraction/poreklo/kremna-entries.json (IDs 9099xxxxxx: the fallen from 000001 in the plaque's order,
the village list's men the plaque lacks from 000101, the spomenica holders from 000201, the commanders from 000301).
Usage: python data-extraction/parse_kremna.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from poreklo_text import load, viewer_url  # noqa: E402

BOOK = 'kremna.json'
OUT = HERE / 'poreklo' / 'kremna-entries.json'
PREFIX = '9099'
OFFSET = 2                                  # scan page minus the book's page
TITLE = 'Hronika sela Kremna sa osnovnim podacima o opštini Prnjavor'
PLAQUE = 'Poginuli borci u selu Kremna i naseljima Lužani i Jasik u Drugom svetskom ratu'
VILLAGE = 'Spisak poginulih boraca u partizanima iz sela Kremne od 1941.-1945.'
SPOMENICA = 'Nosioci Partizanske spomenice 1941. godine'
COMMANDERS = 'Komandanti partizanskih jedinica sa prnjavorskog područja'
# the plaque (number, surname, father's initial, given name) and the village list's number of the same man
FALLEN = [(1, 'Bojanović', '', 'Trivun', None), (2, 'Bijelić', '', 'Mirko', 2), (3, 'Bijelić', '', 'Ljubo', 1),
          (4, 'Budak', '', 'Božo', None), (5, 'Domuz', '', 'Stanko', 3), (6, 'Duronjić', '', 'Rajko', 4),
          (7, 'Gajić', '', 'Tešo', 5), (8, 'Gajanić', '', 'Dragoljub', None), (9, 'Jovičić', '', 'Ostoja', None),
          (10, 'Mijatović', '', 'Novak', 6), (11, 'Marković', '', 'Teodor', 7), (12, 'Mijatović', '', 'Stanko', 8),
          (13, 'Mihajlović', 'N.', 'Petar', 9), (14, 'Nagradić', 'V.', 'Ljuban', 10), (15, 'Nunić', 'O.', 'Matija', 11),
          (16, 'Pavlović', 'J.', 'Milinko', 12), (17, 'Petrović', 'M.', 'Branko', None), (18, 'Petrović', '', 'Mirko', 13),
          (19, 'Rudonjić', '', 'Mitar', 14), (20, 'Stanić', '', 'Simeun', 15), (21, 'Stanić', '', 'Petko', 16),
          (22, 'Šarčević', '', 'Uglješa', 17), (23, 'Šarčević', '', 'Đurađ', 18), (24, 'Šmulja', '', 'Stanko', 23),
          (25, 'Turudić', '', 'Petar', 19), (26, 'Tanasić', '', 'Rajko', 20), (27, 'Tanasić', '', 'Savo', 21),
          (28, 'Tatarević', '', 'Božo', None), (29, 'Vetnić', '', 'Branko', None), (30, 'Zabolotni', 'I.', 'Stevan', None),
          (31, 'Živković', 'I.', 'Dušan', None), (32, 'Žunić', 'J.', 'Milan', 25), (33, 'Žunić', 'J.', 'Živko', 26)]
# the village list as printed where its form differs from the plaque's, and its men the plaque lacks
VILLAGE_FORMS = {1: 'Bijelić Ljubomir', 10: 'Nagradić Ljubo', 12: 'Pavlović Milenko', 4: 'Duronić Rajko'}
VILLAGE_ONLY = [(22, 'Žunić', 'Dušan'), (24, 'Šmulja', 'Branko')]
SPOMENICA_LIST = [(1, 'Čereković', 'Savo', ''), (2, 'Čereković', 'Milka', ''), (3, 'Pivašević', 'Milan', ''),
                  (4, 'Samardžija', 'Stojan', ''), (5, 'Preradović', 'Mirko', 'Beograd'), (6, 'Preradović', 'Zdravko', ''),
                  (7, 'Krajišnik', 'Nenad', ''), (8, 'Kalenjuk', 'Roman', ''), (9, 'Petrović', 'Petar', 'Sarajevo'),
                  (10, 'Janković', 'Ljubo', ''), (11, 'Mitrović', 'Spasoje', ''), (12, 'Grujić', 'Ljubo', ''),
                  (13, 'Ruščukić', 'Smajo', ''), (14, 'Janković', 'Nenad', 'Budisava'), (15, 'Samardžija', 'Stevo', ''),
                  (16, 'Jevtić', 'Dragoljub', ''), (17, 'Milanović', 'Dragomir', ''), (18, 'Radić', 'Milena', ''),
                  (19, 'Modić', 'Vasko', ''), (20, 'Podgorac', 'Živka', ''), (21, 'Mikić', 'Bosiljka', ''),
                  (22, 'Radić', 'Jelena', 'Luke; udata Ignjatić, Budisava')]
COMMANDER_LIST = [(1, 'Mitrov', 'Danko', 'Komandant Četvrtog krajiškog NO odreda'),
                  (2, 'Pivašević', 'Novak', 'Komandant Trećeg bataljona Četvrtog krajiškog odreda'),
                  (3, 'Samardžija', 'Stevo', 'Komandant Prvog prnjavorskog odreda; komandant Četrnaeste srednjobosanske brigade'),
                  (4, 'Čereković', 'Savo', 'Komandant Prvog prnjavorskog odreda'),
                  (5, 'Ćurguz', 'Dragutin', 'Komandant Osamnaeste srednjobosanske udarne brigade'),
                  (6, 'Čelar', 'Zdravko', 'Komandant Prvog udarnog bataljona na Motajici'),
                  (7, 'Hercegovac', 'Adem', 'Politički komesar Prnjavorskog odreda'),
                  (8, 'Kapor', 'Momir', 'Politički komesar Osamnaeste brigade')]


def main():
    book = load(BOOK)
    entries = []
    url = lambda p: viewer_url(book, p)  # noqa: E731
    for no, last, initial, first, vno in FALLEN:
        text = f"{PLAQUE}: {no}. {last}{' ' + initial if initial else ''} {first}"
        if vno:
            text += f" — {VILLAGE}: {vno}. {VILLAGE_FORMS.get(vno, f'{last} {first}')}"
        entries.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f"{last}{' ' + initial if initial else ''} {first}",
                        'last_name': last, 'also': [], 'first_name': first, 'nick': '', 'fathers_name': initial,
                        'birth_year': '', 'born_in': 'Kremna, Prnjavor' if vno else '', 'death_year': '',
                        'survived': False, 'units': [], 'additional_info': text, 'list': PLAQUE, 'book_title': TITLE,
                        'source_url': url(148), 'source_page': 148 - OFFSET})
    for vno, last, first in VILLAGE_ONLY:
        entries.append({'soldier_id': f'{PREFIX}{100 + vno:06d}', 'name': f'{last} {first}', 'last_name': last,
                        'also': [], 'first_name': first, 'nick': '', 'fathers_name': '', 'birth_year': '',
                        'born_in': 'Kremna, Prnjavor', 'death_year': '', 'survived': False, 'units': [],
                        'additional_info': f'{VILLAGE}: {vno}. {last} {first}', 'list': VILLAGE, 'book_title': TITLE,
                        'source_url': url(137), 'source_page': 137 - OFFSET})
    for no, last, first, note in SPOMENICA_LIST:
        entries.append({'soldier_id': f'{PREFIX}{200 + no:06d}', 'name': f'{last} {first}', 'last_name': last,
                        'also': [], 'first_name': first, 'nick': '', 'fathers_name': 'Luke' if no == 22 else '',
                        'birth_year': '', 'born_in': '', 'death_year': '', 'survived': True, 'units': [],
                        'additional_info': f"{SPOMENICA}: {no}. {last} {first}{(' (' + note + ')') if note else ''}",
                        'list': SPOMENICA, 'book_title': TITLE, 'source_url': url(173), 'source_page': 173 - OFFSET})
    for no, last, first, duty in COMMANDER_LIST:
        entries.append({'soldier_id': f'{PREFIX}{300 + no:06d}', 'name': f'{last} {first}', 'last_name': last,
                        'also': [], 'first_name': first, 'nick': '', 'fathers_name': '', 'birth_year': '',
                        'born_in': '', 'death_year': '', 'survived': False, 'units': [],
                        'additional_info': f'{COMMANDERS}: {no}. {duty}: {first} {last}', 'list': COMMANDERS,
                        'book_title': TITLE, 'source_url': url(174), 'source_page': 174 - OFFSET})
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name)


if __name__ == '__main__':
    main()
